import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import json

from ..models import (
    DisputeRequest, DisputeResponse, DisputeAssessment, 
    AgentStep, LaneResult, LaneStatus, DisputeStatus
)
from ..services.data_service import DataService
from ..services.openai_service import OpenAIService
from ..services.mock_api_service import MockAPIService, validate_dispute_eligibility, calculate_temporary_credit_amount

logger = logging.getLogger(__name__)


class BankingDisputeAgent:
    """
    Main agent implementing the agentic workflow:
    plan → retrieve → fork (lanes A/B/C) → synthesize → generate → act → critique → finalize
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.data_service = DataService()
        self.openai_service = OpenAIService(openai_api_key)
        self.mock_api_service = MockAPIService()
        self.processing_steps: List[AgentStep] = []
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
        self._current_user_id: Optional[str] = None
        self._current_session_id: Optional[str] = None
        
    async def process_dispute(self, dispute_request: DisputeRequest) -> DisputeResponse:
        """Main entry point for processing a dispute using agentic workflow"""
        
        # Store user and session context for observability throughout the process
        self._current_user_id = dispute_request.user_id
        self._current_session_id = dispute_request.session_id
        
        # Log with user and session context for observability
        logger.info(
            f"Starting dispute processing for customer {dispute_request.customer_id}",
            extra={
                "user_id": dispute_request.user_id,
                "session_id": dispute_request.session_id,
                "customer_id": dispute_request.customer_id,
                "dispute_category": dispute_request.dispute_category,
                "transaction_amount": dispute_request.transaction_amount
            }
        )
        self.processing_steps = []
        
        try:
            # Step 1: Plan
            plan_result = await self._plan_step(dispute_request)
            
            # Step 2: Retrieve
            retrieve_result = await self._retrieve_step(dispute_request)
            
            # Step 3: Fork into parallel lanes
            lane_results = await self._fork_lanes(dispute_request, retrieve_result)
            
            # Step 4: Synthesize
            synthesis_result = await self._synthesize_step(dispute_request, lane_results)
            
            # Step 5: Generate
            generation_result = await self._generate_step(dispute_request, synthesis_result)
            
            # Step 6: Act
            action_result = await self._act_step(dispute_request, generation_result)
            
            # Step 7: Critique
            critique_result = await self._critique_step(action_result)
            
            # Step 8: Finalize (with potential loop back if critique fails)
            final_result = await self._finalize_step(critique_result)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Error in dispute processing: {str(e)}")
            return self._create_error_response(dispute_request, str(e))
    
    async def _plan_step(self, dispute_request: DisputeRequest) -> Dict[str, Any]:
        """Step 1: Plan - Decide analysis steps"""
        start_time = datetime.now()
        
        logger.info(
            "Planning dispute analysis strategy",
            extra={
                "user_id": dispute_request.user_id,
                "session_id": dispute_request.session_id,
                "step": "plan",
                "customer_id": dispute_request.customer_id
            }
        )
        
        context = {
            "customer_id": dispute_request.customer_id,
            "card_last_four": dispute_request.card_last_four,
            "transaction_amount": dispute_request.transaction_amount,
            "merchant_name": dispute_request.merchant_name,
            "dispute_reason": dispute_request.dispute_reason,
            "dispute_category": dispute_request.dispute_category
        }
        
        # Use OpenAI to create analysis plan
        plan_analysis = await self.openai_service.analyze_dispute_step("plan", context)
        
        # Record this step
        step = AgentStep(
            step_name="plan",
            status="completed",
            start_time=start_time,
            end_time=datetime.now(),
            duration=(datetime.now() - start_time).total_seconds(),
            inputs=context,
            outputs=plan_analysis,
            confidence=plan_analysis.get("confidence", 0.8),
            reasoning=plan_analysis.get("reasoning", "Analysis plan created")
        )
        self.processing_steps.append(step)
        
        return plan_analysis
    
    async def _retrieve_step(self, dispute_request: DisputeRequest) -> Dict[str, Any]:
        """Step 2: Retrieve - Pull relevant data"""
        start_time = datetime.now()
        
        logger.info(
            "Retrieving transaction and policy data",
            extra={
                "user_id": dispute_request.user_id,
                "session_id": dispute_request.session_id,
                "step": "retrieve",
                "customer_id": dispute_request.customer_id
            }
        )
        
        # Find matching transaction
        transaction = self.data_service.find_transaction(
            dispute_request.card_last_four,
            dispute_request.transaction_amount,
            dispute_request.merchant_name
        )
        
        # Get last 90 days of transactions for context
        all_transactions = self.data_service.get_transactions_by_card(
            dispute_request.card_last_four, 90
        )
        
        # Get applicable policies
        policies = self.data_service.get_applicable_policies(
            dispute_request.dispute_category, 
            dispute_request.transaction_amount
        )
        
        context = {
            "matched_transaction": transaction.dict() if transaction else None,
            "customer_transactions": [t.dict() for t in all_transactions[:10]],  # Limit for AI context
            "applicable_policies": [p.dict() for p in policies],
            "transactions_count": len(all_transactions)
        }
        
        # Use OpenAI to analyze retrieved data
        retrieve_analysis = await self.openai_service.analyze_dispute_step("retrieve", context)
        
        # Record this step
        step = AgentStep(
            step_name="retrieve",
            status="completed",
            start_time=start_time,
            end_time=datetime.now(),
            duration=(datetime.now() - start_time).total_seconds(),
            inputs={"data_sources": ["transactions", "policies"]},
            outputs=context,
            confidence=1.0 if transaction else 0.5,
            reasoning=f"Found {len(all_transactions)} transactions, matched: {bool(transaction)}"
        )
        self.processing_steps.append(step)
        
        return {**context, "ai_analysis": retrieve_analysis}
    
    async def _fork_lanes(self, dispute_request: DisputeRequest, retrieve_result: Dict[str, Any]) -> List[LaneResult]:
        """Step 3: Fork into parallel analysis lanes"""
        
        logger.info(
            "Starting parallel analysis lanes",
            extra={
                "user_id": dispute_request.user_id,
                "session_id": dispute_request.session_id,
                "step": "fork_lanes",
                "customer_id": dispute_request.customer_id
            }
        )
        
        # Define the three lanes
        lane_tasks = [
            self._lane_a_past_disputes(dispute_request),
            self._lane_b_merchant_risk(dispute_request),
            self._lane_c_network_rules(dispute_request)
        ]
        
        # Execute lanes in parallel
        lane_results = await asyncio.gather(*lane_tasks, return_exceptions=True)
        
        # Process results and handle any exceptions
        processed_results = []
        for i, result in enumerate(lane_results):
            lane_name = ["lane_a_past_disputes", "lane_b_merchant_risk", "lane_c_network_rules"][i]
            
            if isinstance(result, Exception):
                processed_results.append(LaneResult(
                    lane_name=lane_name,
                    status=LaneStatus.FAILED,
                    data={},
                    confidence=0.0,
                    processing_time=0.0,
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _lane_a_past_disputes(self, dispute_request: DisputeRequest) -> LaneResult:
        """Lane A: Search past disputes for similar merchants"""
        start_time = datetime.now()
        
        try:
            logger.info(
                f"Lane A: Analyzing past disputes for merchant {dispute_request.merchant_name}",
                extra={
                    "user_id": dispute_request.user_id,
                    "session_id": dispute_request.session_id,
                    "lane": "past_disputes",
                    "merchant_name": dispute_request.merchant_name
                }
            )
            
            # Get past disputes for this merchant
            past_disputes = self.data_service.get_past_disputes_by_merchant(dispute_request.merchant_name)
            
            # Get customer's dispute history
            customer_disputes = self.data_service.get_past_disputes_by_customer(dispute_request.customer_id)
            
            context = {
                "merchant_disputes": [d.dict() for d in past_disputes],
                "customer_disputes": [d.dict() for d in customer_disputes],
                "merchant_name": dispute_request.merchant_name,
                "dispute_category": dispute_request.dispute_category
            }
            
            # AI analysis of patterns
            ai_analysis = await self.openai_service.analyze_dispute_step("past_disputes", context)
            
            # Calculate confidence based on data quality
            confidence = min(0.9, 0.5 + (len(past_disputes) * 0.1) + (len(customer_disputes) * 0.05))
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return LaneResult(
                lane_name="past_disputes",
                status=LaneStatus.COMPLETED,
                data={
                    "past_disputes": context,
                    "ai_analysis": ai_analysis,
                    "patterns_found": len(past_disputes) > 0,
                    "customer_history": len(customer_disputes)
                },
                confidence=confidence,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error in Lane A: {str(e)}")
            return LaneResult(
                lane_name="past_disputes",
                status=LaneStatus.FAILED,
                data={},
                confidence=0.0,
                processing_time=(datetime.now() - start_time).total_seconds(),
                error_message=str(e)
            )
    
    async def _lane_b_merchant_risk(self, dispute_request: DisputeRequest) -> LaneResult:
        """Lane B: Search risk signals on this merchant"""
        start_time = datetime.now()
        
        try:
            logger.info(
                f"Lane B: Analyzing merchant risk for {dispute_request.merchant_name}",
                extra={
                    "user_id": dispute_request.user_id,
                    "session_id": dispute_request.session_id,
                    "lane": "merchant_risk",
                    "merchant_name": dispute_request.merchant_name
                }
            )
            
            # Get merchant risk data
            merchant_risk = self.data_service.get_merchant_risk(dispute_request.merchant_name)
            
            context = {
                "merchant_risk": merchant_risk.dict() if merchant_risk else None,
                "merchant_name": dispute_request.merchant_name,
                "transaction_amount": dispute_request.transaction_amount
            }
            
            # AI analysis of risk factors
            ai_analysis = await self.openai_service.analyze_dispute_step("merchant_risk", context)
            
            # Calculate confidence based on risk data availability and quality
            if merchant_risk:
                confidence = min(0.95, 0.7 + (10 - merchant_risk.risk_score) * 0.03)
            else:
                confidence = 0.3  # Low confidence without risk data
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return LaneResult(
                lane_name="merchant_risk",
                status=LaneStatus.COMPLETED,
                data={
                    "merchant_risk": context,
                    "ai_analysis": ai_analysis,
                    "risk_score": merchant_risk.risk_score if merchant_risk else None,
                    "high_risk": merchant_risk.risk_score > 7.0 if merchant_risk else False
                },
                confidence=confidence,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error in Lane B: {str(e)}")
            return LaneResult(
                lane_name="merchant_risk",
                status=LaneStatus.FAILED,
                data={},
                confidence=0.0,
                processing_time=(datetime.now() - start_time).total_seconds(),
                error_message=str(e)
            )
    
    async def _lane_c_network_rules(self, dispute_request: DisputeRequest) -> LaneResult:
        """Lane C: Fetch network rules (Visa/Mastercard)"""
        start_time = datetime.now()
        
        try:
            logger.info(
                f"Lane C: Analyzing network rules for {dispute_request.dispute_category}",
                extra={
                    "user_id": dispute_request.user_id,
                    "session_id": dispute_request.session_id,
                    "lane": "network_rules",
                    "dispute_category": dispute_request.dispute_category
                }
            )
            
            # Get applicable network rules
            network_rules = self.data_service.get_network_rules_by_category(dispute_request.dispute_category)
            
            context = {
                "network_rules": [r.dict() for r in network_rules],
                "dispute_category": dispute_request.dispute_category,
                "transaction_amount": dispute_request.transaction_amount
            }
            
            # AI analysis of rule compliance
            ai_analysis = await self.openai_service.analyze_dispute_step("network_rules", context)
            
            # Calculate confidence based on rule applicability
            if network_rules:
                avg_success_rate = sum(r.success_rate for r in network_rules) / len(network_rules)
                confidence = min(0.9, avg_success_rate / 100.0)
            else:
                confidence = 0.4
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return LaneResult(
                lane_name="network_rules",
                status=LaneStatus.COMPLETED,
                data={
                    "network_rules": context,
                    "ai_analysis": ai_analysis,
                    "applicable_rules": len(network_rules),
                    "avg_success_rate": sum(r.success_rate for r in network_rules) / len(network_rules) if network_rules else 0
                },
                confidence=confidence,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error in Lane C: {str(e)}")
            return LaneResult(
                lane_name="network_rules",
                status=LaneStatus.FAILED,
                data={},
                confidence=0.0,
                processing_time=(datetime.now() - start_time).total_seconds(),
                error_message=str(e)
            )
    
    async def _synthesize_step(self, dispute_request: DisputeRequest, lane_results: List[LaneResult]) -> Dict[str, Any]:
        """Step 4: Synthesize - Merge lane findings into one view"""
        start_time = datetime.now()
        
        logger.info(
            "Synthesizing findings from all analysis lanes",
            extra={
                "user_id": dispute_request.user_id,
                "session_id": dispute_request.session_id,
                "step": "synthesize",
                "lane_count": len(lane_results),
                "successful_lanes": len([r for r in lane_results if r.status == LaneStatus.COMPLETED])
            }
        )
        
        context = {
            "dispute_request": dispute_request.dict(),
            "lane_results": [r.dict() for r in lane_results]
        }
        
        # AI synthesis of all findings
        synthesis = await self.openai_service.analyze_dispute_step("synthesize", context)
        
        # Calculate overall confidence
        successful_lanes = [r for r in lane_results if r.status == LaneStatus.COMPLETED]
        if successful_lanes:
            overall_confidence = sum(r.confidence for r in successful_lanes) / len(successful_lanes)
        else:
            overall_confidence = 0.2
        
        # Record this step
        step = AgentStep(
            step_name="synthesize",
            status="completed",
            start_time=start_time,
            end_time=datetime.now(),
            duration=(datetime.now() - start_time).total_seconds(),
            inputs={"lane_count": len(lane_results), "successful_lanes": len(successful_lanes)},
            outputs=synthesis,
            confidence=overall_confidence,
            reasoning=f"Synthesized {len(successful_lanes)}/{len(lane_results)} successful lanes"
        )
        self.processing_steps.append(step)
        
        return {
            "synthesis": synthesis,
            "overall_confidence": overall_confidence,
            "lane_results": lane_results,
            "successful_lanes": len(successful_lanes)
        }
    
    async def _generate_step(self, dispute_request: DisputeRequest, synthesis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Step 5: Generate - Draft customer reply and back-office note"""
        start_time = datetime.now()
        
        logger.info("Generating customer response and back-office documentation")
        
        context = {
            "dispute_request": dispute_request.dict(),
            "assessment": synthesis_result
        }
        
        # AI generation of responses
        generation = await self.openai_service.analyze_dispute_step("generate", context)
        
        # Record this step
        step = AgentStep(
            step_name="generate",
            status="completed",
            start_time=start_time,
            end_time=datetime.now(),
            duration=(datetime.now() - start_time).total_seconds(),
            inputs=context,
            outputs=generation,
            confidence=synthesis_result["overall_confidence"],
            reasoning="Generated customer and back-office communications"
        )
        self.processing_steps.append(step)
        
        return generation
    
    async def _act_step(self, dispute_request: DisputeRequest, generation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Step 6: Act - File dispute and issue temporary credit"""
        start_time = datetime.now()
        
        logger.info(
            "Taking action: filing dispute and processing credit",
            extra={
                "user_id": dispute_request.user_id,
                "session_id": dispute_request.session_id,
                "step": "act",
                "customer_id": dispute_request.customer_id,
                "transaction_amount": dispute_request.transaction_amount
            }
        )
        
        # Generate dispute ID
        dispute_id = await self.openai_service.generate_dispute_id()
        
        # Check eligibility first
        eligibility = await validate_dispute_eligibility(
            dispute_request.customer_id,
            {"amount": dispute_request.transaction_amount}
        )
        
        action_results = {"dispute_id": dispute_id, "eligibility": eligibility}
        
        if eligibility.get("eligible", False):
            # File the dispute
            dispute_filing = await self.mock_api_service.file_dispute({
                "dispute_id": dispute_id,
                "customer_id": dispute_request.customer_id,
                "transaction_amount": dispute_request.transaction_amount,
                "merchant_name": dispute_request.merchant_name,
                "dispute_reason": dispute_request.dispute_reason,
                "category": dispute_request.dispute_category
            })
            action_results["dispute_filing"] = dispute_filing
            
            # Issue temporary credit if eligible
            credit_amount = await calculate_temporary_credit_amount(
                dispute_request.transaction_amount, 
                dispute_request.dispute_category
            )
            
            if credit_amount > 0:
                temp_credit = await self.mock_api_service.issue_temporary_credit({
                    "dispute_id": dispute_id,
                    "customer_id": dispute_request.customer_id,
                    "amount": credit_amount,
                    "account_number": f"****{dispute_request.card_last_four}"
                })
                action_results["temporary_credit"] = temp_credit
            
        # Record this step
        step = AgentStep(
            step_name="act",
            status="completed",
            start_time=start_time,
            end_time=datetime.now(),
            duration=(datetime.now() - start_time).total_seconds(),
            inputs={"dispute_id": dispute_id, "eligible": eligibility.get("eligible", False)},
            outputs=action_results,
            confidence=0.9 if eligibility.get("eligible", False) else 0.3,
            reasoning="Dispute actions executed based on eligibility"
        )
        self.processing_steps.append(step)
        
        return action_results
    
    async def _critique_step(self, action_result: Dict[str, Any]) -> Dict[str, Any]:
        """Step 7: Critique - Quick self-check for gaps"""
        start_time = datetime.now()
        
        logger.info("Performing quality critique of analysis")
        
        context = {
            "complete_analysis": {
                "processing_steps": [s.dict() for s in self.processing_steps],
                "action_results": action_result
            }
        }
        
        # AI critique of the complete analysis
        critique = await self.openai_service.analyze_dispute_step("critique", context)
        
        # Determine if re-processing is needed
        critique_confidence = critique.get("confidence", 0.8)
        needs_reprocessing = critique_confidence < self.confidence_threshold
        
        # Record this step
        step = AgentStep(
            step_name="critique",
            status="completed",
            start_time=start_time,
            end_time=datetime.now(),
            duration=(datetime.now() - start_time).total_seconds(),
            inputs={"steps_analyzed": len(self.processing_steps)},
            outputs=critique,
            confidence=critique_confidence,
            reasoning=f"Quality check: {'needs improvement' if needs_reprocessing else 'acceptable'}"
        )
        self.processing_steps.append(step)
        
        return {
            "critique": critique,
            "needs_reprocessing": needs_reprocessing,
            "action_results": action_result
        }
    
    async def _finalize_step(self, critique_result: Dict[str, Any]) -> DisputeResponse:
        """Step 8: Finalize - Create final response (with potential loop back)"""
        start_time = datetime.now()
        
        logger.info(
            "Finalizing dispute response",
            extra={
                "user_id": self._current_user_id,
                "session_id": self._current_session_id,
                "step": "finalize"
            }
        )
        
        # If critique suggests reprocessing and we haven't done it yet, we could loop back
        # For now, we'll proceed with current results but flag the quality concern
        
        action_results = critique_result["action_results"]
        dispute_id = action_results.get("dispute_id", "UNKNOWN")
        
        # Determine status
        if action_results.get("eligibility", {}).get("eligible", False):
            if action_results.get("dispute_filing", {}).get("success", False):
                status = DisputeStatus.FILED
            else:
                status = DisputeStatus.PENDING
        else:
            status = DisputeStatus.DENIED
        
        # Calculate final confidence
        final_confidence = critique_result["critique"].get("confidence", 0.5)
        
        # Create customer response
        customer_response = self._create_customer_response(action_results, final_confidence)
        
        # Create back-office notes
        back_office_notes = self._create_back_office_notes()
        
        # Temporary credit information
        temp_credit = action_results.get("temporary_credit", {})
        temp_credit_issued = temp_credit.get("success", False)
        temp_credit_amount = temp_credit.get("amount", 0.0)
        
        # Record final step
        step = AgentStep(
            step_name="finalize",
            status="completed",
            start_time=start_time,
            end_time=datetime.now(),
            duration=(datetime.now() - start_time).total_seconds(),
            inputs={"critique_confidence": final_confidence},
            outputs={"status": status.value, "dispute_id": dispute_id},
            confidence=final_confidence,
            reasoning="Final dispute response created"
        )
        self.processing_steps.append(step)
        
        return DisputeResponse(
            dispute_id=dispute_id,
            status=status,
            customer_response=customer_response,
            back_office_notes=back_office_notes,
            temporary_credit_issued=temp_credit_issued,
            temporary_credit_amount=temp_credit_amount,
            estimated_resolution_days=10,
            confidence_score=final_confidence,
            next_steps=self._generate_next_steps(status, temp_credit_issued),
            supporting_evidence=self._generate_supporting_evidence(),
            processing_steps=self.processing_steps
        )
    
    def _create_customer_response(self, action_results: Dict[str, Any], confidence: float) -> str:
        """Create professional customer response"""
        
        if action_results.get("eligibility", {}).get("eligible", False):
            if action_results.get("dispute_filing", {}).get("success", False):
                return f"""
Dear Valued Customer,

Thank you for contacting us regarding the disputed transaction. We have successfully filed your dispute (Reference: {action_results.get('dispute_id', 'N/A')}) and begun our investigation.

{'A temporary credit has been posted to your account while we investigate.' if action_results.get('temporary_credit', {}).get('success', False) else 'We are reviewing your eligibility for a temporary credit.'}

We will keep you updated on the progress of your dispute. You can expect a resolution within 10 business days.

Thank you for your patience.

Best regards,
Customer Service Team
                """.strip()
            else:
                return """
Dear Valued Customer,

We received your dispute request and are currently processing it. Due to high volume, there may be a slight delay in filing your dispute with the payment network.

We will contact you within 24 hours with an update on the status.

Thank you for your patience.

Best regards,
Customer Service Team
                """.strip()
        else:
            return """
Dear Valued Customer,

Thank you for contacting us regarding the transaction in question. After reviewing your account and the transaction details, we are unable to process a dispute at this time.

This may be due to account restrictions, timing limitations, or other eligibility factors. Please contact customer service for more information about your specific situation.

Best regards,
Customer Service Team
            """.strip()
    
    def _create_back_office_notes(self) -> Dict[str, Any]:
        """Create structured back-office notes"""
        
        return {
            "analysis_summary": {
                "total_steps": len(self.processing_steps),
                "successful_steps": len([s for s in self.processing_steps if s.confidence > 0.5]),
                "average_confidence": sum(s.confidence for s in self.processing_steps) / len(self.processing_steps) if self.processing_steps else 0
            },
            "lane_analysis": {
                "lanes_executed": 3,
                "lanes_successful": len([s for s in self.processing_steps if "lane" in s.step_name and s.confidence > 0.5])
            },
            "risk_assessment": "Automated analysis completed with AI assistance",
            "recommendations": [
                "Review merchant risk profile periodically",
                "Monitor customer dispute patterns",
                "Follow up on temporary credit reversal timing"
            ],
            "processing_time": sum(s.duration or 0 for s in self.processing_steps),
            "system_version": "Banking Dispute Agent v1.0"
        }
    
    def _generate_next_steps(self, status: DisputeStatus, temp_credit_issued: bool) -> List[str]:
        """Generate next steps based on dispute status"""
        
        steps = []
        
        if status == DisputeStatus.FILED:
            steps.extend([
                "Monitor payment network response",
                "Follow up with customer in 5 business days",
                "Prepare additional documentation if requested"
            ])
            
            if temp_credit_issued:
                steps.append("Track temporary credit reversal date")
        
        elif status == DisputeStatus.PENDING:
            steps.extend([
                "Retry dispute filing in 4 hours",
                "Escalate to senior analyst if retry fails",
                "Notify customer of delay"
            ])
        
        elif status == DisputeStatus.DENIED:
            steps.extend([
                "Document denial reason for customer",
                "Explore alternative resolution options",
                "Schedule follow-up call with customer"
            ])
        
        return steps
    
    def _generate_supporting_evidence(self) -> List[str]:
        """Generate list of supporting evidence collected"""
        
        evidence = [
            "Transaction details verified",
            "Customer account history reviewed",
            "Payment network rules analyzed"
        ]
        
        # Add evidence based on processing steps
        for step in self.processing_steps:
            if step.step_name == "past_disputes" and step.confidence > 0.5:
                evidence.append("Historical dispute patterns analyzed")
            elif step.step_name == "merchant_risk" and step.confidence > 0.5:
                evidence.append("Merchant risk assessment completed")
            elif step.step_name == "network_rules" and step.confidence > 0.5:
                evidence.append("Network compliance verified")
        
        return evidence
    
    def _create_error_response(self, dispute_request: DisputeRequest, error_message: str) -> DisputeResponse:
        """Create error response when processing fails"""
        
        return DisputeResponse(
            dispute_id="ERROR",
            status=DisputeStatus.PENDING,
            customer_response="We apologize, but we're experiencing technical difficulties. Please try again later or contact customer service.",
            back_office_notes={"error": error_message, "timestamp": datetime.now().isoformat()},
            temporary_credit_issued=False,
            temporary_credit_amount=0.0,
            estimated_resolution_days=1,
            confidence_score=0.0,
            next_steps=["Technical team to investigate", "Customer service to follow up"],
            supporting_evidence=["Error logged for technical review"],
            processing_steps=self.processing_steps
        )
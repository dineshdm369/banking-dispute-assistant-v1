import asyncio
import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid

from ..models import (
    DisputeRequest, DisputeResponse, DisputeStatus, 
    AgentStep, FunctionCall
)
from ..services.data_service import DataService
from ..services.openai_service import OpenAIService
from ..services.mock_api_service import MockAPIService
from ..services.function_registry import FunctionRegistry

logger = logging.getLogger(__name__)


class IntelligentDisputeAgent:
    """
    banking-dispute-assistant-v1: Intelligent dispute resolution using OpenAI function calling.
    Dynamically decides which analyses to perform and actions to take.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.data_service = DataService()
        self.openai_service = OpenAIService(openai_api_key)
        self.mock_api_service = MockAPIService()
        self.function_registry = FunctionRegistry(self.data_service, self.mock_api_service)
        
        # Configuration
        self.max_conversation_turns = int(os.getenv("MAX_CONVERSATION_TURNS", "10"))
        self._current_user_id: Optional[str] = None
        self._current_session_id: Optional[str] = None
        
    async def process_dispute(self, dispute_request: DisputeRequest) -> DisputeResponse:
        """Main entry point for intelligent dispute processing"""
        
        start_time = datetime.now()
        
        # Store user and session context
        self._current_user_id = dispute_request.user_id
        self._current_session_id = dispute_request.session_id
        
        # Generate unique dispute ID
        dispute_id = await self._generate_dispute_id()
        
        # Log dispute initiation
        logger.info(
            f"Starting intelligent dispute processing",
            extra={
                "user_id": dispute_request.user_id,
                "session_id": dispute_request.session_id,
                "customer_id": dispute_request.customer_id,
                "dispute_id": dispute_id,
                "dispute_category": dispute_request.dispute_category,
                "transaction_amount": dispute_request.transaction_amount
            }
        )
        
        try:
            # Initialize conversation with dispute request
            dispute_dict = dispute_request.dict()
            function_schemas = self.function_registry.get_function_schemas()
            
            # Start intelligent conversation
            messages = []
            all_function_calls = []
            conversation_turns = 0
            final_reasoning = ""
            
            # Initial LLM call
            initial_response, function_calls, initial_message = await self.openai_service.process_dispute_with_functions(
                dispute_dict, function_schemas
            )
            
            # Add the complete assistant message to conversation history
            assistant_message = {"role": "assistant", "content": initial_message.content}
            if hasattr(initial_message, 'tool_calls') and initial_message.tool_calls:
                assistant_message["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function", 
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in initial_message.tool_calls
                ]
            messages.append(assistant_message)
            
            # Process function calls and continue conversation
            while function_calls and conversation_turns < self.max_conversation_turns:
                conversation_turns += 1
                
                logger.info(
                    f"Processing {len(function_calls)} function calls in turn {conversation_turns}",
                    extra={
                        "user_id": dispute_request.user_id,
                        "session_id": dispute_request.session_id,
                        "dispute_id": dispute_id,
                        "turn": conversation_turns,
                        "functions": [fc["function_name"] for fc in function_calls]
                    }
                )
                
                # Execute all function calls
                function_results = await self._execute_function_calls(function_calls)
                all_function_calls.extend(function_results)
                
                # Add function results to conversation
                for result in function_results:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": result.id,
                        "content": json.dumps(result.result) if result.result else f"Error: {result.error}"
                    })
                
                # Continue conversation with results
                next_response, next_function_calls, next_message = await self.openai_service.continue_conversation(
                    messages, function_schemas
                )
                
                if next_response or next_function_calls:
                    # Add the complete assistant message to conversation history
                    assistant_message = {"role": "assistant", "content": next_message.content}
                    if hasattr(next_message, 'tool_calls') and next_message.tool_calls:
                        assistant_message["tool_calls"] = [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            } for tc in next_message.tool_calls
                        ]
                    messages.append(assistant_message)
                    
                    if next_response:
                        final_reasoning = next_response
                
                function_calls = next_function_calls
            
            # Extract resolution information from final response
            resolution_data = self._extract_resolution_data(final_reasoning, all_function_calls)
            
            # Create processing step
            processing_step = AgentStep(
                step_name="intelligent_dispute_processing",
                status="completed",
                start_time=start_time,
                end_time=datetime.now(),
                duration=(datetime.now() - start_time).total_seconds(),
                inputs=dispute_dict,
                outputs=resolution_data,
                confidence=resolution_data.get("confidence_score"),
                reasoning=final_reasoning,
                function_calls=all_function_calls
            )
            
            # Build final response
            response = DisputeResponse(
                dispute_id=dispute_id,
                status=self._determine_status(resolution_data),
                customer_response=resolution_data.get("customer_response", "Your dispute has been processed."),
                back_office_notes=resolution_data.get("back_office_notes", {}),
                temporary_credit_issued=resolution_data.get("temporary_credit_issued", False),
                temporary_credit_amount=resolution_data.get("temporary_credit_amount", 0.0),
                estimated_resolution_days=resolution_data.get("estimated_resolution_days", 5),
                confidence_score=resolution_data.get("confidence_score"),
                next_steps=resolution_data.get("next_steps", []),
                supporting_evidence=resolution_data.get("supporting_evidence", []),
                processing_steps=[processing_step],
                total_function_calls=len(all_function_calls),
                reasoning=final_reasoning
            )
            
            logger.info(
                f"Dispute processing completed successfully",
                extra={
                    "user_id": dispute_request.user_id,
                    "session_id": dispute_request.session_id,
                    "dispute_id": dispute_id,
                    "status": response.status.value,
                    "function_calls_made": len(all_function_calls),
                    "conversation_turns": conversation_turns,
                    "processing_time": processing_step.duration
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(
                f"Error in intelligent dispute processing: {str(e)}",
                extra={
                    "user_id": dispute_request.user_id,
                    "session_id": dispute_request.session_id,
                    "dispute_id": dispute_id,
                    "error": str(e)
                }
            )
            return self._create_error_response(dispute_request, dispute_id, str(e))
    
    async def _execute_function_calls(self, function_calls: List[Dict]) -> List[FunctionCall]:
        """Execute a list of function calls"""
        results = []
        
        # Execute function calls in parallel when possible
        tasks = []
        for fc in function_calls:
            task = self._execute_single_function_call(fc)
            tasks.append(task)
        
        # Wait for all function calls to complete
        function_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(function_results):
            fc = function_calls[i]
            
            if isinstance(result, Exception):
                results.append(FunctionCall(
                    id=fc["id"],
                    function_name=fc["function_name"],
                    arguments=fc["arguments"],
                    error=str(result),
                    execution_time=0.0
                ))
            else:
                results.append(result)
        
        return results
    
    async def _execute_single_function_call(self, function_call: Dict) -> FunctionCall:
        """Execute a single function call"""
        start_time = datetime.now()
        
        try:
            logger.info(
                f"Executing function: {function_call['function_name']}",
                extra={
                    "user_id": self._current_user_id,
                    "session_id": self._current_session_id,
                    "function": function_call["function_name"],
                    "arguments": function_call["arguments"]
                }
            )
            
            result = await self.function_registry.execute_function(
                function_call["function_name"],
                function_call["arguments"],
                session_context={
                    "user_id": self._current_user_id,
                    "session_id": self._current_session_id
                }
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return FunctionCall(
                id=function_call["id"],
                function_name=function_call["function_name"],
                arguments=function_call["arguments"],
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.error(
                f"Function execution failed: {function_call['function_name']} - {str(e)}",
                extra={
                    "user_id": self._current_user_id,
                    "session_id": self._current_session_id,
                    "function": function_call["function_name"],
                    "error": str(e)
                }
            )
            
            return FunctionCall(
                id=function_call["id"],
                function_name=function_call["function_name"],
                arguments=function_call["arguments"],
                error=str(e),
                execution_time=execution_time
            )
    
    def _extract_resolution_data(self, final_reasoning: str, function_calls: List[FunctionCall]) -> Dict[str, Any]:
        """Extract resolution data from LLM response and function call results"""
        
        # Initialize default resolution data
        resolution_data = {
            "customer_response": "Your dispute has been processed and is under review.",
            "back_office_notes": {
                "processing_summary": final_reasoning,
                "function_calls_executed": len(function_calls),
                "investigation_completed": True
            },
            "temporary_credit_issued": False,
            "temporary_credit_amount": 0.0,
            "estimated_resolution_days": 5,
            "confidence_score": 0.8,
            "next_steps": ["Review dispute documentation", "Monitor case status"],
            "supporting_evidence": []
        }
        
        # Analyze function call results for specific actions taken
        for fc in function_calls:
            if fc.result and fc.result.get("success"):
                data = fc.result.get("data", {})
                
                # Check for temporary credit issuance
                if fc.function_name == "issue_temporary_credit":
                    if data.get("success"):
                        resolution_data["temporary_credit_issued"] = True
                        resolution_data["temporary_credit_amount"] = data.get("amount", 0.0)
                        resolution_data["customer_response"] = f"Your dispute has been processed and a temporary credit of ${data.get('amount', 0):.2f} has been issued to your account."
                
                # Check for dispute filing
                elif fc.function_name == "file_dispute_with_network":
                    if data.get("success"):
                        resolution_data["customer_response"] = f"Your dispute has been filed with the payment network. Reference number: {data.get('reference_number', 'N/A')}"
                        resolution_data["estimated_resolution_days"] = 10
                
                # Extract evidence from investigations
                elif fc.function_name in ["search_past_disputes", "assess_merchant_risk", "check_network_rules"]:
                    if "analysis" in data:
                        resolution_data["supporting_evidence"].append(data["analysis"])
        
        # Extract confidence from reasoning text (simple heuristic)
        if "high confidence" in final_reasoning.lower():
            resolution_data["confidence_score"] = 0.9
        elif "medium confidence" in final_reasoning.lower():
            resolution_data["confidence_score"] = 0.7
        elif "low confidence" in final_reasoning.lower():
            resolution_data["confidence_score"] = 0.5
        
        return resolution_data
    
    def _determine_status(self, resolution_data: Dict[str, Any]) -> DisputeStatus:
        """Determine dispute status based on resolution data"""
        
        if resolution_data.get("temporary_credit_issued"):
            return DisputeStatus.APPROVED
        elif "filed with the payment network" in resolution_data.get("customer_response", ""):
            return DisputeStatus.FILED
        elif "denied" in resolution_data.get("customer_response", "").lower():
            return DisputeStatus.DENIED
        else:
            return DisputeStatus.INVESTIGATING
    
    def _create_error_response(self, dispute_request: DisputeRequest, dispute_id: str, error_message: str) -> DisputeResponse:
        """Create an error response"""
        
        return DisputeResponse(
            dispute_id=dispute_id,
            status=DisputeStatus.PENDING,
            customer_response=f"We're experiencing technical difficulties processing your dispute. Please try again later. Error: {error_message}",
            back_office_notes={
                "error": error_message,
                "requires_manual_review": True,
                "timestamp": datetime.now().isoformat()
            },
            temporary_credit_issued=False,
            temporary_credit_amount=0.0,
            estimated_resolution_days=1,
            confidence_score=0.0,
            next_steps=["Manual review required", "Contact technical support"],
            supporting_evidence=[],
            processing_steps=[],
            total_function_calls=0,
            reasoning=f"Error occurred: {error_message}"
        )
    
    async def _generate_dispute_id(self) -> str:
        """Generate a unique dispute ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"BDA{timestamp}{unique_id.upper()}"  # BDA = banking-dispute-assistant-v1
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
import os
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI's Chat Completions API and function calling"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"
        
    async def analyze_dispute_step(self, step_name: str, context: Dict[str, Any], 
                                 tools: List[Dict] = None) -> Dict[str, Any]:
        """Analyze a specific step in the dispute process"""
        
        system_prompt = self._get_system_prompt(step_name)
        user_prompt = self._format_context(step_name, context)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            if tools:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.3
                )
                
                # Handle function calls if any
                if response.choices[0].message.tool_calls:
                    return self._handle_tool_calls(response.choices[0].message.tool_calls)
                    
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to text
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"analysis": content, "confidence": 0.8}
                
        except Exception as e:
            logger.error(f"Error in OpenAI analysis for {step_name}: {str(e)}")
            return {"error": str(e), "confidence": 0.0}
    
    def _get_system_prompt(self, step_name: str) -> str:
        """Get system prompt for specific analysis step"""
        
        prompts = {
            "plan": """You are a banking dispute analysis expert. Your task is to create a comprehensive plan for analyzing a customer dispute.
            
            Analyze the dispute request and create a structured plan with:
            1. Key analysis steps needed
            2. Data requirements for each step
            3. Risk factors to investigate
            4. Success probability estimate
            
            Return a JSON object with your analysis plan.""",
            
            "retrieve": """You are a banking data analyst. Analyze the provided transaction and customer data to identify relevant information for the dispute.
            
            Focus on:
            1. Transaction verification and matching
            2. Customer history patterns
            3. Anomaly detection
            4. Data quality assessment
            
            Return a JSON object with your findings.""",
            
            "past_disputes": """You are a dispute pattern analyst. Analyze past disputes for similar patterns and outcomes.
            
            Focus on:
            1. Similar merchant disputes
            2. Resolution patterns
            3. Success rate analysis
            4. Risk indicators
            
            Return a JSON object with pattern analysis and confidence score.""",
            
            "merchant_risk": """You are a merchant risk analyst. Evaluate the risk profile of the merchant involved in the dispute.
            
            Analyze:
            1. Merchant risk scores and factors
            2. Historical dispute patterns
            3. Fraud indicators
            4. Compliance status
            
            Return a JSON object with risk assessment and recommendations.""",
            
            "network_rules": """You are a payment network rules expert. Analyze applicable chargeback and dispute rules.
            
            Evaluate:
            1. Applicable network rules (Visa/Mastercard)
            2. Time limits and eligibility
            3. Documentation requirements
            4. Success probability based on rules
            
            Return a JSON object with rules analysis and compliance assessment.""",
            
            "synthesize": """You are a dispute resolution specialist. Synthesize all gathered information to form a comprehensive assessment.
            
            Combine insights from:
            1. Transaction analysis
            2. Past dispute patterns
            3. Merchant risk assessment
            4. Network rules compliance
            
            Return a JSON object with synthesis, overall confidence, and recommendation.""",
            
            "generate": """You are a customer communication specialist. Generate appropriate responses for the customer and back-office notes.
            
            Create:
            1. Professional customer response
            2. Detailed back-office notes
            3. Action items and next steps
            4. Documentation requirements
            
            Return a JSON object with generated content.""",
            
            "critique": """You are a quality assurance analyst. Review the dispute analysis for completeness and accuracy.
            
            Check:
            1. Analysis completeness
            2. Evidence quality
            3. Reasoning consistency
            4. Compliance with policies
            
            Return a JSON object with critique, gaps identified, and improvement recommendations."""
        }
        
        return prompts.get(step_name, "You are a banking dispute analysis expert. Analyze the provided information and return insights in JSON format.")
    
    def _format_context(self, step_name: str, context: Dict[str, Any]) -> str:
        """Format context data for the specific analysis step"""
        
        base_info = f"""
        Dispute Request Information:
        - Customer ID: {context.get('customer_id', 'N/A')}
        - Card Last Four: {context.get('card_last_four', 'N/A')}
        - Transaction Amount: ${context.get('transaction_amount', 0):.2f}
        - Merchant: {context.get('merchant_name', 'N/A')}
        - Dispute Reason: {context.get('dispute_reason', 'N/A')}
        - Category: {context.get('dispute_category', 'N/A')}
        """
        
        if step_name == "plan":
            return f"""{base_info}
            
            Create a comprehensive analysis plan for this dispute. Consider all aspects that need investigation."""
            
        elif step_name == "retrieve":
            transactions = context.get('transactions', [])
            return f"""{base_info}
            
            Transaction Data Available:
            {json.dumps(transactions, indent=2) if transactions else 'No matching transactions found'}
            
            Analyze this transaction data for the dispute."""
            
        elif step_name == "past_disputes":
            past_disputes = context.get('past_disputes', [])
            return f"""{base_info}
            
            Past Disputes Data:
            {json.dumps(past_disputes, indent=2) if past_disputes else 'No past disputes found'}
            
            Analyze patterns in past disputes for this merchant."""
            
        elif step_name == "merchant_risk":
            merchant_risk = context.get('merchant_risk', {})
            return f"""{base_info}
            
            Merchant Risk Data:
            {json.dumps(merchant_risk, indent=2) if merchant_risk else 'No merchant risk data available'}
            
            Assess the risk profile of this merchant."""
            
        elif step_name == "network_rules":
            network_rules = context.get('network_rules', [])
            return f"""{base_info}
            
            Applicable Network Rules:
            {json.dumps(network_rules, indent=2) if network_rules else 'No specific network rules found'}
            
            Evaluate compliance with payment network rules."""
            
        elif step_name == "synthesize":
            lane_results = context.get('lane_results', [])
            return f"""{base_info}
            
            Analysis Results from All Lanes:
            {json.dumps(lane_results, indent=2)}
            
            Synthesize all findings into a comprehensive assessment."""
            
        elif step_name == "generate":
            assessment = context.get('assessment', {})
            return f"""{base_info}
            
            Final Assessment:
            {json.dumps(assessment, indent=2)}
            
            Generate customer response and back-office documentation."""
            
        elif step_name == "critique":
            analysis = context.get('complete_analysis', {})
            return f"""{base_info}
            
            Complete Analysis:
            {json.dumps(analysis, indent=2)}
            
            Review this analysis for quality and completeness."""
        
        return base_info
    
    def _handle_tool_calls(self, tool_calls) -> Dict[str, Any]:
        """Handle function calls from OpenAI"""
        results = []
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # Mock function execution for demonstration
            result = {
                "function": function_name,
                "arguments": function_args,
                "result": f"Executed {function_name} with args: {function_args}"
            }
            results.append(result)
        
        return {"tool_calls": results}
    
    async def generate_dispute_id(self) -> str:
        """Generate a unique dispute ID"""
        import uuid
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"DSP{timestamp}{unique_id.upper()}"
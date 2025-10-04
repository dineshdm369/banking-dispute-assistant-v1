import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from openai import OpenAI
import os
from datetime import datetime
from ..utils.helpers import safe_json_dumps

# Set up logging
logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI's Chat Completions API with function calling support"""
    
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None  # Allow testing without API key
        self.model = "gpt-4o-mini"
        
    async def process_dispute_with_functions(self, dispute_request: Dict[str, Any], 
                                           function_schemas: List[Dict]) -> Tuple[str, List[Dict], Dict]:
        """Process dispute using function calling approach"""
        
        if not self.client:
            return "OpenAI client not initialized - API key required", [], {}
        
        system_prompt = self._get_intelligent_system_prompt()
        user_prompt = self._format_dispute_request(dispute_request)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=function_schemas,
                tool_choice="auto",
                temperature=0.3
            )
            
            message = response.choices[0].message
            function_calls = []
            
            # Extract function calls if any
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    function_calls.append({
                        "id": tool_call.id,
                        "function_name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments)
                    })
            
            # Return the full message object for proper conversation history
            return message.content or "I need to gather information first.", function_calls, message
                
        except Exception as e:
            logger.error(f"Error in OpenAI dispute processing: {str(e)}")
            return f"Error processing dispute: {str(e)}", [], {}
    
    async def continue_conversation(self, messages: List[Dict], function_schemas: List[Dict]) -> Tuple[str, List[Dict], Dict]:
        """Continue conversation with function results"""
        
        if not self.client:
            return "OpenAI client not initialized - API key required", [], {}
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=function_schemas,
                tool_choice="auto",
                temperature=0.3
            )
            
            message = response.choices[0].message
            function_calls = []
            
            # Extract function calls if any
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    function_calls.append({
                        "id": tool_call.id,
                        "function_name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments)
                    })
            
            return message.content or "", function_calls, message
                
        except Exception as e:
            logger.error(f"Error in OpenAI conversation: {str(e)}")
            return f"Error continuing conversation: {str(e)}", [], {}
    
    def _get_intelligent_system_prompt(self) -> str:
        """Get the system prompt for intelligent dispute processing"""
        return """You are an expert dispute resolution specialist with access to comprehensive tools and data.

Your role is to analyze customer disputes intelligently and efficiently by:

1. **Understanding the Request**: Carefully review the dispute details including customer ID, transaction amount, merchant, and dispute reason.

2. **Strategic Investigation**: Use available functions to gather relevant information. You can:
   - Search past disputes for patterns
   - Assess merchant risk profiles  
   - Check payment network rules
   - Find transaction details
   - Review customer dispute history
   - Verify account eligibility
   - Check internal policies

3. **Dynamic Decision Making**: Based on the information you gather, decide whether to:
   - Approve the dispute and issue temporary credit
   - Deny the dispute with explanation
   - File with payment networks for further investigation
   - Request additional documentation

4. **Taking Action**: When ready, you can:
   - Calculate and issue temporary credits
   - File disputes with payment networks
   - Send customer notifications
   - Update case management systems

**Important Guidelines:**
- Start by gathering basic transaction and account information
- Use your judgment on which investigations are necessary based on dispute type and amount
- Consider merchant risk, customer history, and network rules in your decisions
- Provide clear reasoning for your recommendations
- Take appropriate actions to resolve the dispute

**Customer Service Focus:**
- Be helpful and thorough in your analysis
- Provide clear explanations to customers
- Ensure fast resolution when possible
- Follow all compliance and policy requirements

Begin by analyzing the dispute request and determining what information you need to make an informed decision."""
    
    def _format_dispute_request(self, dispute_request: Dict[str, Any]) -> str:
        """Format dispute request for LLM processing"""
        
        return f"""
NEW DISPUTE REQUEST

**Customer Information:**
- Customer ID: {dispute_request.get('customer_id', 'N/A')}
- Card Last Four Digits: {dispute_request.get('card_last_four', 'N/A')}

**Transaction Details:**
- Amount: ${dispute_request.get('transaction_amount', 0):.2f}
- Merchant: {dispute_request.get('merchant_name', 'N/A')}
- Dispute Category: {dispute_request.get('dispute_category', 'N/A')}

**Dispute Information:**
- Reason: {dispute_request.get('dispute_reason', 'N/A')}
- Additional Details: {dispute_request.get('additional_details', 'None provided')}

**Context:**
- User ID: {dispute_request.get('user_id', 'N/A')}
- Session ID: {dispute_request.get('session_id', 'N/A')}

Please analyze this dispute request and determine what information you need to gather to make an informed decision. Use the available functions to investigate as needed, then provide a resolution.
        """
    
    # Legacy method for backward compatibility
    async def analyze_dispute_step(self, step_name: str, context: Dict[str, Any], 
                                 tools: List[Dict] = None) -> Dict[str, Any]:
        """Legacy method - kept for compatibility"""
        logger.warning("Using legacy analyze_dispute_step method. Consider upgrading to function calling.")
        
        # Simple fallback implementation
        return {
            "step": step_name,
            "context": context,
            "confidence": 0.5,
            "analysis": f"Legacy analysis for {step_name}",
            "recommendation": "Upgrade to function calling for better analysis"
        }
    
    async def generate_dispute_id(self) -> str:
        """Generate a unique dispute ID"""
        import uuid
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"DSP{timestamp}{unique_id.upper()}"
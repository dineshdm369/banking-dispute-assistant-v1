import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from .data_service import DataService
from .mock_api_service import MockAPIService

logger = logging.getLogger(__name__)


class FunctionRegistry:
    """Registry of functions available to the banking-dispute-assistant-v1"""
    
    def __init__(self, data_service: DataService, mock_api_service: MockAPIService):
        self.data_service = data_service
        self.mock_api_service = mock_api_service
        self._functions = {}
        self._register_functions()
    
    def _register_functions(self):
        """Register all available functions"""
        
        # Analysis Functions
        self._functions["search_past_disputes"] = {
            "function": self._search_past_disputes,
            "schema": {
                "type": "function",
                "function": {
                    "name": "search_past_disputes",
                    "description": "Search for past disputes involving a specific merchant to identify patterns and success rates",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "merchant_name": {
                                "type": "string",
                                "description": "Name of the merchant to search disputes for"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["Fraud", "Billing Error", "Authorization Issue", "all"],
                                "description": "Dispute category to filter by, or 'all' for all categories"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of past disputes to return",
                                "default": 10
                            }
                        },
                        "required": ["merchant_name"]
                    }
                }
            }
        }
        
        self._functions["assess_merchant_risk"] = {
            "function": self._assess_merchant_risk,
            "schema": {
                "type": "function",
                "function": {
                    "name": "assess_merchant_risk",
                    "description": "Get comprehensive risk assessment data for a merchant including fraud rates and dispute patterns",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "merchant_name": {
                                "type": "string",
                                "description": "Name of the merchant to assess"
                            }
                        },
                        "required": ["merchant_name"]
                    }
                }
            }
        }
        
        self._functions["check_network_rules"] = {
            "function": self._check_network_rules,
            "schema": {
                "type": "function",
                "function": {
                    "name": "check_network_rules",
                    "description": "Check applicable payment network rules (Visa/Mastercard) for dispute eligibility and requirements",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dispute_category": {
                                "type": "string",
                                "enum": ["Fraud", "Billing Error", "Authorization Issue"],
                                "description": "Category of the dispute"
                            },
                            "transaction_amount": {
                                "type": "number",
                                "description": "Amount of the disputed transaction"
                            }
                        },
                        "required": ["dispute_category", "transaction_amount"]
                    }
                }
            }
        }
        
        self._functions["find_transaction_details"] = {
            "function": self._find_transaction_details,
            "schema": {
                "type": "function",
                "function": {
                    "name": "find_transaction_details",
                    "description": "Locate and retrieve detailed information about a specific transaction",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "card_last_four": {
                                "type": "string",
                                "description": "Last four digits of the card"
                            },
                            "amount": {
                                "type": "number",
                                "description": "Transaction amount"
                            },
                            "merchant_name": {
                                "type": "string",
                                "description": "Name of the merchant"
                            }
                        },
                        "required": ["card_last_four", "amount", "merchant_name"]
                    }
                }
            }
        }
        
        self._functions["get_customer_dispute_history"] = {
            "function": self._get_customer_dispute_history,
            "schema": {
                "type": "function",
                "function": {
                    "name": "get_customer_dispute_history",
                    "description": "Get the customer's past dispute history to identify patterns and assess credibility",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "string",
                                "description": "Customer ID to look up"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days back to search",
                                "default": 365
                            }
                        },
                        "required": ["customer_id"]
                    }
                }
            }
        }
        
        self._functions["check_dispute_policies"] = {
            "function": self._check_dispute_policies,
            "schema": {
                "type": "function",
                "function": {
                    "name": "check_dispute_policies",
                    "description": "Check internal bank policies for dispute handling, time limits, and eligibility criteria",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": ["Fraud", "Billing Error", "Authorization Issue"],
                                "description": "Dispute category"
                            },
                            "amount": {
                                "type": "number",
                                "description": "Dispute amount"
                            }
                        },
                        "required": ["category", "amount"]
                    }
                }
            }
        }
        
        # Action Functions
        self._functions["check_account_eligibility"] = {
            "function": self._check_account_eligibility,
            "schema": {
                "type": "function",
                "function": {
                    "name": "check_account_eligibility",
                    "description": "Check if customer account is eligible for dispute filing and temporary credits",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "string",
                                "description": "Customer ID to check"
                            }
                        },
                        "required": ["customer_id"]
                    }
                }
            }
        }
        
        self._functions["calculate_temporary_credit"] = {
            "function": self._calculate_temporary_credit,
            "schema": {
                "type": "function",
                "function": {
                    "name": "calculate_temporary_credit",
                    "description": "Calculate the appropriate temporary credit amount based on dispute details and policies",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "string",
                                "description": "Customer ID"
                            },
                            "dispute_amount": {
                                "type": "number",
                                "description": "Amount being disputed"
                            },
                            "dispute_category": {
                                "type": "string",
                                "enum": ["Fraud", "Billing Error", "Authorization Issue"],
                                "description": "Category of dispute"
                            }
                        },
                        "required": ["customer_id", "dispute_amount", "dispute_category"]
                    }
                }
            }
        }
        
        self._functions["issue_temporary_credit"] = {
            "function": self._issue_temporary_credit,
            "schema": {
                "type": "function",
                "function": {
                    "name": "issue_temporary_credit",
                    "description": "Issue a temporary credit to the customer's account",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "string",
                                "description": "Customer ID"
                            },
                            "amount": {
                                "type": "number",
                                "description": "Credit amount to issue"
                            },
                            "dispute_id": {
                                "type": "string",
                                "description": "Associated dispute ID"
                            }
                        },
                        "required": ["customer_id", "amount", "dispute_id"]
                    }
                }
            }
        }
        
        self._functions["file_dispute_with_network"] = {
            "function": self._file_dispute_with_network,
            "schema": {
                "type": "function",
                "function": {
                    "name": "file_dispute_with_network",
                    "description": "File the dispute with the payment network (Visa/Mastercard)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dispute_data": {
                                "type": "object",
                                "description": "Complete dispute information",
                                "properties": {
                                    "customer_id": {"type": "string"},
                                    "transaction_id": {"type": "string"},
                                    "dispute_category": {"type": "string"},
                                    "dispute_reason": {"type": "string"},
                                    "amount": {"type": "number"},
                                    "merchant_name": {"type": "string"}
                                },
                                "required": ["customer_id", "dispute_category", "dispute_reason", "amount", "merchant_name"]
                            }
                        },
                        "required": ["dispute_data"]
                    }
                }
            }
        }
        
        self._functions["send_customer_notification"] = {
            "function": self._send_customer_notification,
            "schema": {
                "type": "function",
                "function": {
                    "name": "send_customer_notification",
                    "description": "Send notification to customer about dispute status or next steps",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_id": {
                                "type": "string",
                                "description": "Customer ID"
                            },
                            "message": {
                                "type": "string",
                                "description": "Message to send to customer"
                            },
                            "channel": {
                                "type": "string",
                                "enum": ["email", "sms", "both"],
                                "description": "Communication channel",
                                "default": "email"
                            }
                        },
                        "required": ["customer_id", "message"]
                    }
                }
            }
        }
        
        self._functions["update_case_management"] = {
            "function": self._update_case_management,
            "schema": {
                "type": "function",
                "function": {
                    "name": "update_case_management",
                    "description": "Update the case management system with dispute status and notes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dispute_id": {
                                "type": "string",
                                "description": "Dispute ID"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["Pending", "Investigating", "Approved", "Denied", "Filed"],
                                "description": "Current dispute status"
                            },
                            "notes": {
                                "type": "string",
                                "description": "Case notes and findings"
                            }
                        },
                        "required": ["dispute_id", "status", "notes"]
                    }
                }
            }
        }
    
    def get_function_schemas(self) -> List[Dict]:
        """Return all function schemas for OpenAI"""
        return [func_data["schema"] for func_data in self._functions.values()]
    
    async def execute_function(self, function_name: str, arguments: Dict[str, Any], session_context: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Execute a function call with optional session context"""
        if function_name not in self._functions:
            raise ValueError(f"Unknown function: {function_name}")
        
        function_handler = self._functions[function_name]["function"]
        
        try:
            # Create log entry with session context
            extra_fields = {"function": function_name}
            if session_context:
                extra_fields.update(session_context)
            
            logger.info(f"Executing function {function_name} with arguments: {arguments}", extra=extra_fields)
            result = await function_handler(**arguments)
            logger.info(f"Function {function_name} completed successfully", extra=extra_fields)
            return {"success": True, "data": result}
        except Exception as e:
            extra_fields = {"function": function_name}
            if session_context:
                extra_fields.update(session_context)
            logger.error(f"Function {function_name} failed: {str(e)}", extra=extra_fields)
            return {"success": False, "error": str(e)}
    
    # Function Implementations
    async def _search_past_disputes(self, merchant_name: str, category: str = "all", limit: int = 10) -> Dict[str, Any]:
        """Search past disputes for merchant patterns"""
        past_disputes = self.data_service.get_past_disputes_by_merchant(merchant_name)
        
        if category != "all":
            past_disputes = [d for d in past_disputes if d.dispute_category.lower() == category.lower()]
        
        # Limit results
        past_disputes = past_disputes[:limit]
        
        # Calculate statistics
        total_disputes = len(past_disputes)
        if total_disputes > 0:
            successful = len([d for d in past_disputes if d.resolution.lower() in ["approved", "resolved"]])
            success_rate = successful / total_disputes
        else:
            success_rate = 0.0
        
        return {
            "merchant_name": merchant_name,
            "total_disputes_found": total_disputes,
            "success_rate": success_rate,
            "disputes": [d.dict() for d in past_disputes],
            "analysis": f"Found {total_disputes} past disputes for {merchant_name} with {success_rate:.1%} success rate"
        }
    
    async def _assess_merchant_risk(self, merchant_name: str) -> Dict[str, Any]:
        """Get merchant risk assessment"""
        merchant_risk = self.data_service.get_merchant_risk_data(merchant_name)
        
        if merchant_risk:
            return {
                "merchant_found": True,
                "risk_data": merchant_risk.dict(),
                "risk_level": "High" if merchant_risk.risk_score > 7 else "Medium" if merchant_risk.risk_score > 4 else "Low",
                "recommendation": "Proceed with caution" if merchant_risk.risk_score > 7 else "Standard processing"
            }
        else:
            return {
                "merchant_found": False,
                "risk_level": "Unknown",
                "recommendation": "No risk data available - proceed with standard analysis"
            }
    
    async def _check_network_rules(self, dispute_category: str, transaction_amount: float) -> Dict[str, Any]:
        """Check payment network rules"""
        network_rules = self.data_service.get_network_rules_by_category(dispute_category)
        
        applicable_rules = []
        for rule in network_rules:
            if rule.description and str(transaction_amount) in rule.description:
                applicable_rules.append(rule.dict())
        
        # If no specific rules, get general category rules
        if not applicable_rules:
            applicable_rules = [rule.dict() for rule in network_rules[:3]]  # Top 3 general rules
        
        return {
            "dispute_category": dispute_category,
            "transaction_amount": transaction_amount,
            "applicable_rules": applicable_rules,
            "rules_count": len(applicable_rules),
            "analysis": f"Found {len(applicable_rules)} applicable network rules for {dispute_category} disputes"
        }
    
    async def _find_transaction_details(self, card_last_four: str, amount: float, merchant_name: str) -> Dict[str, Any]:
        """Find specific transaction details"""
        transaction = self.data_service.find_transaction(card_last_four, amount, merchant_name)
        
        if transaction:
            return {
                "transaction_found": True,
                "transaction": transaction.dict(),
                "analysis": f"Found matching transaction: {transaction.transaction_id}"
            }
        else:
            return {
                "transaction_found": False,
                "analysis": f"No matching transaction found for card {card_last_four}, amount ${amount}, merchant {merchant_name}"
            }
    
    async def _get_customer_dispute_history(self, customer_id: str, days: int = 365) -> Dict[str, Any]:
        """Get customer's dispute history"""
        customer_disputes = self.data_service.get_past_disputes_by_customer(customer_id)
        
        # Filter by days if needed (simplified for mock data)
        total_disputes = len(customer_disputes)
        
        if total_disputes > 0:
            successful = len([d for d in customer_disputes if d.resolution.lower() in ["approved", "resolved"]])
            success_rate = successful / total_disputes
        else:
            success_rate = 0.0
        
        return {
            "customer_id": customer_id,
            "total_disputes": total_disputes,
            "success_rate": success_rate,
            "disputes": [d.dict() for d in customer_disputes],
            "analysis": f"Customer has {total_disputes} disputes in history with {success_rate:.1%} success rate"
        }
    
    async def _check_dispute_policies(self, category: str, amount: float) -> Dict[str, Any]:
        """Check internal dispute policies"""
        policies = self.data_service.get_dispute_policies_by_category(category)
        
        applicable_policies = []
        for policy in policies:
            if amount <= policy.max_amount:
                applicable_policies.append(policy.dict())
        
        return {
            "category": category,
            "amount": amount,
            "applicable_policies": applicable_policies,
            "policies_count": len(applicable_policies),
            "analysis": f"Found {len(applicable_policies)} applicable policies for {category} disputes of ${amount}"
        }
    
    async def _check_account_eligibility(self, customer_id: str) -> Dict[str, Any]:
        """Check account eligibility"""
        account_status = await self.mock_api_service.check_account_status(customer_id, "****1234")
        return account_status
    
    async def _calculate_temporary_credit(self, customer_id: str, dispute_amount: float, dispute_category: str) -> Dict[str, Any]:
        """Calculate temporary credit amount"""
        # Use existing utility function
        from .mock_api_service import calculate_temporary_credit_amount
        
        credit_amount = calculate_temporary_credit_amount(dispute_amount, dispute_category)
        
        return {
            "customer_id": customer_id,
            "dispute_amount": dispute_amount,
            "dispute_category": dispute_category,
            "recommended_credit": credit_amount,
            "credit_percentage": (credit_amount / dispute_amount * 100) if dispute_amount > 0 else 0,
            "analysis": f"Recommended temporary credit: ${credit_amount:.2f} ({credit_amount/dispute_amount*100:.0f}% of dispute amount)"
        }
    
    async def _issue_temporary_credit(self, customer_id: str, amount: float, dispute_id: str) -> Dict[str, Any]:
        """Issue temporary credit"""
        credit_data = {
            "customer_id": customer_id,
            "amount": amount,
            "dispute_id": dispute_id,
            "account_number": "****1234"
        }
        
        result = await self.mock_api_service.issue_temporary_credit(credit_data)
        return result
    
    async def _file_dispute_with_network(self, dispute_data: Dict[str, Any]) -> Dict[str, Any]:
        """File dispute with payment network"""
        result = await self.mock_api_service.file_dispute(dispute_data)
        return result
    
    async def _send_customer_notification(self, customer_id: str, message: str, channel: str = "email") -> Dict[str, Any]:
        """Send customer notification"""
        notification_data = {
            "customer_id": customer_id,
            "message": message,
            "channel": channel
        }
        
        result = await self.mock_api_service.notify_customer(notification_data)
        return result
    
    async def _update_case_management(self, dispute_id: str, status: str, notes: str) -> Dict[str, Any]:
        """Update case management system"""
        case_data = {
            "dispute_id": dispute_id,
            "status": status,
            "notes": notes,
            "priority": "Normal"
        }
        
        result = await self.mock_api_service.update_case_management(case_data)
        return result
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


class MockAPIService:
    """Service for mocking external banking APIs"""
    
    def __init__(self):
        self.mock_delay = float(os.getenv("MOCK_API_DELAY", "1.5"))
        self.dispute_success_rate = 0.85  # 85% success rate for filing
        self.credit_success_rate = 0.95   # 95% success rate for credits
        
    async def file_dispute(self, dispute_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock dispute filing API"""
        await asyncio.sleep(self.mock_delay)
        
        logger.info(f"Filing dispute for customer {dispute_data.get('customer_id')}")
        
        # Simulate random success/failure
        import random
        success = random.random() < self.dispute_success_rate
        
        if success:
            dispute_id = f"DSP{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
            
            return {
                "success": True,
                "dispute_id": dispute_id,
                "reference_number": f"REF{uuid.uuid4().hex[:8].upper()}",
                "status": "Filed",
                "filed_date": datetime.now().isoformat(),
                "estimated_resolution_date": (datetime.now() + timedelta(days=10)).isoformat(),
                "message": "Dispute successfully filed with payment network"
            }
        else:
            return {
                "success": False,
                "error_code": "FILING_ERROR",
                "error_message": "Unable to file dispute at this time. Please try again later.",
                "retry_after": 300  # 5 minutes
            }
    
    async def issue_temporary_credit(self, credit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock temporary credit API"""
        await asyncio.sleep(self.mock_delay * 0.5)  # Credits are faster
        
        logger.info(f"Issuing temporary credit of ${credit_data.get('amount')} to customer {credit_data.get('customer_id')}")
        
        # Simulate random success/failure
        import random
        success = random.random() < self.credit_success_rate
        
        if success:
            credit_id = f"TMP{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
            
            return {
                "success": True,
                "credit_id": credit_id,
                "amount": credit_data.get("amount"),
                "customer_id": credit_data.get("customer_id"),
                "account_number": credit_data.get("account_number", "****1234"),
                "posted_date": datetime.now().isoformat(),
                "description": f"Temporary credit for dispute {credit_data.get('dispute_id', 'N/A')}",
                "reversal_date": (datetime.now() + timedelta(days=10)).isoformat(),
                "message": "Temporary credit successfully posted to account"
            }
        else:
            return {
                "success": False,
                "error_code": "CREDIT_ERROR", 
                "error_message": "Unable to post temporary credit. Account may have restrictions.",
                "retry_after": 600  # 10 minutes
            }
    
    async def check_account_status(self, customer_id: str, account_number: str) -> Dict[str, Any]:
        """Mock account status check API"""
        await asyncio.sleep(self.mock_delay * 0.3)
        
        logger.info(f"Checking account status for customer {customer_id}")
        
        # Simulate account status check
        import random
        
        statuses = ["Active", "Active", "Active", "Restricted", "Frozen"]  # Mostly active
        account_status = random.choice(statuses)
        
        available_balance = random.uniform(100, 5000)
        pending_disputes = random.randint(0, 3)
        
        return {
            "success": True,
            "customer_id": customer_id,
            "account_number": account_number,
            "account_status": account_status,
            "available_balance": round(available_balance, 2),
            "pending_disputes": pending_disputes,
            "last_transaction_date": (datetime.now() - timedelta(days=random.randint(1, 7))).isoformat(),
            "credit_eligible": account_status == "Active" and pending_disputes < 3,
            "dispute_eligible": account_status in ["Active", "Restricted"],
            "restrictions": [] if account_status == "Active" else ["Limited dispute filing"]
        }
    
    async def notify_customer(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock customer notification API (SMS/Email)"""
        await asyncio.sleep(self.mock_delay * 0.2)
        
        logger.info(f"Sending notification to customer {notification_data.get('customer_id')}")
        
        # Simulate notification sending
        import random
        success = random.random() < 0.98  # Very high success rate for notifications
        
        if success:
            notification_id = f"NOT{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
            
            return {
                "success": True,
                "notification_id": notification_id,
                "customer_id": notification_data.get("customer_id"),
                "channel": notification_data.get("channel", "email"),
                "sent_date": datetime.now().isoformat(),
                "message": "Notification sent successfully"
            }
        else:
            return {
                "success": False,
                "error_code": "NOTIFICATION_ERROR",
                "error_message": "Failed to send notification. Contact information may be outdated."
            }
    
    async def update_case_management(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock case management system update"""
        await asyncio.sleep(self.mock_delay * 0.4)
        
        logger.info(f"Updating case management for dispute {case_data.get('dispute_id')}")
        
        case_id = f"CASE{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
        
        return {
            "success": True,
            "case_id": case_id,
            "dispute_id": case_data.get("dispute_id"),
            "assigned_agent": f"Agent{random.randint(100, 999)}",
            "priority": case_data.get("priority", "Normal"),
            "created_date": datetime.now().isoformat(),
            "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
            "status": "Open",
            "workflow_stage": "Investigation",
            "message": "Case created and assigned successfully"
        }
    
    async def simulate_api_delay(self, operation_name: str) -> None:
        """Simulate realistic API delays for different operations"""
        delays = {
            "database_query": 0.3,
            "external_api": 1.0,
            "file_operation": 0.5,
            "validation": 0.2,
            "processing": 0.8
        }
        
        delay = delays.get(operation_name, self.mock_delay)
        await asyncio.sleep(delay)
        
        logger.debug(f"Simulated {operation_name} delay: {delay}s")


# Utility functions for common API patterns
async def validate_dispute_eligibility(customer_id: str, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """Check if customer is eligible to file a dispute"""
    api_service = MockAPIService()
    
    # Check account status
    account_check = await api_service.check_account_status(
        customer_id, 
        transaction_data.get("account_number", "****1234")
    )
    
    if not account_check["success"]:
        return account_check
    
    # Additional validation logic
    eligible = (
        account_check["dispute_eligible"] and
        account_check["pending_disputes"] < 5 and
        float(transaction_data.get("amount", 0)) > 1.00  # Minimum dispute amount
    )
    
    return {
        "success": True,
        "eligible": eligible,
        "account_status": account_check["account_status"],
        "pending_disputes": account_check["pending_disputes"],
        "reason": "Eligible for dispute filing" if eligible else "Does not meet dispute eligibility criteria"
    }


async def calculate_temporary_credit_amount(transaction_amount: float, dispute_category: str) -> float:
    """Calculate appropriate temporary credit amount"""
    # Business rules for temporary credit
    if dispute_category == "Fraud":
        return transaction_amount  # Full amount for fraud
    elif dispute_category == "Billing Error":
        return transaction_amount  # Full amount for billing errors
    elif dispute_category == "Authorization Issue":
        return min(transaction_amount * 0.5, 500.00)  # Partial credit, max $500
    else:
        return 0.0  # No credit for other categories
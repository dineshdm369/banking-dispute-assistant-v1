from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class DisputeCategory(str, Enum):
    FRAUD = "Fraud"
    BILLING_ERROR = "Billing Error"
    AUTHORIZATION_ISSUE = "Authorization Issue"


class DisputeStatus(str, Enum):
    PENDING = "Pending"
    INVESTIGATING = "Investigating"
    APPROVED = "Approved"
    DENIED = "Denied"
    FILED = "Filed"


class LaneStatus(str, Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"


class Transaction(BaseModel):
    transaction_id: str
    customer_id: str
    card_number: str
    card_last_four: str
    merchant_name: str
    merchant_category: str
    amount: float
    currency: str = "USD"
    transaction_date: str
    transaction_time: str
    status: str
    description: str
    location: str
    mcc_code: int
    auth_code: str


class DisputeRequest(BaseModel):
    customer_id: str
    card_last_four: str
    transaction_amount: float
    merchant_name: str
    dispute_reason: str
    dispute_category: DisputeCategory
    additional_details: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class PastDispute(BaseModel):
    dispute_id: str
    transaction_id: str
    customer_id: str
    merchant_name: str
    dispute_reason: str
    dispute_category: str
    amount: float
    dispute_date: str
    resolution: str
    resolution_date: str
    notes: str
    similar_cases: int


class MerchantRisk(BaseModel):
    merchant_name: str
    merchant_id: str
    risk_score: float
    dispute_rate: float
    fraud_incidents_90d: int
    total_transactions_90d: int
    avg_transaction_amount: float
    high_risk_transactions: int
    compliance_score: float
    last_updated: str
    risk_factors: str


class NetworkRule(BaseModel):
    rule_id: str
    network: str
    rule_type: str
    description: str
    time_limit_days: int
    liability_shift: str
    documentation_required: str
    success_rate: float


class DisputePolicy(BaseModel):
    policy_id: str
    category: str
    subcategory: str
    time_limit_hours: int
    max_amount: float
    auto_approve_threshold: float
    investigation_required: bool
    temporary_credit_eligible: bool
    documentation_required: List[str]
    processing_time_days: int
    success_rate: float


class LaneResult(BaseModel):
    lane_name: str
    status: LaneStatus
    data: Dict[str, Any]
    confidence: float
    processing_time: float
    error_message: Optional[str] = None


class AgentStep(BaseModel):
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    step_name: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    confidence: float
    reasoning: str


class DisputeAssessment(BaseModel):
    dispute_request: DisputeRequest
    matched_transaction: Optional[Transaction] = None
    past_disputes: List[PastDispute] = []
    merchant_risk: Optional[MerchantRisk] = None
    network_rules: List[NetworkRule] = []
    applicable_policies: List[DisputePolicy] = []
    lane_results: List[LaneResult] = []
    overall_confidence: float
    recommendation: str
    reasoning: str
    back_office_notes: Dict[str, Any]
    temporary_credit_amount: float = 0.0
    dispute_likely_success: bool = False


class DisputeResponse(BaseModel):
    dispute_id: str
    status: DisputeStatus
    customer_response: str
    back_office_notes: Dict[str, Any]
    temporary_credit_issued: bool
    temporary_credit_amount: float
    estimated_resolution_days: int
    confidence_score: float
    next_steps: List[str]
    supporting_evidence: List[str]
    processing_steps: List[AgentStep]
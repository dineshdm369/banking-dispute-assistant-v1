import pandas as pd
import os
from typing import List, Optional
from ..models import (
    Transaction, PastDispute, MerchantRisk, 
    NetworkRule, DisputePolicy
)


class DataService:
    """Service for loading and querying mock data"""
    
    def __init__(self, data_path: str = "./data"):
        self.data_path = data_path
        self._transactions_df = None
        self._disputes_df = None
        self._merchant_risk_df = None
        self._network_rules_df = None
        self._policies_df = None
        
    def _load_transactions(self) -> pd.DataFrame:
        """Load transactions data"""
        if self._transactions_df is None:
            file_path = os.path.join(self.data_path, "transactions.csv")
            self._transactions_df = pd.read_csv(file_path)
        return self._transactions_df
    
    def _load_disputes(self) -> pd.DataFrame:
        """Load past disputes data"""
        if self._disputes_df is None:
            file_path = os.path.join(self.data_path, "past_disputes.csv")
            self._disputes_df = pd.read_csv(file_path)
        return self._disputes_df
    
    def _load_merchant_risk(self) -> pd.DataFrame:
        """Load merchant risk data"""
        if self._merchant_risk_df is None:
            file_path = os.path.join(self.data_path, "merchant_risk.csv")
            self._merchant_risk_df = pd.read_csv(file_path)
        return self._merchant_risk_df
    
    def _load_network_rules(self) -> pd.DataFrame:
        """Load network rules data"""
        if self._network_rules_df is None:
            file_path = os.path.join(self.data_path, "network_rules.csv")
            self._network_rules_df = pd.read_csv(file_path)
        return self._network_rules_df
    
    def _load_policies(self) -> pd.DataFrame:
        """Load dispute policies data"""
        if self._policies_df is None:
            file_path = os.path.join(self.data_path, "dispute_policies.csv")
            self._policies_df = pd.read_csv(file_path)
        return self._policies_df
    
    def get_transactions_by_card(self, card_last_four: str, days: int = 90) -> List[Transaction]:
        """Get transactions for a card in the last N days"""
        df = self._load_transactions()
        
        # Convert card_last_four to string for comparison (handle both string and int types in CSV)
        df_card_str = df['card_last_four'].astype(str)
        
        # Filter by card last four digits
        filtered_df = df[df_card_str == str(card_last_four)]
        
        # Convert to Transaction objects
        transactions = []
        for _, row in filtered_df.iterrows():
            row_dict = row.to_dict()
            # Convert numeric fields to strings where needed
            row_dict['card_number'] = str(row_dict['card_number'])
            row_dict['card_last_four'] = str(row_dict['card_last_four'])
            transactions.append(Transaction(**row_dict))
        
        return transactions
    
    def find_transaction(self, card_last_four: str, amount: float, merchant_name: str) -> Optional[Transaction]:
        """Find a specific transaction by card, amount, and merchant"""
        df = self._load_transactions()
        
        # Convert card_last_four to string for comparison (handle both string and int types in CSV)
        df_card_str = df['card_last_four'].astype(str)
        
        # Filter by criteria
        filtered_df = df[
            (df_card_str == str(card_last_four)) &
            (abs(df['amount'] - amount) < 0.01) &  # Allow small floating point differences
            (df['merchant_name'].str.contains(merchant_name, case=False, na=False))
        ]
        
        if not filtered_df.empty:
            # Return the first match
            row = filtered_df.iloc[0].copy()
            # Convert numeric fields to strings where needed
            row_dict = row.to_dict()
            row_dict['card_number'] = str(row_dict['card_number'])
            row_dict['card_last_four'] = str(row_dict['card_last_four'])
            return Transaction(**row_dict)
        
        return None
    
    def get_past_disputes_by_merchant(self, merchant_name: str) -> List[PastDispute]:
        """Get past disputes for a specific merchant"""
        df = self._load_disputes()
        
        # Filter by merchant name (case insensitive)
        filtered_df = df[df['merchant_name'].str.contains(merchant_name, case=False, na=False)]
        
        disputes = []
        for _, row in filtered_df.iterrows():
            disputes.append(PastDispute(**row.to_dict()))
        
        return disputes
    
    def get_past_disputes_by_customer(self, customer_id: str) -> List[PastDispute]:
        """Get past disputes for a specific customer"""
        df = self._load_disputes()
        
        # Filter by customer ID
        filtered_df = df[df['customer_id'] == customer_id]
        
        disputes = []
        for _, row in filtered_df.iterrows():
            disputes.append(PastDispute(**row.to_dict()))
        
        return disputes
    
    def get_merchant_risk_data(self, merchant_name: str) -> Optional[MerchantRisk]:
        """Get risk data for a specific merchant"""
        df = self._load_merchant_risk()
        
        # Filter by merchant name (case insensitive)
        filtered_df = df[df['merchant_name'].str.contains(merchant_name, case=False, na=False)]
        
        if not filtered_df.empty:
            row = filtered_df.iloc[0]
            return MerchantRisk(**row.to_dict())
        
        return None
    
    def get_dispute_policies_by_category(self, category: str) -> List[DisputePolicy]:
        """Get dispute policies by category"""
        df = self._load_policies()
        
        # Filter by category
        filtered_df = df[df['category'].str.contains(category, case=False, na=False)]
        
        policies = []
        for _, row in filtered_df.iterrows():
            # Convert documentation_required from string to list
            doc_req = row['documentation_required']
            if isinstance(doc_req, str):
                # Parse string representation of list
                import ast
                try:
                    doc_req = ast.literal_eval(doc_req)
                except (ValueError, SyntaxError):
                    # Fallback to simple comma-separated parsing
                    doc_req = [doc.strip() for doc in doc_req.split(',')]
            row_dict = row.to_dict()
            row_dict['documentation_required'] = doc_req
            
            policies.append(DisputePolicy(**row_dict))
        
        return policies
    
    def get_network_rules_by_category(self, category: str) -> List[NetworkRule]:
        """Get network rules by dispute category"""
        df = self._load_network_rules()
        
        # Map categories to rule types
        category_map = {
            "Fraud": "Fraud",
            "Billing Error": "Processing Error",
            "Authorization Issue": "Authorization"
        }
        
        rule_type = category_map.get(category, category)
        filtered_df = df[df['rule_type'].str.contains(rule_type, case=False, na=False)]
        
        rules = []
        for _, row in filtered_df.iterrows():
            rules.append(NetworkRule(**row.to_dict()))
        
        return rules
    
    def get_applicable_policies(self, category: str, amount: float) -> List[DisputePolicy]:
        """Get applicable dispute policies"""
        df = self._load_policies()
        
        # Filter by category and amount
        filtered_df = df[
            (df['category'].str.contains(category, case=False, na=False)) &
            (df['max_amount'] >= amount)
        ]
        
        policies = []
        for _, row in filtered_df.iterrows():
            # Convert documentation_required from string to list
            doc_req = row['documentation_required']
            if isinstance(doc_req, str):
                # Parse string representation of list
                import ast
                try:
                    doc_req = ast.literal_eval(doc_req)
                except (ValueError, SyntaxError):
                    # Fallback to simple comma-separated parsing
                    doc_req = [doc.strip() for doc in doc_req.split(',')]
            row_dict = row.to_dict()
            row_dict['documentation_required'] = doc_req
            
            policies.append(DisputePolicy(**row_dict))
        
        return policies
    
    def get_all_merchants(self) -> List[str]:
        """Get list of all merchants"""
        df = self._load_transactions()
        return df['merchant_name'].unique().tolist()
    
    def get_transaction_stats(self) -> dict:
        """Get basic transaction statistics"""
        df = self._load_transactions()
        
        return {
            "total_transactions": len(df),
            "total_amount": df['amount'].sum(),
            "avg_amount": df['amount'].mean(),
            "unique_merchants": df['merchant_name'].nunique(),
            "unique_customers": df['customer_id'].nunique(),
            "date_range": {
                "start": df['transaction_date'].min(),
                "end": df['transaction_date'].max()
            }
        }
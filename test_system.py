#!/usr/bin/env python3
"""
Test script for banking-dispute-assistant-v1
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.models import DisputeRequest, DisputeCategory
from src.services.data_service import DataService
from src.utils.helpers import setup_logging, load_environment


async def test_basic_functionality():
    """Test basic functionality without OpenAI"""
    print("🧪 Testing banking-dispute-assistant-v1 Components...")
    
    # Set up logging
    setup_logging("INFO")
    
    # Test data service
    print("\n📊 Testing Data Service...")
    data_service = DataService()
    
    # Test loading data
    try:
        transactions = data_service.get_transactions_by_card("1234", 90)
        print(f"✅ Loaded {len(transactions)} transactions")
        
        merchants = data_service.get_all_merchants()
        print(f"✅ Found {len(merchants)} unique merchants")
        
        stats = data_service.get_transaction_stats()
        print(f"✅ Transaction stats: {stats['total_transactions']} total transactions")
        
    except Exception as e:
        print(f"❌ Data service error: {e}")
        return False
    
    # Test models
    print("\n📝 Testing Data Models...")
    try:
        dispute_request = DisputeRequest(
            customer_id="CUST1234",
            card_last_four="1234",
            transaction_amount=100.50,
            merchant_name="Amazon",
            dispute_reason="Unauthorized transaction",
            dispute_category=DisputeCategory.FRAUD
        )
        print(f"✅ Created dispute request: {dispute_request.dispute_category}")
        
    except Exception as e:
        print(f"❌ Model error: {e}")
        return False
    
    # Test configuration
    print("\n⚙️ Testing Configuration...")
    try:
        config = load_environment()
        print(f"✅ Loaded configuration with {len(config)} settings")
        
        if not config.get('openai_api_key') or config['openai_api_key'] == 'sk-your-actual-openai-api-key-here':
            print("⚠️  Warning: OpenAI API key not set - agent functionality will be limited")
        else:
            print("✅ OpenAI API key configured")
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    print("\n🎉 All basic tests passed!")
    return True


async def test_mock_apis():
    """Test mock API services"""
    print("\n🔧 Testing Mock API Services...")
    
    try:
        from src.services.mock_api_service import MockAPIService
        
        api_service = MockAPIService()
        
        # Test dispute filing
        dispute_result = await api_service.file_dispute({
            "customer_id": "CUST1234",
            "transaction_amount": 100.00,
            "merchant_name": "Test Merchant"
        })
        
        print(f"✅ Dispute filing test: {dispute_result.get('success', False)}")
        
        # Test temporary credit
        credit_result = await api_service.issue_temporary_credit({
            "customer_id": "CUST1234",
            "amount": 50.00,
            "dispute_id": "DSP123456"
        })
        
        print(f"✅ Temporary credit test: {credit_result.get('success', False)}")
        
        # Test account status
        account_result = await api_service.check_account_status("CUST1234", "****1234")
        print(f"✅ Account status test: {account_result.get('success', False)}")
        
    except Exception as e:
        print(f"❌ Mock API error: {e}")
        return False
    
    print("✅ Mock API tests completed")
    return True


def test_data_files():
    """Test that all data files are present and readable"""
    print("\n📂 Testing Data Files...")
    
    data_files = [
        "data/transactions.csv",
        "data/past_disputes.csv", 
        "data/merchant_risk.csv",
        "data/network_rules.csv",
        "data/dispute_policies.csv"
    ]
    
    for file_path in data_files:
        if os.path.exists(file_path):
            try:
                import pandas as pd
                df = pd.read_csv(file_path)
                print(f"✅ {file_path}: {len(df)} rows")
            except Exception as e:
                print(f"❌ {file_path}: Error reading - {e}")
                return False
        else:
            print(f"❌ {file_path}: File not found")
            return False
    
    return True


async def main():
    """Main test function"""
    print("🚀 banking-dispute-assistant-v1 - System Test")
    print("=" * 50)
    
    # Test data files first
    if not test_data_files():
        print("\n❌ Data file tests failed")
        return 1
    
    # Test basic functionality
    if not await test_basic_functionality():
        print("\n❌ Basic functionality tests failed")
        return 1
    
    # Test mock APIs
    if not await test_mock_apis():
        print("\n❌ Mock API tests failed")
        return 1
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! System is ready.")
    print("\nTo run the Streamlit app:")
    print("  streamlit run streamlit_app.py")
    print("\nTo run with Docker:")
    print("  docker-compose up --build")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
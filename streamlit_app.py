import streamlit as st
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any
import pandas as pd

# Import our modules
from src.models import DisputeRequest, DisputeCategory
from src.agents.dispute_agent import BankingDisputeAgent
from src.utils.helpers import (
    setup_logging, load_environment, validate_config,
    format_currency, mask_sensitive_data, get_status_color, UI_COLORS
)

# Page configuration
st.set_page_config(
    page_title="Banking Dispute Agent",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apple-inspired CSS styling
st.markdown("""
<style>
    /* Main app styling */
    .main {
        padding: 1rem 2rem;
    }
    
    /* Card-like containers */
    .dispute-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border: 1px solid #E5E5EA;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 500;
        color: white;
        margin: 0.25rem;
    }
    
    .status-completed { background-color: #34C759; }
    .status-processing { background-color: #FF9500; }
    .status-pending { background-color: #5856D6; }
    .status-failed { background-color: #FF3B30; }
    
    /* Progress indicators */
    .progress-lane {
        display: flex;
        align-items: center;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        background: #F2F2F7;
        border-left: 4px solid #007AFF;
    }
    
    /* Headers */
    .section-header {
        color: #1D1D1F;
        font-size: 1.5rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
        border-bottom: 2px solid #007AFF;
        padding-bottom: 0.5rem;
    }
    
    /* Metrics */
    .metric-container {
        background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
        border-radius: 12px;
        padding: 1.5rem;
        color: white;
        text-align: center;
        margin: 0.5rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.875rem;
        opacity: 0.9;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
        border: none;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        padding: 0.75rem 1.5rem;
        transition: all 0.2s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,122,255,0.3);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: #F2F2F7;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def initialize_app():
    """Initialize the application"""
    if 'initialized' not in st.session_state:
        # Load configuration
        config = load_environment()
        
        # Set up logging
        setup_logging(config.get('log_level', 'INFO'))
        
        # Validate configuration
        try:
            validate_config(config)
            st.session_state.config = config
            st.session_state.agent = BankingDisputeAgent(config.get('openai_api_key'))
            st.session_state.initialized = True
        except ValueError as e:
            st.error(f"Configuration error: {e}")
            st.info("Please set your OpenAI API key in the .env file or environment variables.")
            st.stop()


def render_header():
    """Render application header"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="color: #1D1D1F; font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;">
                🏦 Banking Dispute Agent
            </h1>
            <p style="color: #6D6D70; font-size: 1.125rem; margin: 0;">
                AI-powered dispute processing with agentic workflows
            </p>
        </div>
        """, unsafe_allow_html=True)


def render_dispute_form():
    """Render the dispute input form"""
    st.markdown('<div class="section-header">📋 File a Dispute</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="dispute-card">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            customer_id = st.text_input(
                "Customer ID",
                placeholder="CUST1234",
                help="Enter your customer identification number"
            )
            
            card_last_four = st.text_input(
                "Card Last 4 Digits",
                placeholder="1234",
                max_chars=4,
                help="Last 4 digits of the card used for the transaction"
            )
            
            transaction_amount = st.number_input(
                "Transaction Amount ($)",
                min_value=0.01,
                max_value=10000.00,
                value=50.00,
                step=0.01,
                help="Amount of the disputed transaction"
            )
        
        with col2:
            merchant_name = st.text_input(
                "Merchant Name",
                placeholder="Amazon",
                help="Name of the merchant where the transaction occurred"
            )
            
            dispute_category = st.selectbox(
                "Dispute Category",
                options=[category.value for category in DisputeCategory],
                help="Select the type of dispute"
            )
            
            dispute_reason = st.text_area(
                "Dispute Reason",
                placeholder="Please describe why you're disputing this transaction...",
                height=100,
                help="Provide details about why you're disputing this charge"
            )
        
        additional_details = st.text_area(
            "Additional Details (Optional)",
            placeholder="Any additional information that might help with your dispute...",
            height=80
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Submit button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚀 Process Dispute", use_container_width=True):
                if all([customer_id, card_last_four, merchant_name, dispute_reason]):
                    dispute_request = DisputeRequest(
                        customer_id=customer_id,
                        card_last_four=card_last_four,
                        transaction_amount=transaction_amount,
                        merchant_name=merchant_name,
                        dispute_reason=dispute_reason,
                        dispute_category=DisputeCategory(dispute_category),
                        additional_details=additional_details if additional_details else None
                    )
                    
                    st.session_state.dispute_request = dispute_request
                    st.session_state.processing = True
                    st.rerun()
                else:
                    st.error("Please fill in all required fields")


def render_processing_status():
    """Render real-time processing status"""
    if 'processing' in st.session_state and st.session_state.processing:
        st.markdown('<div class="section-header">⚡ Processing Your Dispute</div>', unsafe_allow_html=True)
        
        # Create placeholders for dynamic updates
        status_container = st.container()
        lanes_container = st.container()
        progress_container = st.container()
        
        # Process the dispute
        dispute_response = asyncio.run(
            st.session_state.agent.process_dispute(st.session_state.dispute_request)
        )
        
        st.session_state.dispute_response = dispute_response
        st.session_state.processing = False
        st.rerun()


def render_lane_progress():
    """Render parallel lane processing progress"""
    st.markdown('<div class="section-header">🔄 Parallel Analysis Lanes</div>', unsafe_allow_html=True)
    
    # Simulate lane progress for demo
    lanes = [
        {"name": "Past Disputes Analysis", "status": "completed", "confidence": 0.85},
        {"name": "Merchant Risk Assessment", "status": "completed", "confidence": 0.78},
        {"name": "Network Rules Check", "status": "completed", "confidence": 0.92}
    ]
    
    cols = st.columns(3)
    
    for i, lane in enumerate(lanes):
        with cols[i]:
            st.markdown(f"""
            <div class="progress-lane">
                <div style="flex: 1;">
                    <div style="font-weight: 600; margin-bottom: 0.25rem;">{lane['name']}</div>
                    <div class="status-indicator status-{lane['status']}">{lane['status'].title()}</div>
                    <div style="margin-top: 0.5rem; font-size: 0.875rem; color: #6D6D70;">
                        Confidence: {lane['confidence']:.1%}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_agent_reasoning():
    """Render agent decision-making process"""
    if 'dispute_response' not in st.session_state:
        return
        
    st.markdown('<div class="section-header">🧠 Agent Reasoning Process</div>', unsafe_allow_html=True)
    
    response = st.session_state.dispute_response
    
    # Create tabs for different aspects of reasoning
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Processing Steps", 
        "🎯 Decision Logic", 
        "📋 Back-Office Notes",
        "🔍 Supporting Evidence"
    ])
    
    with tab1:
        st.markdown('<div class="dispute-card">', unsafe_allow_html=True)
        
        if response.processing_steps:
            for i, step in enumerate(response.processing_steps):
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                
                with col1:
                    st.write(f"**{step.step_name.replace('_', ' ').title()}**")
                
                with col2:
                    status_class = f"status-{step.status}"
                    st.markdown(f'<div class="status-indicator {status_class}">{step.status}</div>', 
                              unsafe_allow_html=True)
                
                with col3:
                    st.write(f"{step.confidence:.1%}")
                
                with col4:
                    if step.duration:
                        st.write(f"{step.duration:.1f}s")
                
                if step.reasoning:
                    st.caption(step.reasoning)
                
                if i < len(response.processing_steps) - 1:
                    st.markdown("---")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="dispute-card">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                label="Overall Confidence",
                value=f"{response.confidence_score:.1%}",
                delta=f"Threshold: {st.session_state.config.get('confidence_threshold', 0.7):.1%}"
            )
        
        with col2:
            st.metric(
                label="Estimated Resolution",
                value=f"{response.estimated_resolution_days} days",
                delta="Business days"
            )
        
        st.subheader("Decision Factors")
        factors = [
            f"✅ Transaction verified and matched" if response.temporary_credit_issued else "❌ Transaction verification failed",
            f"✅ Customer eligible for dispute" if response.status.value != "Denied" else "❌ Customer not eligible",
            f"✅ Temporary credit issued: {format_currency(response.temporary_credit_amount)}" if response.temporary_credit_issued else "❌ No temporary credit issued",
            f"✅ Dispute filed successfully" if response.status.value == "Filed" else "⏳ Dispute filing pending"
        ]
        
        for factor in factors:
            st.write(factor)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<div class="dispute-card">', unsafe_allow_html=True)
        
        if response.back_office_notes:
            st.json(response.back_office_notes)
        else:
            st.info("No back-office notes available")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab4:
        st.markdown('<div class="dispute-card">', unsafe_allow_html=True)
        
        st.subheader("Evidence Collected")
        for evidence in response.supporting_evidence:
            st.write(f"• {evidence}")
        
        st.subheader("Next Steps")
        for step in response.next_steps:
            st.write(f"• {step}")
        
        st.markdown('</div>', unsafe_allow_html=True)


def render_dispute_response():
    """Render the final dispute response"""
    if 'dispute_response' not in st.session_state:
        return
        
    st.markdown('<div class="section-header">✅ Dispute Response</div>', unsafe_allow_html=True)
    
    response = st.session_state.dispute_response
    
    # Status overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{response.status.value}</div>
            <div class="metric-label">Status</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{response.dispute_id}</div>
            <div class="metric-label">Dispute ID</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{response.confidence_score:.1%}</div>
            <div class="metric-label">Confidence</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        credit_text = format_currency(response.temporary_credit_amount) if response.temporary_credit_issued else "None"
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{credit_text}</div>
            <div class="metric-label">Temp Credit</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Customer response
    st.markdown('<div class="dispute-card">', unsafe_allow_html=True)
    st.subheader("Customer Communication")
    st.write(response.customer_response)
    st.markdown('</div>', unsafe_allow_html=True)


def render_sidebar():
    """Render sidebar with system information"""
    with st.sidebar:
        st.markdown("### 🏦 System Status")
        
        if 'config' in st.session_state:
            st.success("✅ System Online")
            st.write(f"**App:** {st.session_state.config.get('app_name', 'N/A')}")
            st.write(f"**Environment:** {'Debug' if st.session_state.config.get('debug') else 'Production'}")
        else:
            st.error("❌ Configuration Error")
        
        st.markdown("---")
        
        st.markdown("### 📊 Statistics")
        
        # Mock statistics
        stats = {
            "Disputes Processed": 1,
            "Average Confidence": "85.3%",
            "Success Rate": "92.1%",
            "Avg Processing Time": "12.4s"
        }
        
        for label, value in stats.items():
            st.metric(label, value)
        
        st.markdown("---")
        
        st.markdown("### 🔧 Actions")
        
        if st.button("🔄 Reset Session"):
            for key in list(st.session_state.keys()):
                if key not in ['initialized', 'config', 'agent']:
                    del st.session_state[key]
            st.rerun()
        
        if st.button("📥 Download Report"):
            if 'dispute_response' in st.session_state:
                report_data = {
                    "dispute_id": st.session_state.dispute_response.dispute_id,
                    "status": st.session_state.dispute_response.status.value,
                    "confidence": st.session_state.dispute_response.confidence_score,
                    "timestamp": datetime.now().isoformat()
                }
                
                st.download_button(
                    label="Download JSON Report",
                    data=json.dumps(report_data, indent=2),
                    file_name=f"dispute_report_{report_data['dispute_id']}.json",
                    mime="application/json"
                )


def main():
    """Main application entry point"""
    # Initialize the application
    initialize_app()
    
    # Render the application
    render_header()
    render_sidebar()
    
    # Main content area
    if 'processing' in st.session_state and st.session_state.processing:
        render_processing_status()
        render_lane_progress()
    elif 'dispute_response' in st.session_state:
        render_dispute_response()
        render_agent_reasoning()
        
        # Option to file another dispute
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("📝 File Another Dispute", use_container_width=True):
                # Clear current dispute data but keep system initialized
                for key in ['dispute_request', 'dispute_response', 'processing']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    else:
        render_dispute_form()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6D6D70; font-size: 0.875rem; padding: 1rem;">
        Banking Dispute Agent v1.0 | Powered by OpenAI GPT-4o Mini & LangChain
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
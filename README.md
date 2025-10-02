# 🏦 Banking Dispute Agent

An AI-powered banking dispute processing system that demonstrates agentic workflow patterns using OpenAI's GPT-4o Mini and a sophisticated multi-lane analysis approach.

## 🚀 Features

### Enhanced User Experience
- **User Authentication**: Role-based user selection with department tracking
- **Session Management**: Unique session IDs for complete audit trails
- **Real-time Progress**: Live updates during multi-stage processing
- **Apple-inspired UI**: Clean, intuitive interface with responsive design

### Agentic Workflow Implementation
The system implements a comprehensive agentic workflow:

1. **Plan** - Decide analysis steps and strategy
2. **Retrieve** - Pull transaction data and policies  
3. **Fork** - Execute parallel analysis lanes:
   - **Lane A**: Past disputes analysis for similar merchants
   - **Lane B**: Merchant risk signal assessment  
   - **Lane C**: Payment network rules compliance check
4. **Synthesize** - Merge findings from all lanes
5. **Generate** - Create customer response and back-office notes
6. **Act** - File dispute and issue temporary credit via APIs
7. **Critique** - Self-assessment for quality and completeness
8. **Finalize** - Complete processing with potential loop-back

### Technical Capabilities
- **OpenAI Integration**: Uses GPT-4o Mini with function calling and structured output
- **Parallel Processing**: Async execution of analysis lanes for efficiency  
- **Mock Banking APIs**: Realistic simulation of dispute filing and credit systems
- **Data Validation**: Pydantic v2 models with comprehensive validation
- **Error Handling**: Robust error recovery and safe JSON serialization
- **Observability Ready**: Structured for future tracing and monitoring integration

## 📁 Project Structure

```
banking-dispute-agent/
├── data/                    # Mock data files (CSV format)
│   ├── users.csv            # 10 user profiles with departments
│   ├── transactions.csv     # 50 realistic banking transactions
│   ├── past_disputes.csv    # 25 historical dispute records
│   ├── merchant_risk.csv    # Risk profiles for 30 merchants
│   ├── network_rules.csv    # Visa/Mastercard chargeback rules
│   └── dispute_policies.csv # Bank dispute policies
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md      # System architecture guide
│   └── SPECIFICATION.md     # Technical specifications
├── src/
│   ├── agents/             # Core agent implementation
│   │   └── dispute_agent.py # Main agentic workflow
│   ├── services/           # Service layer
│   │   ├── data_service.py    # Data access and querying
│   │   ├── openai_service.py  # OpenAI API integration
│   │   └── mock_api_service.py # Mock banking APIs
│   ├── models/             # Pydantic v2 data models
│   │   └── __init__.py     # All data models and types
│   └── utils/              # Utility functions
│       └── helpers.py      # Common utilities and safe JSON handling
├── streamlit_app.py        # Main UI application with user auth
├── test_system.py          # System verification script
├── generate_mock_data.py   # Data generation utility
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
├── docker-compose.yml     # Multi-service deployment
├── LICENSE                # MIT License
├── .env.example           # Environment template
└── .env                   # Environment configuration
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.11+
- OpenAI API key
- Docker (optional)

### Local Setup

1. **Clone and navigate to the project:**
   ```bash
   cd banking-dispute-agent
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Generate mock data (already done):**
   ```bash
   python generate_mock_data.py
   ```

5. **Test the system:**
   ```bash
   python test_system.py
   ```

6. **Run the application:**
   ```bash
   streamlit run streamlit_app.py
   ```

### Docker Setup

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   - Open http://localhost:8501 in your browser

## 🎯 Usage

### Filing a Dispute

1. **Open the application** in your browser
2. **Select a user profile** from the dropdown (e.g., John Smith - Customer Service)
3. **Fill in the dispute form:**
   - Customer ID (e.g., CUST1234)
   - Card last 4 digits (e.g., 1234)  
   - Transaction amount
   - Merchant name
   - Dispute category (Fraud, Billing Error, Authorization Issue)
   - Detailed reason for dispute

4. **Click "Process Dispute"** to start the agentic workflow

4. **Watch real-time processing:**
   - See parallel lanes execute simultaneously
   - Monitor confidence scores and reasoning
   - Track decision-making process

5. **Review results:**
   - Customer response message
   - Temporary credit information
   - Back-office notes and evidence
   - Next steps and recommendations

### Understanding the Agent Reasoning

The interface provides detailed visibility into:

- **Processing Steps**: Each workflow stage with timing and confidence
- **Decision Logic**: How the agent reached its conclusions  
- **Back-Office Notes**: Structured data for bank operations
- **Supporting Evidence**: Documentation and analysis results

## 🔧 Configuration

### Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Application Settings
APP_NAME=Banking Dispute Agent
DEBUG=false
LOG_LEVEL=INFO

# Agent Parameters  
CONFIDENCE_THRESHOLD=0.7    # Minimum confidence for auto-approval
PROCESSING_DELAY=2          # Delay between steps (for demo)
MAX_PARALLEL_LANES=3        # Number of analysis lanes

# Mock API Settings
MOCK_API_DELAY=1.5          # Simulated API response time
```

### Customization

- **Data**: Replace CSV files in `/data` with your own datasets
- **Models**: Extend Pydantic models in `src/models/`  
- **Agents**: Modify workflow logic in `src/agents/dispute_agent.py`
- **UI**: Customize Streamlit interface in `streamlit_app.py`

## 📊 Mock Data

The system includes realistic mock data:

- **10 user profiles** across different bank departments
- **50 transactions** across 30 major merchants
- **25 historical disputes** with various outcomes
- **30 merchant risk profiles** with scoring
- **5 network rules** for Visa/Mastercard compliance
- **3 dispute policies** covering different categories

All data uses realistic but fake information suitable for testing and education.

## 🔮 Future Enhancements

### Observability Integration
The system is designed for easy integration with observability tools:

- **Tracing**: Each agent step is structured for distributed tracing
- **Metrics**: Confidence scores and processing times are tracked
- **Logging**: Structured logs with correlation IDs
- **Monitoring**: Health checks and performance metrics

### Planned Features
- [ ] Integration with OpenTelemetry for tracing
- [ ] Real banking API connections
- [ ] Advanced ML risk scoring
- [ ] Multi-language support
- [ ] Compliance reporting dashboard
- [ ] Database integration (PostgreSQL/MongoDB)
- [ ] Role-based access control (RBAC)
- [ ] API rate limiting and caching

## 🛡️ Security & Privacy

- **No real financial data**: All data is mock/synthetic
- **API key security**: Environment-based configuration
- **Input sanitization**: User inputs are validated and sanitized
- **Audit trail**: Complete processing history is maintained

## 🧪 Testing

Run the test suite:
```bash
python test_system.py
```

The test verifies:
- Data file integrity
- Model validation
- Service functionality  
- Mock API responses
- Configuration loading

## 📈 Performance

Typical processing times:
- **End-to-end dispute**: 10-15 seconds
- **Parallel lane execution**: 3-5 seconds  
- **OpenAI API calls**: 1-3 seconds each
- **Data retrieval**: <1 second

Performance scales with:
- OpenAI API response times
- Data volume in CSV files
- Number of parallel lanes
- Mock API delay settings

## 🤝 Contributing

This is a demonstration project showcasing agentic workflow patterns. Key areas for contribution:

1. **Agent Logic**: Enhance decision-making algorithms
2. **Data Models**: Extend for more complex scenarios  
3. **UI/UX**: Improve interface and visualizations
4. **Integrations**: Add real banking system connections
5. **Observability**: Implement comprehensive monitoring

## 📚 Documentation

For detailed technical information, see:
- **[System Architecture](docs/ARCHITECTURE.md)** - Comprehensive architecture overview
- **[Technical Specification](docs/SPECIFICATION.md)** - Detailed system specifications

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

For questions or issues:
1. Check the test output: `python test_system.py`
2. Review logs in the Streamlit interface
3. Verify OpenAI API key configuration
4. Ensure all dependencies are installed

---

## 🎓 Educational Purpose Disclaimer

**This project is created exclusively for educational and learning purposes.**

- **All data used in this system is synthetic and fictitious** - no real financial information, customer data, or banking records are used
- **Mock banking APIs simulate real systems** - no actual banking transactions or disputes are processed
- **User profiles and scenarios are educational examples** - not representative of real banking operations
- **AI reasoning and decisions are for demonstration only** - not suitable for production financial services

This system is designed to teach and demonstrate:
- Agentic AI workflow patterns
- Multi-lane parallel processing
- OpenAI integration best practices
- Clean software architecture principles
- Modern Python development techniques

**For learning purposes only** - please ensure compliance with your organization's policies and applicable regulations before adapting any concepts for production use.

---

**Built with:** OpenAI GPT-4o Mini, Streamlit, Python 3.11, Pydantic v2, Pandas
**Design inspiration:** Apple's design principles for clean, intuitive interfaces
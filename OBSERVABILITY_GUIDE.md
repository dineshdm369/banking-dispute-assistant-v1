# Observability Enhancement for banking-dispute-assistant-v1

## Overview

This enhancement adds user and session context to the banking-dispute-assistant-v1, enabling comprehensive observability instrumentation with third-party tools like Datadog, New Relic, OpenTelemetry, Splunk, and others.

## Changes Made

### 1. Enhanced Data Model (`src/models/__init__.py`)

Added two optional fields to the `DisputeRequest` model:

```python
class DisputeRequest(BaseModel):
    # ... existing fields ...
    user_id: Optional[str] = None      # User who initiated the dispute
    session_id: Optional[str] = None   # Unique session identifier
```

### 2. Updated Streamlit Frontend (`streamlit_app.py`)

Modified the dispute request creation to include user and session context:

```python
dispute_request = DisputeRequest(
    # ... existing fields ...
    user_id=st.session_state.get('current_user_id'),
    session_id=st.session_state.get('session_id')
)
```

### 3. Enhanced Agent Logging (`src/agents/dispute_agent.py`)

Added structured logging with user/session context throughout the agent workflow:

```python
logger.info(
    "Starting dispute processing",
    extra={
        "user_id": dispute_request.user_id,
        "session_id": dispute_request.session_id,
        "customer_id": dispute_request.customer_id,
        "dispute_category": dispute_request.dispute_category,
        "transaction_amount": dispute_request.transaction_amount
    }
)
```

## Current Implementation Benefits

### Complete Audit Trail ✅
Every operation is now fully traceable:

```bash
# User authentication and session creation
User selects "Sarah Johnson" → Session USR002_20251004_115317_57ea012e created

# Dispute processing with full context
2025-10-04 11:54:12,152 - src.agents.intelligent_dispute_agent - INFO - Starting intelligent dispute processing [user_id=USR002, session_id=USR002_20251004_115317_57ea012e, dispute_id=BDA2025100411541269ECC04B]

# Every function call tracked with session context
2025-10-04 11:54:17,608 - src.services.function_registry - INFO - Executing function get_customer_dispute_history [user_id=USR002, session_id=USR002_20251004_115317_57ea012e, function=get_customer_dispute_history]

# Processing completion with metrics
2025-10-04 11:54:30,057 - src.agents.intelligent_dispute_agent - INFO - Dispute processing completed successfully [user_id=USR002, session_id=USR002_20251004_115317_57ea012e, dispute_id=BDA2025100411541269ECC04B]
```

### Enhanced Debugging Capabilities ✅
- **Filter by session_id**: See complete user workflow
- **Track function performance**: Individual function execution times
- **User behavior analysis**: Department-based usage patterns
- **Error correlation**: Link errors to specific user sessions

### Cost Attribution Ready ✅
- **OpenAI API usage**: Track by user_id and session_id  
- **Function call frequency**: Monitor usage by department
- **Processing time analysis**: Identify optimization opportunities
- **Resource allocation**: Plan capacity based on user patterns

## Key Features Implemented

### 1. Session Lifecycle Management
- **User Authentication**: Role-based user selection from predefined profiles
- **Session Generation**: Automatic creation of unique session identifiers
- **Context Propagation**: Session data flows through entire system
- **Audit Trail**: Complete tracking from user login to dispute completion

### 2. Enhanced Function Registry
- **Session Context Injection**: All function calls include user and session data
- **Structured Logging**: Consistent log format with session information
- **Error Attribution**: Function failures linked to specific user sessions
- **Performance Tracking**: Function execution times by user context

### 3. Production-Ready Monitoring
- **Log Filtering**: Easy identification of user-specific issues
- **Metrics Collection**: Built-in support for observability tools
- **Compliance Ready**: Audit trails suitable for regulatory requirements
- **Debugging Support**: Complete request tracing for troubleshooting

## Ready for Third-Party Integration

The current implementation provides the foundation for integrating with:

### APM Tools
- **Datadog**: Session context ready for custom metrics and traces
- **New Relic**: Structured logs compatible with New Relic insights
- **AppDynamics**: Session correlation for application performance monitoring

### Tracing Systems  
- **OpenTelemetry**: Session attributes ready for distributed tracing
- **Jaeger**: User journey tracking across service boundaries
- **Zipkin**: Function-level span correlation with session context

### Log Analytics
- **ELK Stack**: Structured logs ready for Elasticsearch indexing
- **Splunk**: Session-based log analysis and alerting
- **Fluentd**: Log forwarding with session enrichment

## Implementation Guide

### Step 1: Choose Your Observability Stack

Select one or more observability tools:
- **APM**: Datadog, New Relic, AppDynamics
- **Tracing**: OpenTelemetry, Jaeger, Zipkin
- **Logging**: ELK Stack, Splunk, Fluentd
- **Metrics**: Prometheus + Grafana, InfluxDB

### Step 2: Install Required Packages

```bash
# For OpenTelemetry
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger

# For Datadog
pip install datadog

# For New Relic
pip install newrelic

# For structured logging
pip install structlog
```

### Step 3: Create Instrumented Agent

Extend the `BankingDisputeAgent` class with your observability instrumentation (see `observability_example.py` for a complete example).

### Step 4: Configure Environment

Add necessary environment variables for your observability tools:

```bash
# Datadog
export DD_API_KEY="your-datadog-api-key"
export DD_SITE="datadoghq.com"

# New Relic
export NEW_RELIC_LICENSE_KEY="your-newrelic-license-key"
export NEW_RELIC_APP_NAME="banking-dispute-assistant-v1"

# OpenTelemetry
export OTEL_EXPORTER_JAEGER_ENDPOINT="http://localhost:14268/api/traces"
```

## Key Observability Metrics to Track

### Performance Metrics
- `dispute.processing.duration` - End-to-end processing time
- `dispute.lane.duration` - Individual lane processing times
- `dispute.openai.api.duration` - OpenAI API call latencies
- `dispute.confidence.score` - Agent confidence scores

### Business Metrics
- `dispute.status.{status}` - Count by dispute status (Filed, Denied, etc.)
- `dispute.category.{category}` - Count by dispute category
- `dispute.credit.issued` - Temporary credits issued
- `dispute.credit.amount` - Credit amounts by user/session

### Error Metrics
- `dispute.processing.errors` - Processing failures
- `dispute.lane.failures` - Individual lane failures
- `dispute.openai.api.errors` - OpenAI API errors

### User Journey Metrics
- `user.sessions.active` - Active user sessions
- `user.disputes.per_session` - Disputes per user session
- `user.department.{dept}` - Activity by department

## Alerting Examples

### High Error Rate Alert
```yaml
alert: High Dispute Processing Error Rate
condition: error_rate > 5% over 5 minutes
dimensions: [user_id, session_id, dispute_category]
notification: Slack, PagerDuty
```

### Low Confidence Score Alert
```yaml
alert: Low Agent Confidence Score
condition: avg(confidence_score) < 0.7 over 10 minutes
dimensions: [user_id, dispute_category]
notification: Email
```

### High Processing Time Alert
```yaml
alert: Slow Dispute Processing
condition: p95(processing_duration) > 30 seconds over 5 minutes
dimensions: [user_id, session_id]
notification: Slack
```

## Testing Your Current Implementation

You can verify the session tracking is working by:

1. **Running the Streamlit app:**
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Select a user** (e.g., "Sarah Johnson - Fraud Investigation")

3. **Submit a dispute** and watch the terminal logs

4. **Verify session consistency** - every log entry should show the same session_id

Expected log pattern:
```bash
# User session creation
USR002_20251004_115317_57ea012e

# All function calls with same session
[user_id=USR002, session_id=USR002_20251004_115317_57ea012e, function=get_customer_dispute_history]
[user_id=USR002, session_id=USR002_20251004_115317_57ea012e, function=assess_merchant_risk]
[user_id=USR002, session_id=USR002_20251004_115317_57ea012e, function=check_network_rules]
```

## Function Call Token Considerations

**Important Note**: OpenAI charges for function schemas as input tokens. With 12 functions in the registry, you're using approximately 800-1,200 tokens per request just for function definitions.

**Cost Impact**: ~$0.024-$0.036 per dispute (at GPT-4 pricing) before actual processing.

**Optimization Strategies**:
- Consider dynamic function loading based on dispute category
- Implement function schema caching
- Use shorter function descriptions where possible
- Monitor token usage via session tracking

## Backward Compatibility

The changes are fully backward compatible:
- `user_id` and `session_id` are optional fields
- Existing code will continue to work without modification
- New fields will be `None` if not provided

## Security Considerations

- Ensure user_id and session_id don't contain PII
- Consider data retention policies for observability data
- Implement proper access controls for observability dashboards
- Be mindful of data sovereignty requirements

## Next Steps

1. Choose your observability stack
2. Implement the instrumentation using the provided examples
3. Set up dashboards and alerts
4. Train your team on the new observability capabilities
5. Monitor and iterate on your observability strategy

The enhanced banking-dispute-assistant-v1 now provides comprehensive observability capabilities, enabling you to monitor, debug, and optimize your AI-powered dispute processing system with full user and session context.
# Observability Enhancement for Banking Dispute Agent

## Overview

This enhancement adds user and session context to the Banking Dispute Agent, enabling comprehensive observability instrumentation with third-party tools like Datadog, New Relic, OpenTelemetry, Splunk, and others.

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

## Observability Benefits

### Before Enhancement ❌
- No user/session correlation
- Limited traceability across system components
- Difficult to attribute costs and performance to specific users
- No way to track user journeys
- Limited debugging capabilities for user-specific issues

### After Enhancement ✅
- **User Journey Tracking**: Follow a user's actions across multiple sessions
- **Performance Monitoring**: Track response times and error rates by user/session
- **Cost Attribution**: Assign OpenAI API costs to specific users or departments
- **Error Correlation**: Debug issues with full user context
- **A/B Testing**: Track feature performance across user segments
- **Compliance**: Maintain audit trails with user identification
- **Real-time Alerting**: Set up alerts with user context for faster resolution

## Integration Examples

### 1. OpenTelemetry Tracing

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def process_dispute(self, dispute_request: DisputeRequest):
    with tracer.start_as_current_span("dispute_processing") as span:
        span.set_attributes({
            "user.id": dispute_request.user_id,
            "session.id": dispute_request.session_id,
            "customer.id": dispute_request.customer_id,
            "dispute.category": dispute_request.dispute_category.value,
            "transaction.amount": dispute_request.transaction_amount
        })
        
        # Process dispute...
        response = await super().process_dispute(dispute_request)
        
        span.set_attributes({
            "dispute.id": response.dispute_id,
            "dispute.status": response.status.value,
            "confidence.score": response.confidence_score
        })
        
        return response
```

### 2. Datadog Metrics

```python
from datadog import DogStatsdClient

statsd = DogStatsdClient()

def log_dispute_metrics(dispute_request, response, processing_time):
    tags = [
        f'user_id:{dispute_request.user_id}',
        f'session_id:{dispute_request.session_id}',
        f'category:{dispute_request.dispute_category.value}',
        f'status:{response.status.value}'
    ]
    
    statsd.increment('dispute.processing.completed', tags=tags)
    statsd.histogram('dispute.processing.duration', processing_time, tags=tags)
    statsd.gauge('dispute.confidence.score', response.confidence_score, tags=tags)
    
    if response.temporary_credit_issued:
        statsd.increment('dispute.credit.issued', tags=tags)
        statsd.histogram('dispute.credit.amount', response.temporary_credit_amount, tags=tags)
```

### 3. New Relic Custom Events

```python
import newrelic.agent

def log_dispute_event(dispute_request, response):
    newrelic.agent.record_custom_event('DisputeProcessed', {
        'user_id': dispute_request.user_id,
        'session_id': dispute_request.session_id,
        'customer_id': dispute_request.customer_id,
        'dispute_id': response.dispute_id,
        'dispute_category': dispute_request.dispute_category.value,
        'transaction_amount': dispute_request.transaction_amount,
        'status': response.status.value,
        'confidence_score': response.confidence_score,
        'temporary_credit_issued': response.temporary_credit_issued,
        'temporary_credit_amount': response.temporary_credit_amount
    })
```

### 4. Structured Logging for ELK Stack

```python
import structlog

logger = structlog.get_logger()

def log_dispute_processing(dispute_request, response, processing_time):
    logger.info(
        "dispute_processed",
        user_id=dispute_request.user_id,
        session_id=dispute_request.session_id,
        customer_id=dispute_request.customer_id,
        dispute_id=response.dispute_id,
        dispute_category=dispute_request.dispute_category.value,
        transaction_amount=dispute_request.transaction_amount,
        status=response.status.value,
        confidence_score=response.confidence_score,
        processing_time_seconds=processing_time,
        temporary_credit_issued=response.temporary_credit_issued,
        temporary_credit_amount=response.temporary_credit_amount
    )
```

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
export NEW_RELIC_APP_NAME="banking-dispute-agent"

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

## Testing Your Observability Setup

Run the included demo to verify your instrumentation:

```bash
python observability_example.py
```

This will simulate dispute processing and show the observability events that would be captured.

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

The enhanced Banking Dispute Agent now provides comprehensive observability capabilities, enabling you to monitor, debug, and optimize your AI-powered dispute processing system with full user and session context.
# External Services Integration Guide

This guide covers the implementation and deployment of all external service integrations for the Faithful Finances backend.

## 🚀 Services Implemented

### ✅ Redis Service
- **Connection pooling** with circuit breaker pattern
- **Caching service** with tenant isolation
- **Session management** with TTL and cleanup
- **Rate limiting** with multiple strategies (fixed window, sliding window, token bucket)
- **Health monitoring** and performance metrics

### ✅ Stripe Service  
- **Payment processing** with setup intents and payment methods
- **Subscription management** with plan changes and cancellations
- **Webhook handling** for all subscription and payment events
- **Billing portal** integration for customer self-service
- **Error handling** with automatic retries and circuit breakers

### ✅ Plaid Service
- **Account synchronization** with real-time balance updates
- **Transaction processing** with categorization
- **Institution management** and connection health monitoring
- **Webhook handling** for transaction updates and item errors
- **Rate limiting** to comply with Plaid API limits

### ✅ Background Tasks (Celery)
- **Async processing** for heavy operations
- **Task scheduling** with cron and interval support
- **Task monitoring** and cancellation
- **Worker management** with health checks
- **Queue separation** by priority and task type

## 📋 Prerequisites

### Required Services
1. **Redis Server** (v6.0+)
2. **Stripe Account** with API keys
3. **Plaid Account** with API credentials
4. **PostgreSQL** (already configured)

### Environment Variables
```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379

# Stripe Configuration  
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Plaid Configuration
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret_key
PLAID_ENV=sandbox  # or development/production
PLAID_PRODUCTS=transactions,accounts,identity
PLAID_COUNTRY_CODES=US

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 🛠️ Installation

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements-services.txt
```

### 2. Start Redis Server
```bash
# On Ubuntu/Debian
sudo systemctl start redis-server

# On macOS with Homebrew
brew services start redis

# Using Docker
docker run -d -p 6379:6379 --name redis redis:alpine
```

### 3. Start Celery Workers
```bash
# Start worker for background tasks
celery -A src.services.background.celery_app worker --loglevel=info --queues=high_priority,medium_priority,notifications,reports,maintenance

# Start beat scheduler for periodic tasks
celery -A src.services.background.celery_app beat --loglevel=info

# Monitor tasks (optional)
celery -A src.services.background.celery_app monitor
```

### 4. Configure Webhooks

#### Stripe Webhooks
1. Go to Stripe Dashboard → Webhooks
2. Add endpoint: `https://yourdomain.com/webhooks/stripe`
3. Select events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
4. Copy webhook secret to `STRIPE_WEBHOOK_SECRET`

#### Plaid Webhooks
1. Go to Plaid Dashboard → Webhooks
2. Add endpoint: `https://yourdomain.com/webhooks/plaid`
3. Select events:
   - `TRANSACTIONS` (all codes)
   - `ITEM` (all codes)

## 🏃‍♂️ Running the Application

### Development Mode
```bash
# Start the main application
python -m src.main

# In separate terminals:
# Start Celery worker
celery -A src.services.background.celery_app worker --loglevel=info

# Start Celery beat
celery -A src.services.background.celery_app beat --loglevel=info
```

### Production Mode
```bash
# Use supervisord or systemd to manage processes
# Example supervisord configuration provided below
```

## 🔧 Configuration Files

### supervisord.conf (Production)
```ini
[program:faithfulfinances_api]
command=/path/to/venv/bin/python -m src.main
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/faithfulfinances/api.log

[program:faithfulfinances_celery_worker]
command=/path/to/venv/bin/celery -A src.services.background.celery_app worker --loglevel=info
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/faithfulfinances/celery_worker.log

[program:faithfulfinances_celery_beat]
command=/path/to/venv/bin/celery -A src.services.background.celery_app beat --loglevel=info
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/faithfulfinances/celery_beat.log
```

## 📊 Health Monitoring

### Health Check Endpoints
- **Main API**: `GET /health/detailed`
- **Webhooks**: `GET /webhooks/health`

### Service-Specific Health Checks
```python
# Check Redis
from src.services.redis import get_redis_client
redis_client = await get_redis_client()
health = await redis_client.health_check()

# Check Stripe
from src.services.stripe import get_stripe_client
stripe_client = get_stripe_client()
health = await stripe_client.health_check()

# Check Plaid
from src.services.plaid import get_plaid_client
plaid_client = get_plaid_client()
health = await plaid_client.health_check()

# Check Celery
from src.services.background import TaskScheduler
scheduler = TaskScheduler()
health = await scheduler.health_check()
```

## 🔐 Security Considerations

### Redis Security
- Use Redis AUTH if exposed to network
- Configure firewall rules to restrict access
- Enable TLS for production deployments

### API Keys Management
- Store API keys in environment variables or secure key management
- Rotate keys regularly
- Use different keys for different environments

### Webhook Security
- Validate webhook signatures
- Use HTTPS endpoints only
- Implement rate limiting on webhook endpoints

## 📈 Performance Optimization

### Redis Optimization
- Configure appropriate `maxmemory` policy
- Use Redis Cluster for high availability
- Monitor connection pool usage

### Celery Optimization
- Use separate queues for different task types
- Configure appropriate worker concurrency
- Monitor task execution times and failures

### Rate Limiting
- Implement rate limiting for API endpoints
- Use Redis for distributed rate limiting
- Monitor rate limit violations

## 🚨 Error Handling & Monitoring

### Circuit Breakers
All external service clients implement circuit breaker patterns:
- **Redis**: Fails open (allows operation without cache)
- **Stripe**: Fails closed (returns error for payment operations)
- **Plaid**: Fails closed with retry logic

### Logging
Structured logging with correlation IDs:
```python
logger = structlog.get_logger(__name__)
logger.info("Operation completed", 
           tenant_id=tenant_id, 
           operation="sync_accounts",
           duration_ms=123)
```

### Monitoring Metrics
- Request/response times for all services
- Error rates and types
- Cache hit/miss ratios
- Task queue lengths and processing times
- Webhook delivery success rates

## 🔄 Common Operations

### Sync Account Data
```python
from src.services.background import TaskScheduler

scheduler = TaskScheduler()
task_id = await scheduler.schedule_account_sync(
    tenant_id="tenant_123",
    access_token="access_token_xyz",
    delay_seconds=0
)
```

### Process Subscription Changes
```python
from src.services.stripe import SubscriptionService

sub_service = SubscriptionService()
result = await sub_service.change_subscription_plan(
    tenant_id="tenant_123",
    subscription_id="sub_xyz",
    new_plan_type=PlanType.FAMILY
)
```

### Cache User Data
```python
from src.services.redis import CacheService

cache = CacheService()
await cache.set(
    tenant_id="tenant_123",
    key="user:profile",
    value=user_data,
    ttl=3600
)
```

## 🔧 Troubleshooting

### Common Issues

#### Redis Connection Issues
```bash
# Check Redis status
redis-cli ping

# Check connection from Python
python -c "import redis; r=redis.Redis(); print(r.ping())"
```

#### Celery Worker Issues
```bash
# Check worker status
celery -A src.services.background.celery_app inspect active

# Purge task queues
celery -A src.services.background.celery_app purge

# Restart workers
celery -A src.services.background.celery_app control shutdown
```

#### Webhook Issues
- Verify webhook URLs are accessible from external services
- Check webhook signature validation
- Monitor webhook delivery attempts in service dashboards

### Performance Issues
- Monitor Redis memory usage and connection pool
- Check Celery queue lengths and worker utilization
- Review external service rate limits and usage

## 📚 Additional Resources

- [Redis Documentation](https://redis.io/documentation)
- [Stripe API Reference](https://stripe.com/docs/api)
- [Plaid API Documentation](https://plaid.com/docs/api/)
- [Celery Documentation](https://docs.celeryproject.org/)

## 🤝 Support

For implementation-specific questions:
1. Check service health endpoints
2. Review application logs
3. Monitor external service dashboards
4. Use provided debugging utilities
# 🚀 Faithful Finances API - Setup Guide

This guide will walk you through setting up the Faithful Finances API from scratch, including all required vendor accounts and configurations.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Vendor Account Setup](#vendor-account-setup)
4. [Local Development Setup](#local-development-setup)
5. [Production Deployment](#production-deployment)
6. [Troubleshooting](#troubleshooting)

## 🔧 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** (recommended: use `pyenv` for version management)
- **uv** (Python package manager): `pip install uv`
- **Redis** (for caching and background tasks)
- **Git** (for version control)

### Install Python with pyenv (Recommended)

```bash
# Install pyenv
curl https://pyenv.run | bash

# Install Python 3.11
pyenv install 3.11.6
pyenv global 3.11.6
```

### Install Redis

**macOS (using Homebrew):**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

**Windows:**
Download from [Redis for Windows](https://github.com/microsoftarchive/redis/releases)

## ⚡ Quick Start

### 1. Clone and Setup Project

```bash
# Clone the repository
git clone <repository-url>
cd faithful-finances-backend

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Generate security keys
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(64))" >> .env
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))" >> .env
```

#### 🔐 Understanding Security Keys

The Faithful Finances API uses two critical security keys that must be properly configured:

**SECRET_KEY** - Application Security Operations
- **Primary Uses:**
  - JWT token signing and verification
  - Session cookie security
  - CSRF protection tokens
  - Password reset and email verification links
  - API rate limiting tokens
  - Internal cryptographic operations

- **Security Requirements:**
  - Minimum 64 characters for production
  - Must be cryptographically random (never use predictable values)
  - Should be rotated every 90 days in production
  - Never commit to version control or log in application

**ENCRYPTION_KEY** - Data Encryption at Rest
- **Primary Uses:**
  - Encrypting tenant API keys and access tokens
  - Protecting sensitive financial data (account numbers, routing numbers)
  - Securing user PII (personally identifiable information)
  - Encrypting Plaid and Stripe integration tokens
  - Protecting webhook secrets and external service credentials

- **Technical Implementation:**
  - Uses PBKDF2-HMAC-SHA256 key derivation (100,000 iterations)
  - Creates Fernet symmetric encryption keys
  - Includes authentication to prevent data tampering
  - Supports graceful key rotation with backward compatibility

- **Security Requirements:**
  - Minimum 32 characters (Fernet encryption requirement)
  - Must be cryptographically random
  - Should never be changed without proper data migration
  - Requires secure key management in production

**⚠️ Critical Security Notes:**
- These keys protect your users' financial data and personal information
- Loss of ENCRYPTION_KEY means permanent data loss for encrypted fields
- Compromise of either key requires immediate rotation and security audit
- Consider using managed key services (AWS KMS, Azure Key Vault) in production

### 3. Configure Required Services

You'll need to set up accounts with the following services. See [Vendor Account Setup](#vendor-account-setup) for detailed instructions.

**Required Services:**
- 🏢 **Auth0** (Authentication)
- 🏢 **Turso** (Database)
- 🏢 **Plaid** (Banking Integration)
- 🏢 **Stripe** (Payments)

**Optional Services:**
- 🏢 **Sentry** (Error Tracking)
- 🏢 **Gmail/SMTP** (Email)

## 🏢 Vendor Account Setup

### Auth0 (Authentication)

Auth0 provides JWT-based authentication for the API.

**Setup Steps:**

1. **Create Auth0 Account**
   - Go to [auth0.com](https://auth0.com) and create a free account
   - Choose a tenant domain (e.g., `faithful-finances.auth0.com`)

2. **Create Application**
   - In Auth0 Dashboard → Applications → Create Application
   - Choose "Machine to Machine API" type
   - Name: "Faithful Finances API"

3. **Create API**
   - In Auth0 Dashboard → APIs → Create API
   - Name: "Faithful Finances API"
   - Identifier: `https://api.faithfulfinances.com`
   - Signing Algorithm: RS256

4. **Get Credentials**
   ```bash
   # Add to your .env file:
   AUTH0_DOMAIN="your-tenant.auth0.com"
   AUTH0_AUDIENCE="https://api.faithfulfinances.com"
   AUTH0_CLIENT_ID="your-client-id"
   AUTH0_CLIENT_SECRET="your-client-secret"
   ```

5. **Configure Permissions (Optional)**
   - In your API → Permissions → Add permissions:
     - `read:users`
     - `write:users`
     - `admin:tenants`

### Turso (Database)

Turso provides SQLite-compatible databases with global replication.

**Setup Steps:**

1. **Create Turso Account**
   - Go to [turso.tech](https://turso.tech) and sign up
   - Install Turso CLI: `brew install tursodatabase/tap/turso`

2. **Create Global Database**
   ```bash
   # Login to Turso
   turso auth login
   
   # Create global tenant registry database
   turso db create faithful-finances-global
   
   # Get database URL
   turso db show faithful-finances-global
   
   # Create authentication token
   turso db tokens create faithful-finances-global
   ```

3. **Update Environment**
   ```bash
   # Add to your .env file:
   GLOBAL_DATABASE_URL="libsql://faithful-finances-global-[org].turso.io"
   GLOBAL_AUTH_TOKEN="your-database-token"
   ```

### Plaid (Banking Integration)

Plaid connects to bank accounts and provides financial data.

**Setup Steps:**

1. **Create Plaid Account**
   - Go to [plaid.com](https://plaid.com) and create a developer account
   - Complete the application process

2. **Get API Keys**
   - In Plaid Dashboard → Team Settings → API
   - Copy your `client_id` and `secret`

3. **Update Environment**
   ```bash
   # Add to your .env file:
   PLAID_CLIENT_ID="your-plaid-client-id"
   PLAID_SECRET="your-plaid-secret"
   PLAID_ENV="sandbox"  # Use sandbox for development
   ```

### Stripe (Payment Processing)

Stripe handles subscription payments and billing.

**Setup Steps:**

1. **Create Stripe Account**
   - Go to [stripe.com](https://stripe.com) and create an account
   - Complete business verification for live mode

2. **Get API Keys**
   - In Stripe Dashboard → Developers → API keys
   - Copy your Publishable key and Secret key
   - Use test keys for development (they start with `pk_test_` and `sk_test_`)

3. **Set Up Webhooks**
   - In Stripe Dashboard → Developers → Webhooks
   - Create endpoint: `https://your-api.com/webhooks/stripe`
   - Select events: `customer.subscription.created`, `customer.subscription.updated`, `invoice.payment_succeeded`, etc.
   - Copy the webhook signing secret

4. **Update Environment**
   ```bash
   # Add to your .env file:
   STRIPE_SECRET_KEY="sk_test_your-secret-key"
   STRIPE_PUBLISHABLE_KEY="pk_test_your-publishable-key"
   STRIPE_WEBHOOK_SECRET="whsec_your-webhook-secret"
   ```

### Optional: Sentry (Error Tracking)

**Setup Steps:**

1. **Create Sentry Account**
   - Go to [sentry.io](https://sentry.io) and create account
   - Create new project for Python/FastAPI

2. **Get DSN**
   - Copy the DSN from project settings

3. **Update Environment**
   ```bash
   # Add to your .env file:
   SENTRY_DSN="https://your-dsn@sentry.io/project-id"
   ```

### Optional: Gmail (Email)

**Setup Steps:**

1. **Enable 2FA on Gmail**
   - Go to [myaccount.google.com](https://myaccount.google.com)
   - Security → 2-Step Verification → Turn On

2. **Create App Password**
   - Security → App passwords → Generate
   - Choose "Mail" and your device
   - Copy the 16-character password

3. **Update Environment**
   ```bash
   # Add to your .env file:
   SMTP_USERNAME="your-email@gmail.com"
   SMTP_PASSWORD="your-16-character-app-password"
   ```

## 💻 Local Development Setup

### 1. Verify Redis is Running

```bash
# Test Redis connection
redis-cli ping
# Should return: PONG
```

### 2. Initialize Database

```bash
# Run database migrations
python -m alembic upgrade head

# Verify database connection
python -c "from src.config import settings; print('Database URL:', settings.GLOBAL_DATABASE_URL)"
```

### 3. Start Development Server

```bash
# Start the API server
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or use the development script
python src/main.py
```

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/health/detailed

# API documentation
open http://localhost:8000/docs
```

### 5. Run Tests

```bash
# Install test dependencies
uv pip install -r requirements-dev.txt

# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run specific test module
python -m pytest tests/test_security_validation.py -v
```

## 🚀 Production Deployment

### 1. Environment Configuration

```bash
# Copy production environment template
cp .env.example .env.production

# Update production settings
ENVIRONMENT="production"
DEBUG=false
ENFORCE_HTTPS=true
CORS_ALLOW_ORIGINS="https://app.faithfulfinances.com"
```

### 2. Security Checklist

- [ ] Generate new `SECRET_KEY` and `ENCRYPTION_KEY`
- [ ] Switch to production vendor credentials:
  - [ ] Auth0 production tenant
  - [ ] Plaid production environment
  - [ ] Stripe live keys
  - [ ] Production Turso databases
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall and security groups
- [ ] Set up monitoring and logging
- [ ] Disable API documentation endpoints

### 3. Database Migration

```bash
# Create production tenant databases as needed
# This is handled automatically by the application

# Run migrations on global database
python -m alembic upgrade head
```

### 4. Process Management

**Using systemd (Linux):**

Create `/etc/systemd/system/faithful-finances-api.service`:

```ini
[Unit]
Description=Faithful Finances API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/faithful-finances-backend
Environment=PATH=/path/to/faithful-finances-backend/.venv/bin
ExecStart=/path/to/faithful-finances-backend/.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable faithful-finances-api
sudo systemctl start faithful-finances-api
sudo systemctl status faithful-finances-api
```

**Using Docker (Alternative):**

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install uv && uv pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5. Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name api.faithfulfinances.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.faithfulfinances.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔧 Troubleshooting

### Common Issues

**1. Redis Connection Error**
```bash
# Check if Redis is running
redis-cli ping

# Start Redis
brew services start redis  # macOS
sudo systemctl start redis-server  # Linux
```

**2. Database Connection Error**
```bash
# Verify Turso credentials
turso db show faithful-finances-global

# Test database connection
python -c "from src.database import init_databases; import asyncio; asyncio.run(init_databases())"
```

**3. Auth0 JWT Validation Error**
```bash
# Verify Auth0 configuration
curl https://your-tenant.auth0.com/.well-known/jwks.json

# Check environment variables
python -c "from src.config import settings; print(settings.AUTH0_DOMAIN, settings.AUTH0_AUDIENCE)"
```

**4. Import Errors**
```bash
# Reinstall dependencies
uv pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

### Environment Validation

```bash
# Validate all environment variables
python -c "
from src.config import settings
warnings = settings.validate_security_configuration()
if warnings:
    print('⚠️  Configuration warnings:')
    for warning in warnings:
        print(f'   - {warning}')
else:
    print('✅ Configuration looks good!')
"
```

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health with all services
curl http://localhost:8000/health/detailed | jq '.'
```

### Performance Testing

```bash
# Install load testing tool
pip install httpx

# Simple load test
python -c "
import asyncio
import httpx
import time

async def test_load():
    async with httpx.AsyncClient() as client:
        start = time.time()
        tasks = [client.get('http://localhost:8000/health') for _ in range(100)]
        responses = await asyncio.gather(*tasks)
        end = time.time()
        
        success_count = sum(1 for r in responses if r.status_code == 200)
        print(f'Completed 100 requests in {end-start:.2f}s')
        print(f'Success rate: {success_count}/100')

asyncio.run(test_load())
"
```

## 📞 Support

If you encounter issues not covered in this guide:

1. Check the [SECURITY_AUDIT_REPORT.md](./SECURITY_AUDIT_REPORT.md) for security-related issues
2. Review the application logs for error details
3. Verify all environment variables are correctly set
4. Ensure all vendor services are properly configured

## 🔄 Updates and Maintenance

### Regular Maintenance Tasks

1. **Update Dependencies**
   ```bash
   uv pip install --upgrade -r requirements.txt
   ```

2. **Database Maintenance**
   ```bash
   # Run any new migrations
   python -m alembic upgrade head
   ```

3. **Security Updates**
   - Rotate `SECRET_KEY` and `ENCRYPTION_KEY` periodically
   - Update vendor API keys as needed
   - Review security audit report quarterly

4. **Monitoring**
   - Check application logs regularly
   - Monitor security events
   - Review performance metrics

This setup guide should get you up and running with the Faithful Finances API. For production deployments, ensure you follow all security best practices and have proper monitoring in place.
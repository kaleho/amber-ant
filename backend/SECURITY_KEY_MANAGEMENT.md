# 🔐 Security Key Management Guide

This document provides comprehensive information about managing the cryptographic keys used in the Faithful Finances API.

## 📋 Table of Contents

1. [Overview](#overview)
2. [SECRET_KEY Details](#secret_key-details)
3. [ENCRYPTION_KEY Details](#encryption_key-details)
4. [Key Generation](#key-generation)
5. [Key Rotation](#key-rotation)
6. [Production Key Management](#production-key-management)
7. [Security Best Practices](#security-best-practices)
8. [Incident Response](#incident-response)

## 🎯 Overview

The Faithful Finances API uses two primary cryptographic keys to secure user data and application operations:

- **SECRET_KEY**: Used for signing, verification, and general security operations
- **ENCRYPTION_KEY**: Used for encrypting sensitive data at rest

Both keys are critical for the security and operation of the application. Proper management of these keys is essential for maintaining the confidentiality, integrity, and availability of user data.

## 🔑 SECRET_KEY Details

### Purpose and Usage

The `SECRET_KEY` is used throughout the application for various security operations:

#### JWT Token Operations
```python
# JWT token signing (in auth service)
token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

# JWT token verification
payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
```

#### Session Management
```python
# Session cookie signing
session_data = signer.sign(user_data, key=settings.SECRET_KEY)

# CSRF token generation
csrf_token = generate_csrf_token(settings.SECRET_KEY, user_id)
```

#### Rate Limiting
```python
# Rate limit token generation
rate_limit_key = hashlib.hmac(
    settings.SECRET_KEY.encode(), 
    f"{client_ip}:{endpoint}".encode(), 
    hashlib.sha256
).hexdigest()
```

#### Password Reset and Email Verification
```python
# Secure token for password reset links
reset_token = generate_secure_token(
    user_id, 
    expires_at, 
    settings.SECRET_KEY
)
```

### Security Properties

- **Algorithm**: HMAC-SHA256 for most operations
- **Length**: Minimum 64 characters (512 bits) recommended
- **Entropy**: Must be cryptographically random
- **Rotation**: Every 90 days in production environments

### Impact of Compromise

If the `SECRET_KEY` is compromised:
- ❌ Attackers can forge JWT tokens for any user
- ❌ Session cookies can be forged
- ❌ CSRF protection is bypassed
- ❌ Password reset tokens can be forged
- ❌ Rate limiting can be bypassed

## 🔐 ENCRYPTION_KEY Details

### Purpose and Usage

The `ENCRYPTION_KEY` is used to encrypt sensitive data before storing it in the database:

#### Financial Data Encryption
```python
# Encrypting bank account numbers
encrypted_account = encrypt_token(account_number)  # Uses ENCRYPTION_KEY

# Encrypting routing numbers
encrypted_routing = encrypt_token(routing_number)  # Uses ENCRYPTION_KEY
```

#### API Token Storage
```python
# Encrypting Plaid access tokens
encrypted_plaid_token = encrypt_token(plaid_access_token)

# Encrypting Stripe customer IDs
encrypted_stripe_id = encrypt_token(stripe_customer_id)
```

#### Personal Information
```python
# Encrypting social security numbers (if collected)
encrypted_ssn = encrypt_token(ssn)

# Encrypting phone numbers
encrypted_phone = encrypt_token(phone_number)
```

### Technical Implementation

#### Key Derivation Process
```python
# PBKDF2 key derivation with salt
def derive_encryption_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 256 bits
        salt=salt,
        iterations=100000,  # 100,000 iterations
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))
```

#### Fernet Encryption
```python
# Creating Fernet cipher
def create_fernet_key() -> Fernet:
    derived_key = derive_encryption_key(
        settings.ENCRYPTION_KEY,
        b"faithful_finances_salt_v1"
    )
    return Fernet(derived_key)

# Encryption process
def encrypt_data(plaintext: str) -> str:
    fernet = create_fernet_key()
    encrypted = fernet.encrypt(plaintext.encode())
    return base64.urlsafe_b64encode(encrypted).decode()
```

### Security Properties

- **Algorithm**: AES-128 in CBC mode with HMAC-SHA256 authentication
- **Key Derivation**: PBKDF2-HMAC-SHA256 with 100,000 iterations
- **Length**: Minimum 32 characters (256 bits)
- **Authentication**: Built-in authentication prevents tampering
- **Rotation**: Yearly with graceful migration

### Impact of Compromise

If the `ENCRYPTION_KEY` is compromised:
- ❌ All encrypted financial data can be decrypted
- ❌ User PII becomes accessible
- ❌ API tokens and secrets are exposed
- ❌ Compliance violations (PCI DSS, SOX, etc.)

### Impact of Loss

If the `ENCRYPTION_KEY` is lost:
- ❌ All encrypted data becomes permanently inaccessible
- ❌ Users lose access to connected accounts
- ❌ Financial data cannot be retrieved
- ❌ System must be rebuilt from scratch

## 🔧 Key Generation

### For Development

```bash
# Generate SECRET_KEY (64 characters)
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(64))"

# Generate ENCRYPTION_KEY (32 characters minimum)
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))"

# Generate both keys with validation
python -c "
import secrets
secret_key = secrets.token_urlsafe(64)
encryption_key = secrets.token_urlsafe(32)

print(f'SECRET_KEY={secret_key}')
print(f'ENCRYPTION_KEY={encryption_key}')
print(f'SECRET_KEY length: {len(secret_key)} characters')
print(f'ENCRYPTION_KEY length: {len(encryption_key)} characters')
"
```

### For Production

#### Using Python Script
```python
#!/usr/bin/env python3
"""Generate production-grade cryptographic keys."""

import secrets
import base64
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def generate_production_keys():
    """Generate cryptographically secure keys for production."""
    
    # Generate SECRET_KEY (96 characters = 512 bits)
    secret_key = secrets.token_urlsafe(72)  # 72 * 8/6 = 96 chars
    
    # Generate ENCRYPTION_KEY (64 characters = 384 bits)
    encryption_key = secrets.token_urlsafe(48)  # 48 * 8/6 = 64 chars
    
    # Validate key strength
    assert len(secret_key) >= 64, "SECRET_KEY too short"
    assert len(encryption_key) >= 32, "ENCRYPTION_KEY too short"
    
    # Test key derivation
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000
    )
    derived_key = kdf.derive(encryption_key.encode())
    
    print("🔐 Production Keys Generated Successfully")
    print("=" * 50)
    print(f"SECRET_KEY={secret_key}")
    print(f"ENCRYPTION_KEY={encryption_key}")
    print("=" * 50)
    print(f"SECRET_KEY entropy: {len(secret_key) * 6} bits")
    print(f"ENCRYPTION_KEY entropy: {len(encryption_key) * 6} bits")
    print("Key derivation test: ✅ PASSED")
    print()
    print("⚠️  SECURITY REMINDERS:")
    print("1. Store these keys securely (never commit to version control)")
    print("2. Use environment-specific key management in production")
    print("3. Set up key rotation procedures")
    print("4. Have secure backup and recovery procedures")

if __name__ == "__main__":
    generate_production_keys()
```

#### Using OpenSSL
```bash
# Generate SECRET_KEY using OpenSSL
openssl rand -base64 64 | tr -d '\n'

# Generate ENCRYPTION_KEY using OpenSSL  
openssl rand -base64 32 | tr -d '\n'
```

## 🔄 Key Rotation

### SECRET_KEY Rotation

SECRET_KEY rotation is relatively straightforward as it doesn't affect stored data:

```python
# Step 1: Deploy new SECRET_KEY alongside old one
OLD_SECRET_KEY = "old-key-value"
NEW_SECRET_KEY = "new-key-value"

# Step 2: Accept tokens signed with either key
def verify_jwt_token(token: str) -> dict:
    try:
        # Try new key first
        return jwt.decode(token, NEW_SECRET_KEY, algorithms=["HS256"])
    except jwt.InvalidSignatureError:
        # Fallback to old key
        return jwt.decode(token, OLD_SECRET_KEY, algorithms=["HS256"])

# Step 3: Sign new tokens with new key only
def create_jwt_token(payload: dict) -> str:
    return jwt.encode(payload, NEW_SECRET_KEY, algorithm="HS256")

# Step 4: After grace period, remove old key support
```

### ENCRYPTION_KEY Rotation

ENCRYPTION_KEY rotation requires data migration:

```python
# Step 1: Prepare new encryption key
OLD_ENCRYPTION_KEY = "old-key-value"
NEW_ENCRYPTION_KEY = "new-key-value"

# Step 2: Create migration script
async def migrate_encrypted_data():
    """Migrate all encrypted data to new key."""
    
    # Get all records with encrypted data
    records = await get_all_encrypted_records()
    
    for record in records:
        # Decrypt with old key
        old_fernet = create_fernet_key(OLD_ENCRYPTION_KEY)
        decrypted_data = old_fernet.decrypt(record.encrypted_field)
        
        # Re-encrypt with new key
        new_fernet = create_fernet_key(NEW_ENCRYPTION_KEY)
        new_encrypted_data = new_fernet.encrypt(decrypted_data)
        
        # Update record
        record.encrypted_field = new_encrypted_data
        await record.save()
        
    print(f"Migrated {len(records)} encrypted records")

# Step 3: Deploy with both keys temporarily
def decrypt_token(encrypted_token: str) -> str:
    """Decrypt token with fallback to old key."""
    try:
        # Try new key first
        new_fernet = create_fernet_key(NEW_ENCRYPTION_KEY)
        return new_fernet.decrypt(encrypted_token).decode()
    except InvalidToken:
        # Fallback to old key
        old_fernet = create_fernet_key(OLD_ENCRYPTION_KEY)
        return old_fernet.decrypt(encrypted_token).decode()

# Step 4: Run migration during maintenance window
# Step 5: Remove old key after verification
```

### Rotation Schedule

| Key Type | Production Frequency | Staging Frequency | Development |
|----------|---------------------|-------------------|-------------|
| SECRET_KEY | Every 90 days | Every 180 days | As needed |
| ENCRYPTION_KEY | Yearly | Every 6 months | As needed |

## 🏢 Production Key Management

### Cloud Provider Solutions

#### AWS Key Management Service (KMS)
```python
import boto3

# Store keys in AWS Parameter Store
def store_keys_in_aws():
    ssm = boto3.client('ssm')
    
    # Store SECRET_KEY
    ssm.put_parameter(
        Name='/faithful-finances/prod/SECRET_KEY',
        Value=secret_key,
        Type='SecureString',
        KeyId='alias/faithful-finances-key',
        Overwrite=True
    )
    
    # Store ENCRYPTION_KEY  
    ssm.put_parameter(
        Name='/faithful-finances/prod/ENCRYPTION_KEY',
        Value=encryption_key,
        Type='SecureString',
        KeyId='alias/faithful-finances-key',
        Overwrite=True
    )

# Retrieve keys in application
def get_keys_from_aws():
    ssm = boto3.client('ssm')
    
    secret_key = ssm.get_parameter(
        Name='/faithful-finances/prod/SECRET_KEY',
        WithDecryption=True
    )['Parameter']['Value']
    
    encryption_key = ssm.get_parameter(
        Name='/faithful-finances/prod/ENCRYPTION_KEY',
        WithDecryption=True
    )['Parameter']['Value']
    
    return secret_key, encryption_key
```

#### Azure Key Vault
```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

# Store keys in Azure Key Vault
def store_keys_in_azure():
    credential = DefaultAzureCredential()
    client = SecretClient(
        vault_url="https://faithful-finances.vault.azure.net/",
        credential=credential
    )
    
    # Store keys
    client.set_secret("SECRET-KEY", secret_key)
    client.set_secret("ENCRYPTION-KEY", encryption_key)

# Retrieve keys
def get_keys_from_azure():
    credential = DefaultAzureCredential()
    client = SecretClient(
        vault_url="https://faithful-finances.vault.azure.net/",
        credential=credential
    )
    
    secret_key = client.get_secret("SECRET-KEY").value
    encryption_key = client.get_secret("ENCRYPTION-KEY").value
    
    return secret_key, encryption_key
```

#### Google Cloud Secret Manager
```python
from google.cloud import secretmanager

# Store keys in Google Cloud
def store_keys_in_gcp():
    client = secretmanager.SecretManagerServiceClient()
    project_id = "faithful-finances-prod"
    
    # Create and store SECRET_KEY
    parent = f"projects/{project_id}"
    secret_id = "SECRET_KEY"
    
    secret = client.create_secret(
        request={
            "parent": parent,
            "secret_id": secret_id,
            "secret": {"replication": {"automatic": {}}},
        }
    )
    
    # Add secret version
    client.add_secret_version(
        request={
            "parent": secret.name,
            "payload": {"data": secret_key.encode("UTF-8")},
        }
    )
```

### Hardware Security Modules (HSMs)

For high-security deployments, consider using HSMs:

```python
# Example with AWS CloudHSM
import boto3

def use_cloudhsm_for_keys():
    # CloudHSM client
    hsm_client = boto3.client('cloudhsmv2')
    
    # Generate keys directly in HSM
    # Keys never leave the secure hardware boundary
    response = hsm_client.generate_data_key(
        KeyId='alias/faithful-finances-master-key',
        KeySpec='AES_256'
    )
    
    return response['Plaintext'], response['CiphertextBlob']
```

## 🛡️ Security Best Practices

### Development Environment

1. **Use Generated Keys**: Never use default or example keys
2. **Local Storage**: Store in `.env` file (never commit to git)
3. **Team Sharing**: Use secure channels to share development keys
4. **Regular Updates**: Update keys when team members leave

### Staging Environment

1. **Separate Keys**: Use different keys from production
2. **Rotation Testing**: Test key rotation procedures
3. **Access Control**: Limit access to staging keys
4. **Monitoring**: Log key usage and access patterns

### Production Environment

1. **Key Management Service**: Use cloud provider key management
2. **Access Control**: Implement least-privilege access
3. **Audit Logging**: Log all key access and usage
4. **Backup Strategy**: Secure backup of key material
5. **Incident Response**: Procedures for key compromise
6. **Compliance**: Meet regulatory requirements (PCI DSS, SOX)

### Application Security

```python
# Secure key loading
def load_keys_securely():
    """Load keys with proper error handling and validation."""
    
    try:
        secret_key = os.environ.get('SECRET_KEY')
        encryption_key = os.environ.get('ENCRYPTION_KEY')
        
        # Validate keys exist
        if not secret_key or not encryption_key:
            raise ValueError("Missing required security keys")
        
        # Validate key strength
        if len(secret_key) < 64:
            raise ValueError("SECRET_KEY too short (minimum 64 characters)")
        
        if len(encryption_key) < 32:
            raise ValueError("ENCRYPTION_KEY too short (minimum 32 characters)")
        
        # Test key derivation
        test_encrypt_decrypt(encryption_key)
        
        return secret_key, encryption_key
        
    except Exception as e:
        logger.critical(f"Failed to load security keys: {e}")
        raise SystemExit("Security key validation failed")

def test_encrypt_decrypt(encryption_key: str):
    """Test encryption/decryption functionality."""
    from src.shared.utils import encrypt_token, decrypt_token
    
    test_data = "test-encryption-data"
    encrypted = encrypt_token(test_data)
    decrypted = decrypt_token(encrypted)
    
    if decrypted != test_data:
        raise ValueError("Encryption key validation failed")
```

### Monitoring and Alerting

```python
# Key usage monitoring
def monitor_key_usage():
    """Monitor and alert on key usage patterns."""
    
    # Log key operations
    logger.info("Encryption key used for token encryption", extra={
        'operation': 'encrypt',
        'key_id': hashlib.sha256(encryption_key.encode()).hexdigest()[:8],
        'timestamp': datetime.utcnow().isoformat()
    })
    
    # Alert on suspicious patterns
    if detect_unusual_key_usage():
        send_security_alert("Unusual key usage pattern detected")

def detect_key_compromise():
    """Detect potential key compromise."""
    
    indicators = [
        unusual_token_creation_patterns(),
        invalid_signature_spike(),
        decryption_failure_spike(),
        access_from_unknown_locations()
    ]
    
    if any(indicators):
        trigger_key_rotation_procedure()
```

## 🚨 Incident Response

### Key Compromise Response

If you suspect key compromise:

1. **Immediate Actions** (within 1 hour):
   ```bash
   # Rotate keys immediately
   ./scripts/emergency-key-rotation.sh
   
   # Revoke all active sessions
   ./scripts/revoke-all-sessions.sh
   
   # Alert security team
   ./scripts/send-security-alert.sh "KEY_COMPROMISE"
   ```

2. **Short-term Actions** (within 24 hours):
   - Audit logs for unauthorized access
   - Identify scope of compromise
   - Notify affected users
   - Document incident details

3. **Long-term Actions** (within 1 week):
   - Conduct security audit
   - Update security procedures
   - Implement additional monitoring
   - Regulatory reporting if required

### Key Loss Response

If encryption keys are lost:

1. **Assessment**:
   - Determine which data is affected
   - Check for available backups
   - Assess business impact

2. **Recovery Options**:
   - Restore from secure key backup
   - Regenerate keys and migrate data
   - Request users to re-authenticate

3. **Prevention**:
   - Implement key escrow procedures
   - Multiple secure backup locations
   - Regular backup testing

### Emergency Key Rotation Script

```bash
#!/bin/bash
# emergency-key-rotation.sh

set -e

echo "🚨 EMERGENCY KEY ROTATION INITIATED"
echo "Timestamp: $(date -u)"

# Generate new keys
NEW_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(72))")
NEW_ENCRYPTION_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(48))")

# Update production environment
kubectl set env deployment/faithful-finances-api \
  SECRET_KEY="$NEW_SECRET_KEY" \
  ENCRYPTION_KEY="$NEW_ENCRYPTION_KEY"

# Wait for deployment
kubectl rollout status deployment/faithful-finances-api

# Verify health
curl -f https://api.faithfulfinances.com/health || exit 1

echo "✅ Emergency key rotation completed"
echo "📧 Sending notifications..."

# Send alerts
./scripts/send-security-alert.sh "Emergency key rotation completed successfully"
```

## 📊 Compliance Considerations

### PCI DSS Requirements

- Store keys in secure key management systems
- Implement key rotation procedures
- Audit key access and usage
- Separate key management duties

### SOX Compliance

- Document key management procedures
- Implement change control processes
- Regular security assessments
- Incident response procedures

### GDPR Considerations

- Right to erasure (encryption key deletion)
- Data protection by design
- Security breach notifications
- Data processing records

## 🔍 Auditing and Monitoring

### Key Usage Metrics

```python
# Track key operations
KEY_USAGE_METRICS = {
    'secret_key_operations': Counter(),
    'encryption_operations': Counter(),
    'decryption_operations': Counter(),
    'key_rotation_events': Counter(),
    'key_validation_failures': Counter()
}

def track_key_operation(operation: str):
    """Track key usage for monitoring."""
    KEY_USAGE_METRICS[f'{operation}_operations'].inc()
    
    # Log for audit trail
    logger.info(f"Key operation: {operation}", extra={
        'operation': operation,
        'timestamp': datetime.utcnow().isoformat(),
        'user_agent': request.headers.get('User-Agent'),
        'client_ip': get_client_ip(request)
    })
```

### Security Dashboards

Monitor key security metrics:
- Key rotation status
- Failed decryption attempts
- Unusual access patterns
- Key age and compliance status

This comprehensive guide ensures proper management of the cryptographic keys that protect user data in the Faithful Finances API. Regular review and updates of these procedures are essential for maintaining security.
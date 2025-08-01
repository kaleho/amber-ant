"""Secure encryption key management."""
import os
import base64
import hashlib
from typing import Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import structlog

logger = structlog.get_logger(__name__)


class KeyManager:
    """Secure key derivation and management."""
    
    def __init__(self):
        self._derived_keys = {}
    
    def derive_encryption_key(
        self, 
        password: str, 
        salt: Optional[bytes] = None,
        iterations: int = 100000
    ) -> bytes:
        """
        Derive encryption key using PBKDF2-HMAC-SHA256.
        
        Args:
            password: Master password/key material
            salt: Salt bytes (generated if None)
            iterations: Number of PBKDF2 iterations
            
        Returns:
            Base64-encoded encryption key suitable for Fernet
        """
        if salt is None:
            salt = os.urandom(16)
            logger.info("Generated new salt for key derivation")
        
        # Use PBKDF2 with SHA-256
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 32 bytes for Fernet
            salt=salt,
            iterations=iterations,
        )
        
        key_material = kdf.derive(password.encode('utf-8'))
        derived_key = base64.urlsafe_b64encode(key_material)
        
        logger.debug("Successfully derived encryption key", salt_length=len(salt))
        return derived_key
    
    def create_fernet_cipher(self, key: bytes) -> Fernet:
        """Create Fernet cipher from derived key."""
        try:
            return Fernet(key)
        except Exception as e:
            logger.error("Failed to create Fernet cipher", error=str(e))
            raise ValueError(f"Invalid encryption key: {e}")
    
    def generate_secure_key(self) -> str:
        """Generate a cryptographically secure key."""
        return base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
    
    def hash_secret(self, secret: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Hash a secret with salt for secure storage.
        
        Returns:
            Tuple of (hash_hex, salt_hex)
        """
        if salt is None:
            salt_bytes = os.urandom(32)
            salt = salt_bytes.hex()
        else:
            salt_bytes = bytes.fromhex(salt)
        
        # Use SHA-256 with salt
        hash_obj = hashlib.sha256()
        hash_obj.update(salt_bytes)
        hash_obj.update(secret.encode('utf-8'))
        
        return hash_obj.hexdigest(), salt
    
    def verify_secret(self, secret: str, stored_hash: str, salt: str) -> bool:
        """Verify a secret against stored hash and salt."""
        computed_hash, _ = self.hash_secret(secret, salt)
        return computed_hash == stored_hash
    
    def rotate_key(self, old_key: bytes, new_password: str) -> bytes:
        """Rotate encryption key with data re-encryption support."""
        # Generate new key
        new_salt = os.urandom(16)
        new_key = self.derive_encryption_key(new_password, new_salt)
        
        logger.info("Key rotation initiated", 
                   old_key_id=hashlib.sha256(old_key).hexdigest()[:8],
                   new_key_id=hashlib.sha256(new_key).hexdigest()[:8])
        
        return new_key


# Global key manager instance
key_manager = KeyManager()
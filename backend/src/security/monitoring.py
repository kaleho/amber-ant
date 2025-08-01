"""Security event monitoring and logging."""
import structlog
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
import json

logger = structlog.get_logger("security")


class SecurityEventType(Enum):
    """Types of security events to monitor."""
    
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "token_invalid"
    
    # Authorization events
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PERMISSION_DENIED = "permission_denied"
    TENANT_ACCESS_DENIED = "tenant_access_denied"
    ROLE_ESCALATION_ATTEMPT = "role_escalation_attempt"
    
    # Suspicious activity
    MULTIPLE_FAILED_LOGINS = "multiple_failed_logins"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNUSUAL_ACCESS_PATTERN = "unusual_access_pattern"
    SUSPICIOUS_USER_AGENT = "suspicious_user_agent"
    
    # Data access
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"
    BULK_DATA_EXPORT = "bulk_data_export"
    DATA_MODIFICATION = "data_modification"
    
    # System events
    ADMIN_ACTION = "admin_action"
    CONFIGURATION_CHANGE = "configuration_change"
    API_KEY_USAGE = "api_key_usage"
    WEBHOOK_FAILURE = "webhook_failure"


class RiskLevel(Enum):
    """Risk levels for security events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event data structure."""
    event_type: SecurityEventType
    risk_level: RiskLevel
    timestamp: datetime
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['risk_level'] = self.risk_level.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


class SecurityMonitor:
    """Security event monitoring and alerting."""
    
    def __init__(self):
        self.event_counts = {}
        
    async def log_security_event(
        self,
        event_type: SecurityEventType,
        risk_level: RiskLevel = RiskLevel.LOW,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """Log a security event with structured data."""
        
        event = SecurityEvent(
            event_type=event_type,
            risk_level=risk_level,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            method=method,
            details=details or {},
            session_id=session_id,
            request_id=request_id
        )
        
        # Log the event
        logger.info(
            "Security event detected",
            **event.to_dict()
        )
        
        # Check for patterns that require immediate attention
        await self._analyze_event_patterns(event)
        
        # Send alerts for high-risk events
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            await self._send_security_alert(event)
    
    async def _analyze_event_patterns(self, event: SecurityEvent):
        """Analyze events for suspicious patterns."""
        event_key = f"{event.event_type.value}:{event.user_id}:{event.ip_address}"
        
        # Track event frequency
        if event_key not in self.event_counts:
            self.event_counts[event_key] = []
        
        self.event_counts[event_key].append(event.timestamp)
        
        # Remove events older than 1 hour
        cutoff = datetime.utcnow().timestamp() - 3600
        self.event_counts[event_key] = [
            ts for ts in self.event_counts[event_key]
            if ts.timestamp() > cutoff
        ]
        
        # Check for suspicious patterns
        if event.event_type == SecurityEventType.LOGIN_FAILURE:
            if len(self.event_counts[event_key]) >= 5:  # 5 failures in 1 hour
                await self.log_security_event(
                    SecurityEventType.MULTIPLE_FAILED_LOGINS,
                    RiskLevel.HIGH,
                    user_id=event.user_id,
                    ip_address=event.ip_address,
                    details={
                        "failure_count": len(self.event_counts[event_key]),
                        "time_window": "1_hour"
                    }
                )
    
    async def _send_security_alert(self, event: SecurityEvent):
        """Send security alert for high-risk events."""
        alert_data = {
            "alert_type": "security_event",
            "severity": event.risk_level.value,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "user_id": event.user_id,
            "tenant_id": event.tenant_id,
            "ip_address": event.ip_address,
            "details": event.details
        }
        
        # Log as critical alert
        logger.critical(
            "SECURITY ALERT",
            **alert_data
        )
        
        # TODO: Integrate with alerting system (PagerDuty, Slack, etc.)
        # await send_to_alerting_system(alert_data)
    
    async def log_authentication_event(
        self,
        success: bool,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log authentication event."""
        event_type = SecurityEventType.LOGIN_SUCCESS if success else SecurityEventType.LOGIN_FAILURE
        risk_level = RiskLevel.LOW if success else RiskLevel.MEDIUM
        
        await self.log_security_event(
            event_type=event_type,
            risk_level=risk_level,
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )
    
    async def log_authorization_event(
        self,
        success: bool,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        required_permission: Optional[str] = None,
        endpoint: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log authorization event."""
        if success:
            return  # Don't log successful authorization events
        
        event_type = SecurityEventType.PERMISSION_DENIED
        risk_level = RiskLevel.MEDIUM
        
        event_details = details or {}
        if required_permission:
            event_details["required_permission"] = required_permission
        
        await self.log_security_event(
            event_type=event_type,
            risk_level=risk_level,
            user_id=user_id,
            tenant_id=tenant_id,
            endpoint=endpoint,
            ip_address=ip_address,
            details=event_details
        )
    
    async def log_data_access_event(
        self,
        user_id: str,
        tenant_id: str,
        data_type: str,
        operation: str,
        record_count: int = 1,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log sensitive data access event."""
        risk_level = RiskLevel.LOW
        
        # Escalate risk for bulk operations
        if record_count > 100:
            risk_level = RiskLevel.MEDIUM
        if record_count > 1000:
            risk_level = RiskLevel.HIGH
        
        event_details = details or {}
        event_details.update({
            "data_type": data_type,
            "operation": operation,
            "record_count": record_count
        })
        
        await self.log_security_event(
            event_type=SecurityEventType.SENSITIVE_DATA_ACCESS,
            risk_level=risk_level,
            user_id=user_id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            details=event_details
        )


# Global security monitor instance
security_monitor = SecurityMonitor()


# Convenience functions
async def log_auth_success(user_id: str, tenant_id: str, ip_address: str = None, **kwargs):
    """Log successful authentication."""
    await security_monitor.log_authentication_event(
        success=True,
        user_id=user_id,
        tenant_id=tenant_id,
        ip_address=ip_address,
        **kwargs
    )


async def log_auth_failure(user_id: str = None, ip_address: str = None, **kwargs):
    """Log failed authentication."""
    await security_monitor.log_authentication_event(
        success=False,
        user_id=user_id,
        ip_address=ip_address,
        **kwargs
    )


async def log_permission_denied(user_id: str, tenant_id: str, permission: str, **kwargs):
    """Log permission denied event."""
    await security_monitor.log_authorization_event(
        success=False,
        user_id=user_id,
        tenant_id=tenant_id,
        required_permission=permission,
        **kwargs
    )
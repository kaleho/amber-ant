"""Email service client with multiple provider support."""

import asyncio
import smtplib
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
import aiosmtplib
import structlog

from src.config import settings
from src.exceptions import EmailError

logger = structlog.get_logger(__name__)


class EmailProvider(ABC):
    """Abstract base class for email providers."""
    
    @abstractmethod
    async def send_email(
        self,
        to: List[str],
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Send an email."""
        pass


class SMTPEmailProvider(EmailProvider):
    """SMTP email provider for standard email sending."""
    
    def __init__(self, 
                 smtp_host: str,
                 smtp_port: int,
                 smtp_username: str,
                 smtp_password: str,
                 use_tls: bool = True,
                 use_ssl: bool = False):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.use_tls = use_tls
        self.use_ssl = use_ssl
    
    async def send_email(
        self,
        to: List[str],
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Send email via SMTP."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{from_name} <{from_email}>" if from_name else from_email or self.smtp_username
            msg['To'] = ', '.join(to)
            
            if reply_to:
                msg['Reply-To'] = reply_to
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML content
            if html_content:
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Send email
            if self.use_ssl:
                smtp_class = aiosmtplib.SMTP_SSL
            else:
                smtp_class = aiosmtplib.SMTP
            
            async with smtp_class(
                hostname=self.smtp_host,
                port=self.smtp_port,
                use_tls=self.use_tls and not self.use_ssl
            ) as server:
                if self.smtp_username and self.smtp_password:
                    await server.login(self.smtp_username, self.smtp_password)
                
                await server.send_message(msg)
            
            logger.info("Email sent successfully",
                       to=to,
                       subject=subject,
                       provider="smtp")
            
            return True
            
        except Exception as e:
            logger.error("SMTP email sending failed",
                        to=to,
                        subject=subject,
                        error=str(e))
            return False
    
    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """Add attachment to email message."""
        try:
            if 'content' in attachment:
                # Content provided directly
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment['content'])
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={attachment.get("filename", "attachment")}'
                )
                msg.attach(part)
            
            elif 'filepath' in attachment:
                # File path provided
                filepath = Path(attachment['filepath'])
                if filepath.exists():
                    with open(filepath, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename={filepath.name}'
                        )
                        msg.attach(part)
                        
        except Exception as e:
            logger.warning("Failed to add attachment", 
                          attachment=attachment, 
                          error=str(e))


class ConsoleEmailProvider(EmailProvider):
    """Console email provider for development/testing."""
    
    async def send_email(
        self,
        to: List[str],
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Print email to console."""
        print("\n" + "="*80)
        print("📧 EMAIL MESSAGE")
        print("="*80)
        print(f"From: {from_name} <{from_email}>" if from_name else from_email)
        print(f"To: {', '.join(to)}")
        print(f"Subject: {subject}")
        if reply_to:
            print(f"Reply-To: {reply_to}")
        print("-"*80)
        
        if text_content:
            print("TEXT CONTENT:")
            print(text_content)
            print("-"*80)
        
        if html_content:
            print("HTML CONTENT:")
            print(html_content)
            print("-"*80)
        
        if attachments:
            print(f"ATTACHMENTS: {len(attachments)} file(s)")
            for i, attachment in enumerate(attachments, 1):
                filename = attachment.get('filename', f'attachment_{i}')
                print(f"  {i}. {filename}")
            print("-"*80)
        
        print("✅ Email logged to console")
        print("="*80 + "\n")
        
        return True


class EmailService:
    """Email service with template support and provider abstraction."""
    
    def __init__(self, provider: Optional[EmailProvider] = None):
        self.provider = provider or self._create_default_provider()
        self.default_from_email = settings.EMAIL_FROM_ADDRESS
        self.default_from_name = settings.EMAIL_FROM_NAME
    
    def _create_default_provider(self) -> EmailProvider:
        """Create default email provider based on settings."""
        if settings.ENVIRONMENT == "development":
            return ConsoleEmailProvider()
        
        # Production SMTP configuration
        return SMTPEmailProvider(
            smtp_host=settings.SMTP_HOST,
            smtp_port=settings.SMTP_PORT,
            smtp_username=settings.SMTP_USERNAME,
            smtp_password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_USE_TLS,
            use_ssl=settings.SMTP_USE_SSL
        )
    
    async def send_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Send email using configured provider."""
        try:
            # Normalize recipient list
            if isinstance(to, str):
                to = [to]
            
            # Use defaults if not provided
            from_email = from_email or self.default_from_email
            from_name = from_name or self.default_from_name
            
            # Validate required fields
            if not to:
                raise EmailError("No recipients provided")
            if not subject:
                raise EmailError("No subject provided")
            if not html_content and not text_content:
                raise EmailError("No content provided")
            
            # Send email
            success = await self.provider.send_email(
                to=to,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                from_email=from_email,
                from_name=from_name,
                reply_to=reply_to,
                attachments=attachments
            )
            
            if success:
                logger.info("Email sent successfully",
                           to=to,
                           subject=subject)
            else:
                logger.error("Email sending failed",
                           to=to,
                           subject=subject)
            
            return success
            
        except Exception as e:
            logger.error("Email service error",
                        to=to,
                        subject=subject,
                        error=str(e))
            raise EmailError(f"Failed to send email: {str(e)}")
    
    async def send_template_email(
        self,
        to: Union[str, List[str]],
        template_name: str,
        template_data: Dict[str, Any],
        subject: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> bool:
        """Send email using template."""
        try:
            # Load and render template
            html_content, text_content, template_subject = await self._render_template(
                template_name, 
                template_data
            )
            
            # Use template subject if not provided
            final_subject = subject or template_subject or f"Notification from {self.default_from_name}"
            
            return await self.send_email(
                to=to,
                subject=final_subject,
                html_content=html_content,
                text_content=text_content,
                from_email=from_email,
                from_name=from_name,
                reply_to=reply_to
            )
            
        except Exception as e:
            logger.error("Template email sending failed",
                        template_name=template_name,
                        to=to,
                        error=str(e))
            raise EmailError(f"Failed to send template email: {str(e)}")
    
    async def _render_template(
        self, 
        template_name: str, 
        template_data: Dict[str, Any]
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Render email template."""
        try:
            # For now, use simple string formatting
            # In production, you'd use Jinja2 or similar
            templates = {
                "welcome": {
                    "subject": "Welcome to {app_name}!",
                    "html": """
                    <h1>Welcome to {app_name}!</h1>
                    <p>Hi {user_name},</p>
                    <p>Welcome to your new account! We're excited to have you on board.</p>
                    <p>You can start by connecting your bank accounts to track your finances.</p>
                    <p>Best regards,<br>The {app_name} Team</p>
                    """,
                    "text": """
                    Welcome to {app_name}!
                    
                    Hi {user_name},
                    
                    Welcome to your new account! We're excited to have you on board.
                    
                    You can start by connecting your bank accounts to track your finances.
                    
                    Best regards,
                    The {app_name} Team
                    """
                },
                "password_reset": {
                    "subject": "Reset your password",
                    "html": """
                    <h1>Reset Your Password</h1>
                    <p>Hi {user_name},</p>
                    <p>You requested to reset your password. Click the link below to reset it:</p>
                    <p><a href="{reset_link}">Reset Password</a></p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you didn't request this, please ignore this email.</p>
                    """,
                    "text": """
                    Reset Your Password
                    
                    Hi {user_name},
                    
                    You requested to reset your password. Use this link to reset it:
                    {reset_link}
                    
                    This link will expire in 24 hours.
                    
                    If you didn't request this, please ignore this email.
                    """
                },
                "payment_success": {
                    "subject": "Payment Confirmation",
                    "html": """
                    <h1>Payment Confirmed</h1>
                    <p>Hi {user_name},</p>
                    <p>Your payment has been successfully processed.</p>
                    <p><strong>Amount:</strong> {currency} {amount}</p>
                    <p><strong>Invoice ID:</strong> {invoice_id}</p>
                    <p>Thank you for your payment!</p>
                    """,
                    "text": """
                    Payment Confirmed
                    
                    Hi {user_name},
                    
                    Your payment has been successfully processed.
                    
                    Amount: {currency} {amount}
                    Invoice ID: {invoice_id}
                    
                    Thank you for your payment!
                    """
                }
            }
            
            template = templates.get(template_name)
            if not template:
                raise EmailError(f"Template '{template_name}' not found")
            
            # Format templates with data
            html_content = template.get("html", "").format(**template_data)
            text_content = template.get("text", "").format(**template_data)
            subject = template.get("subject", "").format(**template_data)
            
            return html_content, text_content, subject
            
        except KeyError as e:
            raise EmailError(f"Missing template variable: {e}")
        except Exception as e:
            raise EmailError(f"Template rendering failed: {str(e)}")


# Global email service instance
_email_service: Optional[EmailService] = None


async def get_email_service() -> EmailService:
    """Get or create email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


# Convenience functions
async def send_email(
    to: Union[str, List[str]],
    subject: str,
    html_content: Optional[str] = None,
    text_content: Optional[str] = None,
    **kwargs
) -> bool:
    """Send email using default service."""
    service = await get_email_service()
    return await service.send_email(
        to=to,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
        **kwargs
    )


async def send_template_email(
    to: Union[str, List[str]],
    template_name: str,
    template_data: Dict[str, Any],
    **kwargs
) -> bool:
    """Send template email using default service."""
    service = await get_email_service()
    return await service.send_template_email(
        to=to,
        template_name=template_name,
        template_data=template_data,
        **kwargs
    )
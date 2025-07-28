"""
Email Notification Service for HealthMate Application

This module provides:
- Email sending via multiple providers (SendGrid, SMTP, AWS SES)
- HTML email template rendering
- Email delivery tracking and bounce handling
- Email queue processing
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import json
from pathlib import Path

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent, TextContent
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

from jinja2 import Environment, FileSystemLoader, Template
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.notification_models import (
    Notification, NotificationTemplate, NotificationDeliveryAttempt,
    NotificationStatus, NotificationChannel, NotificationBounce
)
from app.exceptions.notification_exceptions import EmailError
from app.utils.audit_logging import AuditLogger

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications."""
    
    def __init__(self, settings: Settings):
        """Initialize the email service."""
        self.settings = settings
        self.audit_logger = AuditLogger()
        
        # Setup template environment
        self.template_env = self._setup_template_environment()
        
        # Initialize provider
        self.provider = self._initialize_provider()
        
        logger.info(f"Email service initialized with provider: {settings.email_provider}")
    
    def _setup_template_environment(self) -> Environment:
        """Setup Jinja2 template environment."""
        template_dir = Path(__file__).parent.parent / "templates" / "email"
        if not template_dir.exists():
            template_dir.mkdir(parents=True, exist_ok=True)
        
        return Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def _initialize_provider(self):
        """Initialize the email provider based on configuration."""
        provider = self.settings.email_provider.lower()
        
        if provider == "sendgrid":
            if not SENDGRID_AVAILABLE:
                raise EmailError("SendGrid not available. Install with: pip install sendgrid")
            if not self.settings.sendgrid_api_key:
                raise EmailError("SendGrid API key not configured")
            return "sendgrid"
        
        elif provider == "smtp":
            if not all([self.settings.smtp_host, self.settings.smtp_username, self.settings.smtp_password]):
                raise EmailError("SMTP configuration incomplete")
            return "smtp"
        
        elif provider == "aws_ses":
            if not AWS_AVAILABLE:
                raise EmailError("AWS SDK not available. Install with: pip install boto3")
            return "aws_ses"
        
        else:
            raise EmailError(f"Unsupported email provider: {provider}")
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send an email using the configured provider.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (optional)
            from_email: Sender email address (optional)
            from_name: Sender name (optional)
            reply_to: Reply-to email address (optional)
            attachments: List of attachment dictionaries
            metadata: Additional metadata for tracking
            
        Returns:
            Dictionary with delivery status and message ID
        """
        try:
            # Use default sender if not specified
            from_email = from_email or self.settings.email_from_address
            from_name = from_name or self.settings.email_from_name
            
            # Generate text content from HTML if not provided
            if not text_content:
                text_content = self._html_to_text(html_content)
            
            # Send email based on provider
            if self.provider == "sendgrid":
                result = await self._send_via_sendgrid(
                    to_email, subject, html_content, text_content,
                    from_email, from_name, reply_to, attachments
                )
            elif self.provider == "smtp":
                result = await self._send_via_smtp(
                    to_email, subject, html_content, text_content,
                    from_email, from_name, reply_to, attachments
                )
            elif self.provider == "aws_ses":
                result = await self._send_via_aws_ses(
                    to_email, subject, html_content, text_content,
                    from_email, from_name, reply_to, attachments
                )
            else:
                raise EmailError(f"Unsupported provider: {self.provider}")
            
            # Log successful email
            self.audit_logger.log_system_action(
                action="email_sent",
                details={
                    "to_email": to_email,
                    "subject": subject,
                    "provider": self.provider,
                    "message_id": result.get("message_id"),
                    "metadata": metadata
                }
            )
            
            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            
            # Log failed email
            self.audit_logger.log_system_action(
                action="email_failed",
                details={
                    "to_email": to_email,
                    "subject": subject,
                    "provider": self.provider,
                    "error": str(e),
                    "metadata": metadata
                }
            )
            
            raise EmailError(f"Failed to send email: {e}", recipient=to_email, subject=subject)
    
    async def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        from_email: str,
        from_name: str,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send email via SendGrid."""
        try:
            message = Mail(
                from_email=Email(from_email, from_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=HtmlContent(html_content),
                text_content=TextContent(text_content)
            )
            
            if reply_to:
                message.reply_to = Email(reply_to)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    message.add_attachment(attachment)
            
            sg = SendGridAPIClient(api_key=self.settings.sendgrid_api_key)
            response = sg.send(message)
            
            return {
                "success": True,
                "message_id": response.headers.get("X-Message-Id"),
                "status_code": response.status_code,
                "provider": "sendgrid"
            }
            
        except Exception as e:
            raise EmailError(f"SendGrid error: {e}", recipient=to_email, subject=subject)
    
    async def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        from_email: str,
        from_name: str,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send email via SMTP."""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{from_email}>"
            msg["To"] = to_email
            
            if reply_to:
                msg["Reply-To"] = reply_to
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment["content"])
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename= {attachment['filename']}"
                    )
                    msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
                if self.settings.smtp_use_tls:
                    server.starttls()
                elif self.settings.smtp_use_ssl:
                    server = smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port)
                
                server.login(self.settings.smtp_username, self.settings.smtp_password)
                server.send_message(msg)
            
            return {
                "success": True,
                "message_id": f"smtp_{datetime.utcnow().timestamp()}",
                "status_code": 250,
                "provider": "smtp"
            }
            
        except Exception as e:
            raise EmailError(f"SMTP error: {e}", recipient=to_email, subject=subject)
    
    async def _send_via_aws_ses(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        from_email: str,
        from_name: str,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send email via AWS SES."""
        try:
            ses = boto3.client("ses")
            
            # Prepare email content
            email_content = {
                "Source": f"{from_name} <{from_email}>",
                "Destination": {"ToAddresses": [to_email]},
                "Message": {
                    "Subject": {"Data": subject},
                    "Body": {
                        "Text": {"Data": text_content},
                        "Html": {"Data": html_content}
                    }
                }
            }
            
            if reply_to:
                email_content["ReplyToAddresses"] = [reply_to]
            
            # Send email
            response = ses.send_email(**email_content)
            
            return {
                "success": True,
                "message_id": response["MessageId"],
                "status_code": 200,
                "provider": "aws_ses"
            }
            
        except ClientError as e:
            raise EmailError(f"AWS SES error: {e}", recipient=to_email, subject=subject)
    
    def render_template(
        self,
        template_name: str,
        template_data: Dict[str, Any],
        template_type: str = "html"
    ) -> str:
        """
        Render an email template with provided data.
        
        Args:
            template_name: Name of the template file
            template_data: Data to populate the template
            template_type: Type of template (html, text)
            
        Returns:
            Rendered template content
        """
        try:
            template_file = f"{template_name}.{template_type}.jinja2"
            template = self.template_env.get_template(template_file)
            return template.render(**template_data)
            
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise EmailError(f"Template rendering failed: {e}")
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML content to plain text."""
        # Simple HTML to text conversion
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        
        # Decode HTML entities
        import html
        text = html.unescape(text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def send_notification_email(
        self,
        notification: Notification,
        db: Session
    ) -> Dict[str, Any]:
        """
        Send a notification email.
        
        Args:
            notification: Notification object
            db: Database session
            
        Returns:
            Delivery result
        """
        try:
            # Get user email
            user = notification.user
            if not user.email:
                raise EmailError("User has no email address", user_id=user.id)
            
            # Get template if specified
            template_data = notification.template_data or {}
            if notification.template_id:
                template = db.query(NotificationTemplate).filter(
                    NotificationTemplate.template_id == notification.template_id,
                    NotificationTemplate.channel == NotificationChannel.EMAIL,
                    NotificationTemplate.is_active == True
                ).first()
                
                if template:
                    html_content = self.render_template(
                        template.template_id,
                        {**template_data, "notification": notification},
                        "html"
                    )
                    text_content = self.render_template(
                        template.template_id,
                        {**template_data, "notification": notification},
                        "text"
                    )
                    subject = template.subject or notification.title
                else:
                    # Use default template
                    html_content = self._create_default_html(notification, template_data)
                    text_content = notification.message
                    subject = notification.title
            else:
                # Use default template
                html_content = self._create_default_html(notification, template_data)
                text_content = notification.message
                subject = notification.title
            
            # Send email
            result = await self.send_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                metadata={"notification_id": notification.id}
            )
            
            # Update notification status
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            notification.external_message_id = result.get("message_id")
            notification.external_status = result.get("status_code")
            
            # Create delivery attempt record
            delivery_attempt = NotificationDeliveryAttempt(
                notification_id=notification.id,
                channel=NotificationChannel.EMAIL,
                status=NotificationStatus.SENT,
                external_message_id=result.get("message_id"),
                external_status=str(result.get("status_code")),
                completed_at=datetime.utcnow()
            )
            
            db.add(delivery_attempt)
            db.commit()
            
            return result
            
        except Exception as e:
            # Update notification status on failure
            notification.status = NotificationStatus.FAILED
            notification.failed_at = datetime.utcnow()
            notification.failure_reason = str(e)
            
            # Create failed delivery attempt record
            delivery_attempt = NotificationDeliveryAttempt(
                notification_id=notification.id,
                channel=NotificationChannel.EMAIL,
                status=NotificationStatus.FAILED,
                error_message=str(e),
                completed_at=datetime.utcnow()
            )
            
            db.add(delivery_attempt)
            db.commit()
            
            raise
    
    def _create_default_html(self, notification: Notification, template_data: Dict[str, Any]) -> str:
        """Create default HTML email template."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{notification.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f8f9fa; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                .priority-high {{ border-left: 4px solid #dc3545; }}
                .priority-normal {{ border-left: 4px solid #007bff; }}
                .priority-low {{ border-left: 4px solid #28a745; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>HealthMate</h1>
                </div>
                <div class="content priority-{notification.priority.value}">
                    <h2>{notification.title}</h2>
                    <p>{notification.message}</p>
                    <p><strong>Type:</strong> {notification.type.value}</p>
                    <p><strong>Priority:</strong> {notification.priority.value}</p>
                    <p><strong>Sent:</strong> {notification.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from HealthMate. Please do not reply to this email.</p>
                    <p>© 2024 HealthMate. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    async def process_bounce_webhook(self, webhook_data: Dict[str, Any], db: Session) -> None:
        """
        Process email bounce webhook from email provider.
        
        Args:
            webhook_data: Webhook data from email provider
            db: Database session
        """
        try:
            # Extract bounce information based on provider
            if self.provider == "sendgrid":
                await self._process_sendgrid_bounce(webhook_data, db)
            elif self.provider == "aws_ses":
                await self._process_aws_ses_bounce(webhook_data, db)
            else:
                logger.warning(f"Bounce processing not implemented for provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Failed to process bounce webhook: {e}")
    
    async def _process_sendgrid_bounce(self, webhook_data: Dict[str, Any], db: Session) -> None:
        """Process SendGrid bounce webhook."""
        for event in webhook_data:
            email = event.get("email")
            event_type = event.get("event")
            message_id = event.get("sg_message_id")
            
            if event_type in ["bounce", "dropped", "spamreport", "unsubscribe"]:
                # Find user by email
                user = db.query(User).filter(User.email == email).first()
                if user:
                    # Create bounce record
                    bounce = NotificationBounce(
                        user_id=user.id,
                        email=email,
                        bounce_type=event_type,
                        bounce_reason=event.get("reason", "Unknown"),
                        external_message_id=message_id,
                        external_bounce_id=event.get("sg_event_id")
                    )
                    db.add(bounce)
                    
                    # Update user notification preferences if hard bounce
                    if event_type == "bounce" and event.get("type") == "hard":
                        prefs = user.notification_preferences
                        if prefs:
                            prefs.email_enabled = False
                    
                    db.commit()
                    
                    logger.info(f"Processed {event_type} for user {user.id}: {email}")
    
    async def _process_aws_ses_bounce(self, webhook_data: Dict[str, Any], db: Session) -> None:
        """Process AWS SES bounce webhook."""
        # Implementation for AWS SES bounce processing
        # This would handle SNS notifications from SES
        pass 
from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Core settings
    openai_api_key: str
    pinecone_api_key: str
    pinecone_environment: str
    pinecone_index_name: str
    postgres_uri: str
    secret_key: str
    
    # Security settings
    environment: str = "development"
    debug: bool = False
    
    # HTTPS/TLS settings
    ssl_keyfile: Optional[str] = None
    ssl_certfile: Optional[str] = None
    ssl_ca_certs: Optional[str] = None
    ssl_check_hostname: bool = True
    ssl_verify_mode: str = "CERT_REQUIRED"
    
    # CORS settings
    cors_allow_origins: str = "*"
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "*"
    cors_allow_headers: str = "*"
    cors_expose_headers: str = ""
    cors_max_age: int = 600
    
    # Security headers
    security_headers_enabled: bool = True
    hsts_max_age: int = 31536000
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False
    content_security_policy: str = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    x_frame_options: str = "DENY"
    x_content_type_options: str = "nosniff"
    x_xss_protection: str = "1; mode=block"
    referrer_policy: str = "strict-origin-when-cross-origin"
    
    # Notification settings
    # Email configuration
    email_provider: str = "sendgrid"  # sendgrid, smtp, aws_ses
    sendgrid_api_key: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    email_from_address: str = "noreply@healthmate.com"
    email_from_name: str = "HealthMate"
    
    # SMS configuration
    sms_provider: str = "twilio"  # twilio, aws_sns
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # Push notification configuration
    push_provider: str = "fcm"  # fcm, apns
    fcm_server_key: Optional[str] = None
    apns_key_id: Optional[str] = None
    apns_team_id: Optional[str] = None
    apns_key_file: Optional[str] = None
    
    # Notification queue settings
    notification_queue_enabled: bool = True
    notification_retry_attempts: int = 3
    notification_retry_delay: int = 300  # seconds
    notification_batch_size: int = 100
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_requests_per_hour: int = 1000
    
    # Request/Response validation
    request_validation_enabled: bool = True
    response_validation_enabled: bool = True
    validation_strict_mode: bool = False
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        if self.cors_allow_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]
    
    @property
    def cors_methods_list(self) -> List[str]:
        """Get CORS methods as a list."""
        if self.cors_allow_methods == "*":
            return ["*"]
        return [method.strip() for method in self.cors_allow_methods.split(",") if method.strip()]
    
    @property
    def cors_headers_list(self) -> List[str]:
        """Get CORS headers as a list."""
        if self.cors_allow_headers == "*":
            return ["*"]
        return [header.strip() for header in self.cors_allow_headers.split(",") if header.strip()]
    
    @property
    def cors_expose_headers_list(self) -> List[str]:
        """Get CORS expose headers as a list."""
        if not self.cors_expose_headers:
            return []
        return [header.strip() for header in self.cors_expose_headers.split(",") if header.strip()]
    
    @property
    def ssl_config(self) -> dict:
        """Get SSL configuration for uvicorn."""
        config = {}
        if self.ssl_keyfile and os.path.exists(self.ssl_keyfile):
            config["ssl_keyfile"] = self.ssl_keyfile
        if self.ssl_certfile and os.path.exists(self.ssl_certfile):
            config["ssl_certfile"] = self.ssl_certfile
        if self.ssl_ca_certs and os.path.exists(self.ssl_ca_certs):
            config["ssl_ca_certs"] = self.ssl_ca_certs
        return config

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        env_prefix = "HEALTHMATE_"

settings = Settings() 
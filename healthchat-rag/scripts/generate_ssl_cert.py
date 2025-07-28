#!/usr/bin/env python3
"""
SSL Certificate Generator for HealthMate Development

This script generates self-signed SSL certificates for development and testing.
For production, use proper SSL certificates from a trusted CA.
"""

import os
import subprocess
import sys
from pathlib import Path

def generate_ssl_certificate(
    key_file: str = "key.pem",
    cert_file: str = "cert.pem",
    days: int = 365,
    common_name: str = "localhost",
    country: str = "US",
    state: str = "CA",
    locality: str = "San Francisco",
    organization: str = "HealthMate Development",
    organizational_unit: str = "Development"
):
    """
    Generate a self-signed SSL certificate using OpenSSL.
    
    Args:
        key_file: Path to the private key file
        cert_file: Path to the certificate file
        days: Certificate validity in days
        common_name: Common name for the certificate
        country: Country code
        state: State or province
        locality: City or locality
        organization: Organization name
        organizational_unit: Organizational unit
    """
    
    # Check if OpenSSL is available
    try:
        subprocess.run(["openssl", "version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: OpenSSL is not installed or not available in PATH")
        print("Please install OpenSSL and try again.")
        sys.exit(1)
    
    # Create certificates directory if it doesn't exist
    cert_dir = Path("ssl")
    cert_dir.mkdir(exist_ok=True)
    
    key_path = cert_dir / key_file
    cert_path = cert_dir / cert_file
    
    # Generate private key
    print(f"Generating private key: {key_path}")
    subprocess.run([
        "openssl", "genrsa",
        "-out", str(key_path),
        "2048"
    ], check=True)
    
    # Generate certificate signing request and self-signed certificate
    print(f"Generating self-signed certificate: {cert_path}")
    subprocess.run([
        "openssl", "req", "-x509", "-new", "-nodes",
        "-key", str(key_path),
        "-sha256", "-days", str(days),
        "-out", str(cert_path),
        "-subj", f"/C={country}/ST={state}/L={locality}/O={organization}/OU={organizational_unit}/CN={common_name}"
    ], check=True)
    
    print(f"\nSSL certificate generated successfully!")
    print(f"Private key: {key_path}")
    print(f"Certificate: {cert_path}")
    print(f"Validity: {days} days")
    print(f"Common Name: {common_name}")
    
    # Set proper permissions
    os.chmod(key_path, 0o600)
    os.chmod(cert_path, 0o644)
    
    return str(key_path), str(cert_path)

def create_nginx_ssl_config(key_file: str, cert_file: str, output_file: str = "nginx-ssl.conf"):
    """
    Create an Nginx SSL configuration template.
    
    Args:
        key_file: Path to the private key file
        cert_file: Path to the certificate file
        output_file: Output configuration file name
    """
    
    config_template = f"""# Nginx SSL Configuration for HealthMate
# This is a template - customize for your environment

server {{
    listen 80;
    server_name localhost;
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name localhost;

    # SSL Configuration
    ssl_certificate {cert_file};
    ssl_certificate_key {key_file};
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Proxy to FastAPI application
    location / {{
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
    }}
    
    # Health check
    location /health {{
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }}
}}
"""
    
    with open(output_file, "w") as f:
        f.write(config_template)
    
    print(f"Nginx SSL configuration template created: {output_file}")

def main():
    """Main function to generate SSL certificates."""
    
    print("HealthMate SSL Certificate Generator")
    print("=" * 40)
    
    # Generate certificates
    key_file, cert_file = generate_ssl_certificate()
    
    # Create Nginx configuration
    create_nginx_ssl_config(key_file, cert_file)
    
    print("\nNext steps:")
    print("1. Update your .env file with SSL certificate paths:")
    print(f"   HEALTHMATE_SSL_KEYFILE={key_file}")
    print(f"   HEALTHMATE_SSL_CERTFILE={cert_file}")
    print("2. Run the application with SSL:")
    print("   uvicorn app.main:app --ssl-keyfile ssl/key.pem --ssl-certfile ssl/cert.pem")
    print("3. Or use Nginx as a reverse proxy with the generated nginx-ssl.conf")
    print("\nNote: These are self-signed certificates for development only.")
    print("For production, use certificates from a trusted Certificate Authority.")

if __name__ == "__main__":
    main() 
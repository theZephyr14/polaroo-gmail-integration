#!/usr/bin/env python3
"""
Gmail Service Account Demo
=========================

Uses a Google Service Account for automated Gmail sending.
No user interaction required after initial setup.
"""

import os
import json
import base64
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("❌ Google API libraries not installed!")
    print("   Run: pip install google-api-python-client google-auth")
    exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GmailServiceDemo:
    def __init__(self):
        self.service = None
        self.email_generator = None
        self.generated_emails = []
        self.sender_email = None
        
    def setup_service_account(self):
        """Set up Gmail API using service account."""
        print("🔑 Setting up Gmail API with service account...")
        
        service_account_file = Path('service-account.json')
        
        if not service_account_file.exists():
            print("❌ service-account.json not found!")
            print("   Please follow these steps:")
            print("   1. Go to https://console.cloud.google.com/")
            print("   2. Create a service account")
            print("   3. Enable domain-wide delegation")
            print("   4. Download the JSON key file")
            print("   5. Rename it to 'service-account.json'")
            return False
        
        try:
            # Load service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                'service-account.json',
                scopes=['https://www.googleapis.com/auth/gmail.send']
            )
            
            # For service accounts, you need to specify which user to impersonate
            # This requires domain-wide delegation
            delegated_credentials = credentials.with_subject(self.sender_email)
            
            self.service = build('gmail', 'v1', credentials=delegated_credentials)
            print("✅ Service account authentication successful!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup service account: {e}")
            print("   Make sure domain-wide delegation is enabled")
            return False
    
    def load_config(self):
        """Load configuration from email_config.json"""
        config_file = Path("email_config.json")
        
        if not config_file.exists():
            print("❌ email_config.json not found!")
            return False
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Get sender email from config
            self.sender_email = config.get('gmail_credentials', {}).get('email')
            
            if not self.sender_email:
                print("❌ No sender email found in config")
                return False
            
            print(f"📧 Using sender: {self.sender_email}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return False
    
    def setup_email_system(self):
        """Initialize the email system components."""
        try:
            from src.email_system.email_generator import EmailGenerator
            
            self.email_generator = EmailGenerator("email_templates.xlsx")
            print("✅ Email system initialized!")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize email system: {e}")
            return False
    
    def generate_emails(self):
        """Generate sample emails."""
        print("📧 Generating sample emails...")
        
        properties = [
            {
                'name': 'Aribau 1º 1ª',
                'elec_cost': 45.50,
                'water_cost': 25.30,
                'allowance': 50.0,
                'total_extra': 20.80,
                'payment_link': 'https://payment.example.com/aribau',
                'electricity_invoice_url': '_debug/invoices/elec_test_001_20250903.pdf',
                'water_invoice_url': '_debug/invoices/water_test_001_20250903.pdf'
            },
            {
                'name': 'Test Property 2',
                'elec_cost': 60.00,
                'water_cost': 30.00,
                'allowance': 70.0,
                'total_extra': 20.00,
                'payment_link': 'https://payment.example.com/test2'
            }
        ]
        
        self.generated_emails = []
        for i, property_data in enumerate(properties, 1):
            print(f"\n🏠 Processing Property {i}: {property_data['name']}")
            print(f"   - Total Extra: €{property_data['total_extra']:.2f}")
            
            email_data = self.email_generator.generate_email_for_property(property_data)
            if email_data:
                self.generated_emails.append(email_data)
                print(f"   ✅ Email generated")
        
        print(f"\n✅ Generated {len(self.generated_emails)} emails")
        return len(self.generated_emails) > 0
    
    def send_email(self, email_data, dry_run=False):
        """Send email using Gmail API."""
        print(f"\n📤 {'[DRY RUN] ' if dry_run else ''}Sending email")
        print(f"   To: {email_data['email_address']}")
        print(f"   Subject: {email_data['subject']}")
        print(f"   Amount: €{email_data['total_extra']:.2f}")
        
        if dry_run:
            print("   ✅ Email prepared (dry run)")
            return {'success': True}
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['to'] = email_data['email_address']
            msg['from'] = self.sender_email
            msg['subject'] = email_data['subject']
            
            # Add body
            body = MIMEText(email_data['body'], 'plain')
            msg.attach(body)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            message = {'raw': raw_message}
            
            # Send via API
            result = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            print(f"   ✅ Email sent! ID: {result['id']}")
            return {'success': True, 'message_id': result['id']}
            
        except Exception as e:
            print(f"   ❌ Failed to send: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_demo(self, dry_run=True):
        """Run the service account demo."""
        print("🚀 Gmail Service Account Demo")
        print("=" * 40)
        
        # Load config first to get sender email
        if not self.load_config():
            return False
        
        # Setup service account
        if not self.setup_service_account():
            return False
        
        # Setup email system
        if not self.setup_email_system():
            return False
        
        # Generate emails
        if not self.generate_emails():
            return False
        
        # Send emails
        sent_count = 0
        for i, email_data in enumerate(self.generated_emails, 1):
            result = self.send_email(email_data, dry_run)
            if result['success']:
                sent_count += 1
        
        print(f"\n📊 Summary: {sent_count}/{len(self.generated_emails)} emails sent")
        return True

def main():
    """Run the service account demo."""
    demo = GmailServiceDemo()
    
    try:
        print("🔒 Running in DRY RUN mode")
        success = demo.run_demo(dry_run=True)
        
        if success:
            choice = input("\nSend real emails? (y/N): ")
            if choice.lower() == 'y':
                demo.run_demo(dry_run=False)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

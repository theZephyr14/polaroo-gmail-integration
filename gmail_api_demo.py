#!/usr/bin/env python3
"""
Gmail API Demo
==============

Uses the official Gmail API to send emails automatically.
Much more reliable than browser automation.
"""

import os
import json
import base64
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

# Gmail API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("❌ Gmail API libraries not installed!")
    print("   Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class GmailAPIDemo:
    def __init__(self):
        self.service = None
        self.email_generator = None
        self.generated_emails = []
        
    def setup_gmail_api(self):
        """Set up Gmail API authentication."""
        print("🔑 Setting up Gmail API authentication...")
        
        creds = None
        token_file = Path('token.json')
        credentials_file = Path('credentials.json')
        
        # Load existing token
        if token_file.exists():
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing expired credentials...")
                creds.refresh(Request())
            else:
                if not credentials_file.exists():
                    print("❌ credentials.json not found!")
                    print("   Please follow these steps:")
                    print("   1. Go to https://console.cloud.google.com/")
                    print("   2. Create a new project or select existing one")
                    print("   3. Enable Gmail API")
                    print("   4. Create OAuth 2.0 credentials")
                    print("   5. Download credentials.json to this folder")
                    return False
                
                print("🔐 Starting OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            print("✅ Gmail API authentication successful!")
            return True
        except Exception as e:
            print(f"❌ Failed to build Gmail service: {e}")
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
                'payment_link': 'https://payment.example.com/test2',
                'electricity_invoice_url': '',
                'water_invoice_url': ''
            }
        ]
        
        self.generated_emails = []
        for i, property_data in enumerate(properties, 1):
            print(f"\n🏠 Processing Property {i}: {property_data['name']}")
            print(f"   - Electricity: €{property_data['elec_cost']:.2f}")
            print(f"   - Water: €{property_data['water_cost']:.2f}")
            print(f"   - Allowance: €{property_data['allowance']:.2f}")
            print(f"   - Total Extra: €{property_data['total_extra']:.2f}")
            
            email_data = self.email_generator.generate_email_for_property(property_data)
            if email_data:
                self.generated_emails.append(email_data)
                print(f"   ✅ Email generated (ID: {email_data['id'][:8]}...)")
            else:
                print(f"   ⏭️  No email generated")
        
        print(f"\n✅ Generated {len(self.generated_emails)} emails")
        return len(self.generated_emails) > 0
    
    def create_message(self, email_data, sender_email):
        """Create email message for Gmail API."""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['to'] = email_data['email_address']
            msg['from'] = sender_email
            msg['subject'] = email_data['subject']
            
            # Add body
            body = MIMEText(email_data['body'], 'plain')
            msg.attach(body)
            
            # Add attachments if they exist
            if email_data.get('electricity_invoice_url') and os.path.exists(email_data['electricity_invoice_url']):
                self.add_attachment(msg, email_data['electricity_invoice_url'], 'electricity_invoice.pdf')
            
            if email_data.get('water_invoice_url') and os.path.exists(email_data['water_invoice_url']):
                self.add_attachment(msg, email_data['water_invoice_url'], 'water_invoice.pdf')
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            return {'raw': raw_message}
            
        except Exception as e:
            print(f"❌ Error creating message: {e}")
            return None
    
    def add_attachment(self, msg, file_path, filename):
        """Add attachment to email message."""
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            msg.attach(part)
            print(f"   📎 Added attachment: {filename}")
        except Exception as e:
            print(f"   ⚠️  Could not add attachment {filename}: {e}")
    
    def send_email(self, email_data, sender_email, dry_run=False):
        """Send email using Gmail API."""
        print(f"\n📤 {'[DRY RUN] ' if dry_run else ''}Sending email to {email_data['email_address']}")
        print(f"   Subject: {email_data['subject']}")
        print(f"   Amount: €{email_data['total_extra']:.2f}")
        
        if dry_run:
            print("   ✅ Email prepared (dry run mode)")
            return {'success': True, 'message_id': 'dry-run-' + email_data['id'][:8]}
        
        try:
            message = self.create_message(email_data, sender_email)
            if not message:
                return {'success': False, 'error': 'Failed to create message'}
            
            result = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            print(f"   ✅ Email sent successfully!")
            print(f"   Message ID: {result['id']}")
            
            return {
                'success': True,
                'message_id': result['id'],
                'sent_at': datetime.now().isoformat()
            }
            
        except HttpError as error:
            print(f"   ❌ Gmail API error: {error}")
            return {'success': False, 'error': str(error)}
        except Exception as e:
            print(f"   ❌ Send error: {e}")
            return {'success': False, 'error': str(e)}
    
    def run_demo(self, sender_email="me", dry_run=True):
        """Run the complete Gmail API demo."""
        print("🚀 Gmail API Demo")
        print("=" * 50)
        print(f"📧 Sender: {sender_email}")
        print(f"🔧 Dry run: {dry_run}")
        print()
        
        # Setup
        if not self.setup_gmail_api():
            return False
        
        if not self.setup_email_system():
            return False
        
        if not self.generate_emails():
            print("❌ No emails generated, cannot continue")
            return False
        
        # Send emails
        sent_count = 0
        failed_count = 0
        
        for i, email_data in enumerate(self.generated_emails, 1):
            print(f"\n📧 Email {i} of {len(self.generated_emails)}")
            
            result = self.send_email(email_data, sender_email, dry_run)
            
            if result['success']:
                sent_count += 1
                print(f"   ✅ Success!")
            else:
                failed_count += 1
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
            
            # Wait between emails
            if i < len(self.generated_emails):
                print("   ⏳ Waiting 2 seconds...")
                import time
                time.sleep(2)
        
        # Summary
        print(f"\n📊 Summary:")
        print(f"   ✅ Sent: {sent_count}")
        print(f"   ❌ Failed: {failed_count}")
        print(f"   📧 Total: {len(self.generated_emails)}")
        
        if dry_run:
            print(f"\n💡 This was a dry run. To actually send emails:")
            print(f"   Set dry_run=False in the run_demo() call")
        
        print(f"\n🎉 Gmail API demo completed!")
        return True

def main():
    """Run the Gmail API demo."""
    demo = GmailAPIDemo()
    
    try:
        # Run in dry run mode by default for safety
        print("🔒 Running in DRY RUN mode (no emails will be sent)")
        print("   This will test the API connection and email generation")
        print()
        
        success = demo.run_demo(dry_run=True)
        
        if success:
            print("\n✅ Demo completed successfully!")
            
            # Ask if user wants to send real emails
            choice = input("\nDo you want to send real emails? (y/N): ").lower()
            if choice == 'y':
                print("\n🚀 Sending real emails...")
                demo.run_demo(dry_run=False)
        else:
            print("\n❌ Demo failed!")
            
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")

if __name__ == "__main__":
    main()

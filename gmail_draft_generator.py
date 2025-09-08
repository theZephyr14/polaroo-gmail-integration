#!/usr/bin/env python3
"""
Gmail Draft Generator
====================

Creates Gmail drafts using the Gmail API instead of sending emails directly.
This allows users to review, edit, and send emails manually for better control.

Key Features:
- Creates drafts instead of sending emails
- Handles PDF attachments from Supabase
- Uses proper Gmail API authentication
- Allows manual review before sending
- Integrates with existing PDF storage system
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
from typing import List, Dict, Optional, Any

# Gmail API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_API_AVAILABLE = True
except ImportError:
    print("❌ Gmail API libraries not installed!")
    print("   Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    GMAIL_API_AVAILABLE = False
    # Don't exit immediately, let the class handle it gracefully

from src.pdf_storage import PDFStorage

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gmail API scopes - need both compose and modify for drafts
SCOPES = [
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify'
]

class GmailDraftGenerator:
    """Creates Gmail drafts with PDF attachments for utility bill overages."""
    
    def __init__(self):
        self.service = None
        self.pdf_storage = PDFStorage()
        self.property_name = "Aribau 1º 1ª"
        
    def setup_gmail_api(self) -> bool:
        """Set up Gmail API authentication."""
        if not GMAIL_API_AVAILABLE:
            print("❌ Gmail API libraries not available!")
            return False
            
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
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"❌ Failed to refresh credentials: {e}")
                    creds = None
            
            if not creds:
                if not credentials_file.exists():
                    print("❌ credentials.json not found!")
                    print("   Please follow these steps:")
                    print("   1. Go to https://console.cloud.google.com/")
                    print("   2. Create a new project or select existing one")
                    print("   3. Enable Gmail API")
                    print("   4. Create OAuth 2.0 credentials (Desktop application)")
                    print("   5. Download credentials.json to this folder")
                    return False
                
                print("🔐 Starting OAuth flow...")
                try:
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"❌ OAuth flow failed: {e}")
                    return False
            
            # Save credentials for next run
            try:
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
                print("💾 Credentials saved for future use")
            except Exception as e:
                print(f"⚠️  Could not save credentials: {e}")
        
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            print("✅ Gmail API authentication successful!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to build Gmail service: {e}")
            return False
    
    def download_pdfs_from_supabase(self) -> List[str]:
        """Download PDFs for the property from Supabase."""
        print(f"📥 Downloading PDFs for {self.property_name}...")
        
        try:
            # Get all PDFs for this property
            pdfs = self.pdf_storage.list_pdfs_for_property(self.property_name)
            
            if not pdfs:
                print(f"❌ No PDFs found for {self.property_name}")
                return []
            
            print(f"📄 Found {len(pdfs)} PDFs:")
            for pdf in pdfs:
                print(f"   - {pdf['filename']}")
            
            # Download PDFs to local temp folder
            temp_folder = Path("_temp_pdfs")
            temp_folder.mkdir(exist_ok=True)
            
            downloaded_files = []
            for pdf in pdfs:
                try:
                    # Create download URL
                    download_url = self.pdf_storage.create_download_url(pdf['object_key'])
                    
                    # Download the PDF
                    import requests
                    response = requests.get(download_url)
                    response.raise_for_status()
                    
                    # Save to temp folder with timestamp to avoid conflicts
                    filename = pdf['filename']
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    unique_filename = f"{timestamp}_{filename}"
                    filepath = temp_folder / unique_filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    downloaded_files.append(str(filepath))
                    print(f"   ✅ Downloaded: {unique_filename}")
                    
                except Exception as e:
                    print(f"   ❌ Failed to download {pdf['filename']}: {e}")
            
            return downloaded_files
            
        except Exception as e:
            print(f"❌ Error downloading PDFs: {e}")
            return []
    
    def create_email_message(self, recipient_email: str, pdf_files: List[str]) -> Optional[Dict[str, Any]]:
        """Create email message with PDF attachments."""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['to'] = recipient_email
            msg['subject'] = f"Utility Overages - {self.property_name}"
            
            # Email body template
            email_body = f"""Hey girls,

Hope everything is well with you ☺️

Please find attached utility invoices for: Electricity + Water

June and july: 122.88€ + 114.94€ + 95.94€ = 333.76€ - 200€ = 133.76€

We cover 100€ a month, in total the debt amounts to 133.76€.

Please make the payment as soon as possible to the following account and send us the receipt please:

Bank Name: La Caixa
Bank Account Number: ES34 2100 8668 2502 0017 5308
To: ALQUILERES BCN HOMES,S.L.
SWIFT code: CAIXESBBXXX

Best regards,
Gaby"""
            
            # Add body
            body = MIMEText(email_body, 'plain')
            msg.attach(body)
            
            # Add PDF attachments
            for pdf_file in pdf_files:
                if os.path.exists(pdf_file):
                    self.add_attachment(msg, pdf_file)
                else:
                    print(f"⚠️  PDF file not found: {pdf_file}")
            
            # Encode message for Gmail API
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            return {'raw': raw_message}
            
        except Exception as e:
            print(f"❌ Error creating message: {e}")
            return None
    
    def add_attachment(self, msg: MIMEMultipart, file_path: str):
        """Add PDF attachment to email message."""
        try:
            filename = Path(file_path).name
            
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
            print(f"   ⚠️  Could not add attachment {Path(file_path).name}: {e}")
    
    def create_draft(self, recipient_email: str, pdf_files: List[str]) -> Optional[str]:
        """Create a Gmail draft with the email and attachments."""
        print(f"\n📝 Creating Gmail draft...")
        print(f"   To: {recipient_email}")
        print(f"   Subject: Utility Overages - {self.property_name}")
        print(f"   Attachments: {len(pdf_files)} PDFs")
        
        try:
            # Create email message
            message = self.create_email_message(recipient_email, pdf_files)
            if not message:
                return None
            
            # Create draft using Gmail API
            draft_body = {'message': message}
            
            result = self.service.users().drafts().create(
                userId='me',
                body=draft_body
            ).execute()
            
            draft_id = result['id']
            print(f"   ✅ Draft created successfully! ID: {draft_id}")
            
            # Get Gmail URL for the draft
            gmail_url = f"https://mail.google.com/mail/u/0/#drafts/{draft_id}"
            print(f"   🔗 View draft: {gmail_url}")
            
            return draft_id
            
        except HttpError as e:
            print(f"   ❌ Gmail API error: {e}")
            return None
        except Exception as e:
            print(f"   ❌ Failed to create draft: {e}")
            return None
    
    def list_drafts(self) -> List[Dict[str, Any]]:
        """List existing drafts."""
        try:
            result = self.service.users().drafts().list(userId='me').execute()
            drafts = result.get('drafts', [])
            
            if drafts:
                print(f"\n📋 Found {len(drafts)} existing drafts:")
                for i, draft in enumerate(drafts[:5], 1):  # Show only first 5
                    draft_id = draft['id']
                    # Get draft details
                    draft_details = self.service.users().drafts().get(
                        userId='me', 
                        id=draft_id
                    ).execute()
                    
                    message = draft_details['message']
                    subject = "No Subject"
                    to_email = "Unknown"
                    
                    for header in message['payload'].get('headers', []):
                        if header['name'] == 'Subject':
                            subject = header['value']
                        elif header['name'] == 'To':
                            to_email = header['value']
                    
                    print(f"   {i}. {subject} → {to_email}")
            else:
                print("\n📋 No existing drafts found")
            
            return drafts
            
        except Exception as e:
            print(f"❌ Error listing drafts: {e}")
            return []
    
    def cleanup_temp_files(self):
        """Clean up temporary PDF files."""
        temp_folder = Path("_temp_pdfs")
        if temp_folder.exists():
            try:
                import shutil
                shutil.rmtree(temp_folder)
                print("🧹 Cleaned up temporary files")
            except Exception as e:
                print(f"⚠️  Could not clean up temp files: {e}")
    
    def run_draft_generator(self):
        """Run the complete draft generation process."""
        print("🚀 Gmail Draft Generator")
        print("=" * 50)
        print("This tool creates Gmail drafts that you can:")
        print("- Review and edit before sending")
        print("- Send manually when ready")
        print("- Keep as drafts for later")
        print("=" * 50)
        
        # Setup Gmail API
        if not self.setup_gmail_api():
            print("❌ Failed to setup Gmail API. Please check credentials.")
            return False
        
        # List existing drafts
        self.list_drafts()
        
        # Get recipient email
        recipient_email = input("\nEnter recipient email address: ").strip()
        if not recipient_email:
            print("❌ Recipient email is required")
            return False
        
        # Validate email format
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', recipient_email):
            print("❌ Invalid email format")
            return False
        
        try:
            # Download PDFs from Supabase
            pdf_files = self.download_pdfs_from_supabase()
            
            if not pdf_files:
                print("❌ No PDFs to attach. Cannot create draft.")
                return False
            
            # Create draft
            draft_id = self.create_draft(recipient_email, pdf_files)
            
            if draft_id:
                print(f"\n🎉 Draft created successfully!")
                print(f"📧 Gmail draft is ready for review")
                print(f"🔗 Open Gmail and go to Drafts to review and send")
                print(f"📎 {len(pdf_files)} PDFs are attached")
                
                # Ask if user wants to open Gmail
                open_gmail = input("\nOpen Gmail in browser? (y/n): ").strip().lower()
                if open_gmail == 'y':
                    import webbrowser
                    webbrowser.open("https://mail.google.com/mail/u/0/#drafts")
                
                return True
            else:
                print("❌ Failed to create draft")
                return False
                
        except KeyboardInterrupt:
            print("\n👋 Draft generation cancelled")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
        finally:
            # Always cleanup temp files
            self.cleanup_temp_files()

def main():
    """Run the Gmail Draft Generator."""
    try:
        generator = GmailDraftGenerator()
        success = generator.run_draft_generator()
        
        if success:
            print("\n✅ Draft generation completed successfully!")
        else:
            print("\n❌ Draft generation failed")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Gmail Batch Draft Generator
===========================

Creates multiple Gmail drafts from Excel data for bulk email processing.
Integrates with the existing email system to generate drafts instead of sending emails.

Features:
- Reads recipient data from Excel files
- Creates individual drafts for each recipient
- Handles property-specific PDF attachments
- Allows batch review and sending
- Integrates with existing template system
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional, Any

# Add src to path for imports
sys.path.append('src')

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    print("❌ Pandas not installed! Run: pip install pandas")
    PANDAS_AVAILABLE = False

from gmail_draft_generator import GmailDraftGenerator

# Optional imports for enhanced functionality
try:
    from src.email_system.email_generator import EmailGenerator
    EMAIL_GENERATOR_AVAILABLE = True
except ImportError:
    EMAIL_GENERATOR_AVAILABLE = False

try:
    from src.email_system.template_manager import TemplateManager
    TEMPLATE_MANAGER_AVAILABLE = True
except ImportError:
    TEMPLATE_MANAGER_AVAILABLE = False

class GmailBatchDraftGenerator(GmailDraftGenerator):
    """Extends GmailDraftGenerator to handle batch processing from Excel data."""
    
    def __init__(self, excel_file: str = "Book1.xlsx"):
        super().__init__()
        self.excel_file = excel_file
        self.email_generator = EmailGenerator() if EMAIL_GENERATOR_AVAILABLE else None
        
    def load_recipients_from_excel(self) -> List[Dict[str, Any]]:
        """Load recipient data from Excel file."""
        print(f"📊 Loading recipients from {self.excel_file}...")
        
        if not PANDAS_AVAILABLE:
            print("❌ Pandas not available! Cannot read Excel file.")
            return []
        
        try:
            if not Path(self.excel_file).exists():
                print(f"❌ Excel file not found: {self.excel_file}")
                return []
            
            # Read Excel file
            df = pd.read_excel(self.excel_file)
            
            # Expected columns (adjust based on your Excel structure)
            required_columns = ['property_name', 'email_address']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                print(f"❌ Missing required columns: {missing_columns}")
                print(f"   Available columns: {list(df.columns)}")
                return []
            
            recipients = []
            for index, row in df.iterrows():
                try:
                    recipient = {
                        'property_name': str(row['property_name']).strip(),
                        'email_address': str(row['email_address']).strip(),
                        'row_index': index + 1
                    }
                    
                    # Add optional fields if they exist
                    optional_fields = ['total_extra', 'electricity_amount', 'water_amount', 'notes']
                    for field in optional_fields:
                        if field in df.columns and pd.notna(row[field]):
                            recipient[field] = row[field]
                    
                    # Validate email
                    import re
                    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', recipient['email_address']):
                        print(f"   ⚠️  Skipping invalid email at row {recipient['row_index']}: {recipient['email_address']}")
                        continue
                    
                    recipients.append(recipient)
                    
                except Exception as e:
                    print(f"   ⚠️  Error processing row {index + 1}: {e}")
                    continue
            
            print(f"   ✅ Loaded {len(recipients)} valid recipients")
            return recipients
            
        except Exception as e:
            print(f"❌ Error reading Excel file: {e}")
            return []
    
    def generate_email_content(self, recipient: Dict[str, Any]) -> Dict[str, str]:
        """Generate personalized email content for a recipient."""
        try:
            # Use the existing email generator if available
            if self.email_generator and hasattr(self.email_generator, 'generate_email_for_property'):
                email_data = self.email_generator.generate_email_for_property(recipient)
                if email_data:
                    return {
                        'subject': email_data.get('subject', f"Utility Overages - {recipient['property_name']}"),
                        'body': email_data.get('body', self.get_default_email_body(recipient))
                    }
            
            # Fallback to default template
            return {
                'subject': f"Utility Overages - {recipient['property_name']}",
                'body': self.get_default_email_body(recipient)
            }
            
        except Exception as e:
            print(f"   ⚠️  Error generating email content: {e}")
            return {
                'subject': f"Utility Overages - {recipient['property_name']}",
                'body': self.get_default_email_body(recipient)
            }
    
    def get_default_email_body(self, recipient: Dict[str, Any]) -> str:
        """Get default email body template."""
        property_name = recipient['property_name']
        total_amount = recipient.get('total_extra', '133.76')
        
        return f"""Hey girls,

Hope everything is well with you ☺️

Please find attached utility invoices for: Electricity + Water

June and july: 122.88€ + 114.94€ + 95.94€ = 333.76€ - 200€ = {total_amount}€

We cover 100€ a month, in total the debt amounts to {total_amount}€.

Please make the payment as soon as possible to the following account and send us the receipt please:

Bank Name: La Caixa
Bank Account Number: ES34 2100 8668 2502 0017 5308
To: ALQUILERES BCN HOMES,S.L.
SWIFT code: CAIXESBBXXX

Best regards,
Gaby"""
    
    def create_email_message_for_recipient(self, recipient: Dict[str, Any], pdf_files: List[str]) -> Optional[Dict[str, Any]]:
        """Create email message for a specific recipient."""
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            import base64
            
            # Generate personalized content
            email_content = self.generate_email_content(recipient)
            
            # Create message
            msg = MIMEMultipart()
            msg['to'] = recipient['email_address']
            msg['subject'] = email_content['subject']
            
            # Add body
            body = MIMEText(email_content['body'], 'plain')
            msg.attach(body)
            
            # Add PDF attachments for this property
            property_pdfs = [pdf for pdf in pdf_files if recipient['property_name'].lower() in pdf.lower()]
            
            for pdf_file in property_pdfs:
                if os.path.exists(pdf_file):
                    self.add_attachment(msg, pdf_file)
            
            # If no property-specific PDFs found, use all PDFs
            if not property_pdfs:
                for pdf_file in pdf_files:
                    if os.path.exists(pdf_file):
                        self.add_attachment(msg, pdf_file)
            
            # Encode message for Gmail API
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            return {'raw': raw_message}
            
        except Exception as e:
            print(f"   ❌ Error creating message for {recipient['email_address']}: {e}")
            return None
    
    def create_batch_drafts(self, recipients: List[Dict[str, Any]], pdf_files: List[str]) -> List[str]:
        """Create drafts for all recipients."""
        print(f"\n📝 Creating {len(recipients)} Gmail drafts...")
        
        draft_ids = []
        successful = 0
        failed = 0
        
        for i, recipient in enumerate(recipients, 1):
            print(f"\n   [{i}/{len(recipients)}] Creating draft for {recipient['property_name']}")
            print(f"      Email: {recipient['email_address']}")
            
            try:
                # Create email message
                message = self.create_email_message_for_recipient(recipient, pdf_files)
                if not message:
                    print(f"      ❌ Failed to create message")
                    failed += 1
                    continue
                
                # Create draft using Gmail API
                draft_body = {'message': message}
                
                result = self.service.users().drafts().create(
                    userId='me',
                    body=draft_body
                ).execute()
                
                draft_id = result['id']
                draft_ids.append(draft_id)
                successful += 1
                
                print(f"      ✅ Draft created! ID: {draft_id}")
                
            except Exception as e:
                print(f"      ❌ Failed to create draft: {e}")
                failed += 1
                continue
        
        print(f"\n📊 Batch Results:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📝 Total drafts created: {len(draft_ids)}")
        
        return draft_ids
    
    def run_batch_draft_generator(self):
        """Run the complete batch draft generation process."""
        print("🚀 Gmail Batch Draft Generator")
        print("=" * 50)
        print("This tool creates multiple Gmail drafts from Excel data")
        print("Features:")
        print("- Reads recipients from Excel file")
        print("- Creates individual drafts for each recipient")
        print("- Attaches relevant PDFs per property")
        print("- Allows batch review and sending")
        print("=" * 50)
        
        # Setup Gmail API
        if not self.setup_gmail_api():
            print("❌ Failed to setup Gmail API. Please check credentials.")
            return False
        
        try:
            # Load recipients from Excel
            recipients = self.load_recipients_from_excel()
            
            if not recipients:
                print("❌ No valid recipients found in Excel file")
                return False
            
            # Show recipients for confirmation
            print(f"\n📋 Found {len(recipients)} recipients:")
            for i, recipient in enumerate(recipients[:5], 1):  # Show first 5
                print(f"   {i}. {recipient['property_name']} → {recipient['email_address']}")
            
            if len(recipients) > 5:
                print(f"   ... and {len(recipients) - 5} more")
            
            # Ask for confirmation
            confirm = input(f"\nCreate drafts for all {len(recipients)} recipients? (y/n): ").strip().lower()
            if confirm != 'y':
                print("❌ Batch draft generation cancelled")
                return False
            
            # Download PDFs from Supabase
            pdf_files = self.download_pdfs_from_supabase()
            
            if not pdf_files:
                print("⚠️  No PDFs found, but continuing with text-only drafts...")
            
            # Create batch drafts
            draft_ids = self.create_batch_drafts(recipients, pdf_files)
            
            if draft_ids:
                print(f"\n🎉 Batch draft generation completed!")
                print(f"📧 {len(draft_ids)} Gmail drafts are ready for review")
                print(f"🔗 Open Gmail and go to Drafts to review and send")
                
                # Ask if user wants to open Gmail
                open_gmail = input("\nOpen Gmail in browser? (y/n): ").strip().lower()
                if open_gmail == 'y':
                    import webbrowser
                    webbrowser.open("https://mail.google.com/mail/u/0/#drafts")
                
                return True
            else:
                print("❌ No drafts were created successfully")
                return False
                
        except KeyboardInterrupt:
            print("\n👋 Batch draft generation cancelled")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
        finally:
            # Always cleanup temp files
            self.cleanup_temp_files()

def main():
    """Run the Gmail Batch Draft Generator."""
    try:
        # Check if custom Excel file is provided
        excel_file = "Book1.xlsx"
        if len(sys.argv) > 1:
            excel_file = sys.argv[1]
        
        generator = GmailBatchDraftGenerator(excel_file)
        success = generator.run_batch_draft_generator()
        
        if success:
            print("\n✅ Batch draft generation completed successfully!")
        else:
            print("\n❌ Batch draft generation failed")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")

if __name__ == "__main__":
    main()

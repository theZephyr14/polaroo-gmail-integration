#!/usr/bin/env python3
"""
Gmail Fixed Automation - Handles signature placement and manual compose click
"""

import asyncio
import os
import time
from pathlib import Path
from playwright.async_api import async_playwright
from src.pdf_storage import PDFStorage

class GmailFixedAutomation:
    def __init__(self):
        self.pdf_storage = PDFStorage()
        self.property_name = "Aribau 1º 1ª"
        
    async def download_pdfs_from_supabase(self):
        """Download PDFs for the property from Supabase"""
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
                    
                    # Save to temp folder
                    filename = pdf['filename']
                    filepath = temp_folder / filename
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    downloaded_files.append(str(filepath))
                    print(f"   ✅ Downloaded: {filename}")
                    
                except Exception as e:
                    print(f"   ❌ Failed to download {pdf['filename']}: {e}")
            
            return downloaded_files
            
        except Exception as e:
            print(f"❌ Error downloading PDFs: {e}")
            return []
    
    async def open_gmail_and_fill_email(self, pdf_files, recipient_email):
        """Open Gmail and fill email with proper signature handling"""
        print("🌐 Opening Gmail popup window...")
        
        async with async_playwright() as p:
            # Launch browser with visible window (popup)
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--start-maximized',
                    '--new-window',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Go to Gmail
                print("📧 Navigating to Gmail...")
                await page.goto("https://mail.google.com", wait_until="networkidle")
                await page.wait_for_timeout(3000)
                
                # Give user time to sign in
                print("⏳ Please sign in to Gmail if needed...")
                print("   (The browser window is open - please sign in and click Compose)")
                print("   Then press Enter here to continue...")
                input()
                
                # Wait for compose window to be ready
                print("⏳ Waiting for compose window...")
                await page.wait_for_timeout(3000)
                
                # Try to fill recipient
                print(f"📝 Filling recipient: {recipient_email}")
                try:
                    # Try multiple selectors for recipient field
                    recipient_selectors = [
                        '[name="to"]',
                        'input[name="to"]',
                        'div[name="to"]',
                        '[aria-label*="To"]',
                        'div[aria-label*="To"]'
                    ]
                    
                    recipient_filled = False
                    for selector in recipient_selectors:
                        try:
                            await page.fill(selector, recipient_email)
                            recipient_filled = True
                            print("   ✅ Recipient filled")
                            break
                        except Exception as e:
                            continue
                    
                    if not recipient_filled:
                        print(f"   ❌ Could not fill recipient automatically")
                        print(f"   Please manually enter: {recipient_email}")
                
                except Exception as e:
                    print(f"   ❌ Error filling recipient: {e}")
                
                # Try to fill subject
                print("📝 Filling subject...")
                try:
                    subject = f"Utility Overages - {self.property_name}"
                    await page.fill('[name="subjectbox"]', subject)
                    print("   ✅ Subject filled")
                except Exception as e:
                    print(f"   ❌ Could not fill subject: {e}")
                    print(f"   Please manually enter: {subject}")
                
                # Handle email body with proper signature placement
                print("📝 Filling email body (above signature)...")
                try:
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
                    
                    # Try to click in the message body area (above signature)
                    message_selectors = [
                        '[role="textbox"]',
                        'div[role="textbox"]',
                        'div[aria-label*="Message Body"]',
                        'div[aria-label*="message body"]',
                        'div[contenteditable="true"]',
                        'div[contenteditable="true"][role="textbox"]'
                    ]
                    
                    message_clicked = False
                    for selector in message_selectors:
                        try:
                            # Click at the beginning of the message area
                            await page.click(selector)
                            # Move cursor to the very beginning (before signature)
                            await page.keyboard.press('Home')
                            await page.keyboard.press('Home')  # Press twice to ensure we're at the very top
                            message_clicked = True
                            print(f"   ✅ Clicked message area with selector: {selector}")
                            break
                        except Exception as e:
                            continue
                    
                    if message_clicked:
                        # Type the email content
                        await page.keyboard.type(email_body)
                        print("   ✅ Email body filled above signature")
                    else:
                        print("   ❌ Could not click message area automatically")
                        print("   Please manually click in the message area (above your signature)")
                        print("   Then press Enter to continue...")
                        input()
                        await page.keyboard.type(email_body)
                        print("   ✅ Email body filled manually")
                
                except Exception as e:
                    print(f"   ❌ Error filling email body: {e}")
                    print("   Please manually copy and paste the email content above your signature")
                
                # Handle PDF attachments
                if pdf_files:
                    print(f"\n📎 Ready to attach {len(pdf_files)} PDF files:")
                    for i, pdf_file in enumerate(pdf_files, 1):
                        print(f"   {i}. {Path(pdf_file).name}")
                    
                    print(f"\n📁 PDF files are in: {Path(pdf_files[0]).parent}")
                    print("   Please manually attach the PDFs:")
                    print("   1. Click the attachment button (📎) in Gmail")
                    print("   2. Navigate to the _temp_pdfs folder")
                    print("   3. Select all the PDF files")
                    print("   4. Click Open")
                    print("   Then press Enter to continue...")
                    input()
                
                print("\n🎉 Email setup complete!")
                print("📧 Gmail is ready with:")
                print(f"   - To: {recipient_email}")
                print(f"   - Subject: Utility Overages - {self.property_name}")
                print(f"   - Body: Pre-filled above your signature")
                print(f"   - Attachments: {len(pdf_files)} PDFs (ready to attach)")
                print("\n👆 Just click SEND when ready!")
                
                # Keep browser open
                print("\n⏳ Browser will stay open for you to send the email...")
                print("   (Press Ctrl+C to close when done)")
                
                try:
                    while True:
                        await page.wait_for_timeout(5000)
                except KeyboardInterrupt:
                    print("\n👋 Closing browser...")
                
            except Exception as e:
                print(f"❌ Error in Gmail automation: {e}")
                print("   Please try again")
            
            finally:
                await browser.close()
    
    async def run_automation(self):
        """Run the complete Gmail automation"""
        print("🚀 Gmail Fixed Automation")
        print("=" * 50)
        print("This version handles:")
        print("- Manual compose click after login")
        print("- Proper message placement above signature")
        print("- Manual PDF attachment")
        print("=" * 50)
        
        # Get recipient email
        recipient_email = input("Enter recipient email address: ").strip()
        if not recipient_email:
            recipient_email = "test@example.com"
            print(f"Using default email: {recipient_email}")
        
        # Download PDFs from Supabase
        pdf_files = await self.download_pdfs_from_supabase()
        
        if not pdf_files:
            print("❌ No PDFs to attach. Automation aborted.")
            return False
        
        # Open Gmail and fill email
        await self.open_gmail_and_fill_email(pdf_files, recipient_email)
        
        # Cleanup temp files
        temp_folder = Path("_temp_pdfs")
        if temp_folder.exists():
            import shutil
            shutil.rmtree(temp_folder)
            print("🧹 Cleaned up temporary files")
        
        print("✅ Automation completed!")
        return True

async def main():
    """Run the Gmail fixed automation"""
    automation = GmailFixedAutomation()
    await automation.run_automation()

if __name__ == "__main__":
    asyncio.run(main())

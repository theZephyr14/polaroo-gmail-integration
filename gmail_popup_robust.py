#!/usr/bin/env python3
"""
Gmail Popup Automation - Robust version with better error handling
"""

import asyncio
import os
import time
from pathlib import Path
from playwright.async_api import async_playwright
from src.pdf_storage import PDFStorage

class GmailPopupRobust:
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
    
    async def wait_for_gmail_load(self, page):
        """Wait for Gmail to fully load with multiple fallback strategies"""
        print("⏳ Waiting for Gmail to load...")
        
        # Try multiple selectors for compose button
        compose_selectors = [
            '[data-action="compose"]',
            '[aria-label*="Compose"]',
            '[aria-label*="compose"]',
            'div[role="button"][aria-label*="Compose"]',
            'div[role="button"][aria-label*="compose"]',
            'div[data-tooltip*="Compose"]',
            'div[data-tooltip*="compose"]'
        ]
        
        for i, selector in enumerate(compose_selectors):
            try:
                print(f"   Trying selector {i+1}/{len(compose_selectors)}: {selector}")
                await page.wait_for_selector(selector, timeout=10000)
                print(f"   ✅ Found compose button with selector: {selector}")
                return True
            except Exception as e:
                print(f"   ❌ Selector {i+1} failed: {e}")
                continue
        
        print("❌ Could not find compose button with any selector")
        return False
    
    async def open_gmail_popup_and_fill_email(self, pdf_files, recipient_email):
        """Open Gmail in popup browser and auto-fill email with attachments"""
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
                await page.wait_for_timeout(5000)
                
                # Wait for user to login if needed
                print("⏳ Please login to Gmail if prompted...")
                print("   (The browser will wait for you to complete login)")
                
                # Wait for Gmail to load completely with multiple strategies
                if not await self.wait_for_gmail_load(page):
                    print("❌ Gmail did not load properly. Please try again.")
                    return False
                
                print("✅ Gmail loaded successfully!")
                
                # Click Compose button with multiple strategies
                print("✍️ Clicking Compose...")
                compose_clicked = False
                
                compose_selectors = [
                    '[data-action="compose"]',
                    '[aria-label*="Compose"]',
                    '[aria-label*="compose"]',
                    'div[role="button"][aria-label*="Compose"]',
                    'div[role="button"][aria-label*="compose"]'
                ]
                
                for selector in compose_selectors:
                    try:
                        await page.click(selector)
                        compose_clicked = True
                        print(f"   ✅ Compose clicked with selector: {selector}")
                        break
                    except Exception as e:
                        print(f"   ❌ Compose click failed with {selector}: {e}")
                        continue
                
                if not compose_clicked:
                    print("❌ Could not click compose button")
                    return False
                
                await page.wait_for_timeout(3000)
                
                # Wait for compose window to open
                print("⏳ Waiting for compose window...")
                try:
                    await page.wait_for_selector('[name="to"]', timeout=15000)
                    print("   ✅ Compose window opened")
                except Exception as e:
                    print(f"   ❌ Compose window did not open: {e}")
                    return False
                
                # Fill in recipient
                print(f"📝 Filling recipient: {recipient_email}")
                await page.fill('[name="to"]', recipient_email)
                await page.wait_for_timeout(1000)
                
                # Fill subject
                subject = f"Utility Overages - {self.property_name}"
                print(f"📝 Filling subject: {subject}")
                await page.fill('[name="subjectbox"]', subject)
                await page.wait_for_timeout(1000)
                
                # Fill email body with template
                print("📝 Filling email body...")
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
                
                # Click in message body and type
                try:
                    await page.click('[role="textbox"]')
                    await page.keyboard.type(email_body)
                    print("   ✅ Email body filled")
                except Exception as e:
                    print(f"   ❌ Failed to fill email body: {e}")
                    # Try alternative method
                    try:
                        await page.click('div[aria-label*="Message Body"]')
                        await page.keyboard.type(email_body)
                        print("   ✅ Email body filled (alternative method)")
                    except Exception as e2:
                        print(f"   ❌ Alternative method failed: {e2}")
                
                await page.wait_for_timeout(2000)
                
                # Attach PDF files
                if pdf_files:
                    print(f"📎 Attaching {len(pdf_files)} PDF files...")
                    
                    for i, pdf_file in enumerate(pdf_files, 1):
                        try:
                            print(f"   📎 Attaching {i}/{len(pdf_files)}: {Path(pdf_file).name}")
                            
                            # Try multiple attachment methods
                            attachment_clicked = False
                            attachment_selectors = [
                                '[data-tooltip="Attach files"]',
                                '[aria-label*="Attach"]',
                                '[aria-label*="attach"]',
                                'div[role="button"][aria-label*="Attach"]',
                                'div[role="button"][aria-label*="attach"]'
                            ]
                            
                            for selector in attachment_selectors:
                                try:
                                    await page.click(selector)
                                    attachment_clicked = True
                                    print(f"      ✅ Attachment button clicked with: {selector}")
                                    break
                                except Exception as e:
                                    print(f"      ❌ Attachment click failed with {selector}: {e}")
                                    continue
                            
                            if not attachment_clicked:
                                print(f"   ❌ Could not click attachment button for {Path(pdf_file).name}")
                                continue
                            
                            await page.wait_for_timeout(1000)
                            
                            # Handle file picker
                            try:
                                async with page.expect_file_chooser() as fc_info:
                                    file_chooser = await fc_info.value
                                    await file_chooser.set_files(pdf_file)
                                
                                # Wait for attachment to process
                                await page.wait_for_timeout(3000)
                                print(f"   ✅ Attached: {Path(pdf_file).name}")
                                
                            except Exception as e:
                                print(f"   ❌ File picker failed for {Path(pdf_file).name}: {e}")
                            
                        except Exception as e:
                            print(f"   ❌ Failed to attach {Path(pdf_file).name}: {e}")
                
                print("\n🎉 Email is ready!")
                print("📧 Gmail popup window is open with:")
                print(f"   - To: {recipient_email}")
                print(f"   - Subject: {subject}")
                print(f"   - Body: Pre-filled with template")
                print(f"   - Attachments: {len(pdf_files)} PDFs")
                print("\n👆 Just click the SEND button in Gmail when ready!")
                
                # Keep browser open for user to send
                print("\n⏳ Browser will stay open for you to send the email...")
                print("   (Press Ctrl+C to close when done)")
                
                # Wait indefinitely until user closes or sends
                try:
                    while True:
                        await page.wait_for_timeout(5000)
                        # Check if email was sent (compose window closed)
                        try:
                            await page.wait_for_selector('[data-action="compose"]', timeout=1000)
                            # Compose button is visible again, email might have been sent
                            print("📤 Email appears to have been sent!")
                            break
                        except:
                            # Compose window still open, continue waiting
                            pass
                except KeyboardInterrupt:
                    print("\n👋 Closing browser...")
                
            except Exception as e:
                print(f"❌ Error in Gmail automation: {e}")
                print("   Please try again or check your Gmail login")
            
            finally:
                await browser.close()
    
    async def run_automation(self):
        """Run the complete Gmail popup automation"""
        print("🚀 Gmail Popup Automation (Robust Version)")
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
        
        # Open Gmail popup and fill email
        await self.open_gmail_popup_and_fill_email(pdf_files, recipient_email)
        
        # Cleanup temp files
        temp_folder = Path("_temp_pdfs")
        if temp_folder.exists():
            import shutil
            shutil.rmtree(temp_folder)
            print("🧹 Cleaned up temporary files")
        
        print("✅ Automation completed!")
        return True

async def main():
    """Run the Gmail popup automation"""
    automation = GmailPopupRobust()
    await automation.run_automation()

if __name__ == "__main__":
    asyncio.run(main())

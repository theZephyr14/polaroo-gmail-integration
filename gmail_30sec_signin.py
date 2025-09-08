#!/usr/bin/env python3
"""
Gmail 30-Second Sign-in Automation
"""

import asyncio
import os
import time
from pathlib import Path
from playwright.async_api import async_playwright
from src.pdf_storage import PDFStorage

class Gmail30SecSignin:
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
    
    async def open_gmail_with_30sec_signin(self, pdf_files, recipient_email):
        """Open Gmail with 30-second sign-in window"""
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
                await page.wait_for_timeout(2000)
                
                # Give user 30 seconds to sign in
                print("⏳ You have 30 seconds to sign in to Gmail...")
                print("   (The browser window is open - please sign in now)")
                
                # Countdown timer
                for i in range(30, 0, -1):
                    print(f"   ⏰ {i} seconds remaining...", end='\r')
                    await page.wait_for_timeout(1000)
                
                print("\n✅ 30 seconds elapsed - continuing with automation...")
                
                # Wait a bit more for Gmail to fully load after sign-in
                await page.wait_for_timeout(3000)
                
                # Try to find compose button with multiple strategies
                print("🔍 Looking for compose button...")
                compose_found = False
                
                # Try clicking compose with multiple selectors
                compose_selectors = [
                    '[data-action="compose"]',
                    '[aria-label*="Compose"]',
                    '[aria-label*="compose"]',
                    'div[role="button"][aria-label*="Compose"]',
                    'div[role="button"][aria-label*="compose"]',
                    'div[data-tooltip*="Compose"]',
                    'div[data-tooltip*="compose"]',
                    'div[jsname="V67aGc"]',  # Another common Gmail compose selector
                    'div[jsname="V67aGc"][role="button"]'
                ]
                
                for i, selector in enumerate(compose_selectors):
                    try:
                        print(f"   Trying compose selector {i+1}/{len(compose_selectors)}...")
                        await page.click(selector, timeout=5000)
                        compose_found = True
                        print(f"   ✅ Compose clicked successfully!")
                        break
                    except Exception as e:
                        print(f"   ❌ Selector {i+1} failed: {str(e)[:50]}...")
                        continue
                
                if not compose_found:
                    print("❌ Could not find compose button automatically")
                    print("   Please manually click the 'Compose' button in Gmail")
                    print("   Then press Enter to continue...")
                    input()
                
                # Wait for compose window
                print("⏳ Waiting for compose window to open...")
                await page.wait_for_timeout(3000)
                
                # Try to fill recipient
                try:
                    print(f"📝 Filling recipient: {recipient_email}")
                    await page.fill('[name="to"]', recipient_email)
                    print("   ✅ Recipient filled")
                except Exception as e:
                    print(f"   ❌ Could not fill recipient automatically: {e}")
                    print(f"   Please manually enter recipient: {recipient_email}")
                
                # Try to fill subject
                try:
                    subject = f"Utility Overages - {self.property_name}"
                    print(f"📝 Filling subject: {subject}")
                    await page.fill('[name="subjectbox"]', subject)
                    print("   ✅ Subject filled")
                except Exception as e:
                    print(f"   ❌ Could not fill subject automatically: {e}")
                    print(f"   Please manually enter subject: {subject}")
                
                # Try to fill email body
                try:
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
                    
                    # Try multiple ways to fill the body
                    try:
                        await page.click('[role="textbox"]')
                        await page.keyboard.type(email_body)
                        print("   ✅ Email body filled")
                    except:
                        try:
                            await page.click('div[aria-label*="Message Body"]')
                            await page.keyboard.type(email_body)
                            print("   ✅ Email body filled (alternative)")
                        except:
                            print("   ❌ Could not fill email body automatically")
                            print("   Please manually copy and paste the email body:")
                            print("   " + "="*50)
                            print(email_body)
                            print("   " + "="*50)
                
                except Exception as e:
                    print(f"   ❌ Error filling email body: {e}")
                
                # Handle PDF attachments
                if pdf_files:
                    print(f"\n📎 PDF files are ready for attachment:")
                    for i, pdf_file in enumerate(pdf_files, 1):
                        print(f"   {i}. {Path(pdf_file).name}")
                    
                    print(f"\n📁 PDF files are located in: {Path(pdf_files[0]).parent}")
                    print("   Please manually attach these PDFs to your email:")
                    print("   1. Click the attachment button (📎) in Gmail")
                    print("   2. Navigate to the _temp_pdfs folder")
                    print("   3. Select all the PDF files")
                    print("   4. Click Open")
                
                print("\n🎉 Email setup complete!")
                print("📧 Gmail is ready with:")
                print(f"   - To: {recipient_email}")
                print(f"   - Subject: Utility Overages - {self.property_name}")
                print(f"   - Body: Pre-filled template")
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
        """Run the complete Gmail automation with 30-second sign-in"""
        print("🚀 Gmail 30-Second Sign-in Automation")
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
        
        # Open Gmail with 30-second sign-in
        await self.open_gmail_with_30sec_signin(pdf_files, recipient_email)
        
        # Cleanup temp files
        temp_folder = Path("_temp_pdfs")
        if temp_folder.exists():
            import shutil
            shutil.rmtree(temp_folder)
            print("🧹 Cleaned up temporary files")
        
        print("✅ Automation completed!")
        return True

async def main():
    """Run the Gmail 30-second sign-in automation"""
    automation = Gmail30SecSignin()
    await automation.run_automation()

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Auto Gmail Demo
==============

Automatically logs into Gmail and creates emails with generated content.
Supports multiple authentication methods.
"""

import time
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutoGmailDemo:
    def __init__(self):
        self.driver = None
        self.email_generator = None
        self.generated_emails = []
        
    def setup_browser(self, headless=False):
        """Set up Chrome browser with options."""
        print("🌐 Setting up browser...")
        
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add user data directory to persist login
        user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✅ Browser setup complete!")
            return True
        except Exception as e:
            print(f"❌ Failed to setup browser: {e}")
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
    
    def load_credentials(self):
        """Load credentials from .env file or environment variables."""
        # Try .env file first
        env_file = Path('.env')
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('GMAIL_EMAIL='):
                        email = line.split('=', 1)[1].strip()
                    elif line.startswith('GMAIL_PASSWORD='):
                        password = line.split('=', 1)[1].strip()
            return email, password
        
        # Fall back to environment variables
        return os.getenv('GMAIL_EMAIL'), os.getenv('GMAIL_PASSWORD')
    
    def auto_login_gmail(self):
        """Automatically log into Gmail using stored credentials."""
        print("🔐 Attempting automatic Gmail login...")
        
        try:
            # Go to Gmail
            self.driver.get("https://gmail.com")
            time.sleep(3)
            
            # Check if already logged in
            if self.is_logged_in():
                print("✅ Already logged in to Gmail!")
                return True
            
            # Try to get credentials
            email, password = self.load_credentials()
            
            if not email or not password:
                print("❌ Gmail credentials not found")
                print("   Please run: python setup_gmail_credentials.py")
                print("   Or set GMAIL_EMAIL and GMAIL_PASSWORD environment variables")
                return False
            
            print(f"📧 Logging in as: {email}")
            
            # Find email input field
            email_selectors = [
                "input[type='email']",
                "input[name='identifier']",
                "input[aria-label*='email']",
                "#identifierId"
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not email_field:
                print("❌ Could not find email input field")
                return False
            
            # Enter email
            email_field.clear()
            email_field.send_keys(email)
            email_field.send_keys(Keys.RETURN)
            print("✅ Email entered")
            
            time.sleep(3)
            
            # Find password input field
            password_selectors = [
                "input[type='password']",
                "input[name='password']",
                "input[aria-label*='password']",
                "#password"
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not password_field:
                print("❌ Could not find password input field")
                return False
            
            # Enter password
            password_field.clear()
            password_field.send_keys(password)
            password_field.send_keys(Keys.RETURN)
            print("✅ Password entered")
            
            # Wait for login to complete
            time.sleep(5)
            
            if self.is_logged_in():
                print("✅ Successfully logged in to Gmail!")
                return True
            else:
                print("❌ Login failed - please check credentials")
                return False
                
        except Exception as e:
            print(f"❌ Auto login failed: {e}")
            return False
    
    def is_logged_in(self):
        """Check if user is logged into Gmail."""
        try:
            # Look for Gmail interface elements that indicate login
            gmail_indicators = [
                "[data-tooltip='Compose']",
                "[aria-label='Compose']",
                "div[role='button'][aria-label*='Compose']",
                ".T-I.T-I-KE.L3"
            ]
            
            for selector in gmail_indicators:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed():
                        return True
                except:
                    continue
            
            return False
        except:
            return False
    
    def manual_login_gmail(self):
        """Open Gmail and wait for manual login."""
        print("📧 Opening Gmail for manual login...")
        
        try:
            self.driver.get("https://gmail.com")
            print("✅ Gmail opened successfully!")
            
            print("\n" + "="*60)
            print("🔐 MANUAL LOGIN REQUIRED")
            print("="*60)
            print("1. The browser window should now show Gmail")
            print("2. Please log in with your Google account")
            print("3. Wait for Gmail to fully load")
            print("4. Then come back here and press Enter")
            print("="*60)
            
            input("\nPress Enter when you're logged in and Gmail is ready...")
            
            if self.is_logged_in():
                print("✅ Gmail login confirmed!")
                return True
            else:
                print("❌ Gmail login not detected")
                return False
                
        except Exception as e:
            print(f"❌ Failed to open Gmail: {e}")
            return False
    
    def create_email(self, email_data, email_num):
        """Create a single email in Gmail."""
        print(f"\n📝 Creating Email {email_num}: {email_data['property_name']}")
        print(f"   💰 Amount: €{email_data['total_extra']:.2f}")
        
        try:
            # Look for compose button
            compose_selectors = [
                "[data-tooltip='Compose']",
                "[aria-label='Compose']",
                "div[role='button'][aria-label*='Compose']",
                "div[jsname='V67aGc']",
                ".T-I.T-I-KE.L3"
            ]
            
            compose_button = None
            for selector in compose_selectors:
                try:
                    compose_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if compose_button.is_displayed():
                        print(f"   ✅ Found compose button")
                        break
                except:
                    continue
            
            if not compose_button:
                print("   ❌ Could not find compose button")
                return False
            
            # Click compose button
            compose_button.click()
            print("   ✅ Compose button clicked")
            time.sleep(3)
            
            # Fill recipient
            to_selectors = [
                "input[aria-label='To']",
                "input[aria-label='Recipients']",
                "input[placeholder*='To']"
            ]
            
            to_field = None
            for selector in to_selectors:
                try:
                    to_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if to_field.is_displayed():
                        break
                except:
                    continue
            
            if to_field:
                to_field.clear()
                to_field.send_keys(email_data['email_address'])
                print(f"   ✅ Recipient: {email_data['email_address']}")
            
            # Fill subject
            subject_selectors = [
                "input[aria-label='Subject']",
                "input[placeholder*='Subject']"
            ]
            
            subject_field = None
            for selector in subject_selectors:
                try:
                    subject_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if subject_field.is_displayed():
                        break
                except:
                    continue
            
            if subject_field:
                subject_field.clear()
                subject_field.send_keys(email_data['subject'])
                print(f"   ✅ Subject: {email_data['subject']}")
            
            # Fill body
            body_selectors = [
                "div[aria-label='Message Body']",
                "div[contenteditable='true']",
                "div[role='textbox']"
            ]
            
            body_field = None
            for selector in body_selectors:
                try:
                    body_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if body_field.is_displayed():
                        break
                except:
                    continue
            
            if body_field:
                body_field.click()
                body_field.clear()
                body_field.send_keys(email_data['body'])
                print("   ✅ Email body filled")
            
            print(f"   📧 Email {email_num} ready!")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to create email: {e}")
            return False
    
    def run_demo(self, auto_login=True):
        """Run the complete demo."""
        print("🚀 Auto Gmail Demo")
        print("=" * 50)
        
        # Setup
        if not self.setup_browser():
            return False
        
        if not self.setup_email_system():
            return False
        
        if not self.generate_emails():
            print("❌ No emails generated, cannot continue")
            return False
        
        # Login to Gmail
        if auto_login:
            if not self.auto_login_gmail():
                print("🔄 Auto login failed, trying manual login...")
                if not self.manual_login_gmail():
                    print("❌ Login failed, cannot continue")
                    return False
        else:
            if not self.manual_login_gmail():
                print("❌ Login failed, cannot continue")
                return False
        
        # Create emails
        for i, email_data in enumerate(self.generated_emails, 1):
            print(f"\n📧 Creating Email {i} of {len(self.generated_emails)}")
            
            if self.create_email(email_data, i):
                print(f"✅ Email {i} created successfully!")
                
                if i < len(self.generated_emails):
                    input(f"\nPress Enter to create email {i+1}...")
                else:
                    print(f"\n🎉 All {len(self.generated_emails)} emails created!")
            else:
                print(f"❌ Failed to create email {i}")
        
        print("\n📧 Demo completed!")
        print("   All emails have been created in Gmail")
        print("   You can now review, edit, and send them manually")
        
        input("\nPress Enter to close the browser...")
        return True
    
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()
            print("🧹 Browser closed")

def main():
    """Run the auto Gmail demo."""
    demo = AutoGmailDemo()
    
    try:
        # Check if credentials are available
        email = os.getenv('GMAIL_EMAIL')
        password = os.getenv('GMAIL_PASSWORD')
        
        if email and password:
            print("🔐 Gmail credentials found, using auto login")
            success = demo.run_demo(auto_login=True)
        else:
            print("🔐 No Gmail credentials found, using manual login")
            print("   To enable auto login, set these environment variables:")
            print("   GMAIL_EMAIL=your-email@gmail.com")
            print("   GMAIL_PASSWORD=your-app-password")
            print("   (Use App Password, not your regular password)")
            success = demo.run_demo(auto_login=False)
        
        if success:
            print("\n✅ Demo completed successfully!")
        else:
            print("\n❌ Demo failed!")
            
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
    finally:
        demo.cleanup()

if __name__ == "__main__":
    main()

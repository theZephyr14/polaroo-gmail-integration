#!/usr/bin/env python3
"""
Email Browser Demo
=================

Automatically opens Gmail in browser and fills out emails with generated content.
This demonstrates the email system by actually creating emails in Gmail.
"""

import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EmailBrowserDemo:
    def __init__(self):
        self.driver = None
        self.email_generator = None
        self.email_sender = None
        self.generated_emails = []
        
    def setup_browser(self):
        """Set up Chrome browser with options."""
        print("🌐 Setting up browser...")
        
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✅ Browser setup complete!")
            return True
        except Exception as e:
            print(f"❌ Failed to setup browser: {e}")
            print("Make sure ChromeDriver is installed and in PATH")
            return False
    
    def setup_email_system(self):
        """Initialize the email system components."""
        try:
            from src.email_system.email_generator import EmailGenerator
            from src.email_system.email_sender import EmailSender
            
            self.email_generator = EmailGenerator("email_templates.xlsx")
            self.email_sender = EmailSender(offline_mode=True)
            
            print("✅ Email system initialized!")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize email system: {e}")
            return False
    
    def generate_sample_emails(self):
        """Generate sample emails for demonstration."""
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
    
    def open_gmail(self):
        """Open Gmail in the browser."""
        print("📧 Opening Gmail...")
        
        try:
            self.driver.get("https://gmail.com")
            print("✅ Gmail opened successfully!")
            
            # Wait for Gmail to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )
            
            print("⏳ Gmail is loading... Please log in manually if needed.")
            print("   (The script will wait for you to log in)")
            
            # Wait for user to log in - look for various Gmail elements
            print("🔍 Waiting for Gmail to be ready...")
            try:
                # Try multiple selectors for compose button
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
                        compose_button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        print(f"✅ Found compose button with selector: {selector}")
                        break
                    except TimeoutException:
                        continue
                
                if compose_button:
                    print("✅ Gmail is ready!")
                    return True
                else:
                    print("⏰ Could not find compose button")
                    print("   Please make sure you're logged in and Gmail is fully loaded")
                    return False
                    
            except Exception as e:
                print(f"⏰ Error waiting for Gmail: {e}")
                print("   Please make sure you're logged in and try again")
                return False
                
        except Exception as e:
            print(f"❌ Failed to open Gmail: {e}")
            return False
    
    def create_new_email(self, email_data):
        """Create a new email in Gmail with the provided data."""
        print(f"\n📝 Creating email for {email_data['property_name']}...")
        
        try:
            # Try multiple selectors for compose button
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
                    compose_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if not compose_button:
                print("   ❌ Could not find compose button")
                return False
            
            compose_button.click()
            print("   ✅ Compose button clicked")
            
            # Wait for compose window to open
            time.sleep(3)
            
            # Try multiple selectors for recipient field
            to_selectors = [
                "input[aria-label='To']",
                "input[aria-label='Recipients']",
                "input[placeholder*='To']",
                "div[aria-label='To'] input"
            ]
            
            to_field = None
            for selector in to_selectors:
                try:
                    to_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue
            
            if to_field:
                to_field.clear()
                to_field.send_keys(email_data['email_address'])
                print(f"   ✅ Recipient filled: {email_data['email_address']}")
            else:
                print("   ⚠️  Could not find recipient field, continuing...")
            
            # Try multiple selectors for subject field
            subject_selectors = [
                "input[aria-label='Subject']",
                "input[placeholder*='Subject']",
                "div[aria-label='Subject'] input"
            ]
            
            subject_field = None
            for selector in subject_selectors:
                try:
                    subject_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if subject_field:
                subject_field.clear()
                subject_field.send_keys(email_data['subject'])
                print(f"   ✅ Subject filled: {email_data['subject']}")
            else:
                print("   ⚠️  Could not find subject field, continuing...")
            
            # Try multiple selectors for body field
            body_selectors = [
                "div[aria-label='Message Body']",
                "div[contenteditable='true']",
                "div[role='textbox']",
                "div[data-send-message] div[contenteditable]"
            ]
            
            body_field = None
            for selector in body_selectors:
                try:
                    body_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if body_field:
                body_field.click()
                body_field.clear()
                body_field.send_keys(email_data['body'])
                print("   ✅ Email body filled")
            else:
                print("   ⚠️  Could not find body field, continuing...")
            
            print(f"   📧 Email ready for {email_data['property_name']}")
            print(f"   💰 Amount: €{email_data['total_extra']:.2f}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to create email: {e}")
            return False
    
    def wait_for_user(self, message="Press Enter to continue..."):
        """Wait for user input."""
        input(f"\n⏸️  {message}")
    
    def run_demo(self):
        """Run the complete browser demo."""
        print("🚀 Starting Email Browser Demo")
        print("=" * 50)
        
        # Setup
        if not self.setup_browser():
            return False
        
        if not self.setup_email_system():
            return False
        
        if not self.generate_sample_emails():
            print("❌ No emails generated, cannot continue")
            return False
        
        # Open Gmail
        if not self.open_gmail():
            return False
        
        # Create emails
        for i, email_data in enumerate(self.generated_emails, 1):
            print(f"\n📧 Creating Email {i} of {len(self.generated_emails)}")
            
            if self.create_new_email(email_data):
                print(f"✅ Email {i} created successfully!")
                
                if i < len(self.generated_emails):
                    self.wait_for_user("Email created! Press Enter to create the next email...")
                else:
                    self.wait_for_user("All emails created! Press Enter to finish...")
            else:
                print(f"❌ Failed to create email {i}")
        
        print("\n🎉 Demo completed!")
        print("📧 All emails have been created in Gmail")
        print("   You can now review, edit, and send them manually")
        
        self.wait_for_user("Press Enter to close the browser...")
        
        return True
    
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()
            print("🧹 Browser closed")

def main():
    """Run the browser demo."""
    demo = EmailBrowserDemo()
    
    try:
        success = demo.run_demo()
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


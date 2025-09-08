#!/usr/bin/env python3
"""
Simple Gmail Demo
================

Opens Gmail and waits for you to log in, then creates emails automatically.
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

def setup_browser():
    """Set up Chrome browser."""
    print("🌐 Setting up browser...")
    
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✅ Browser setup complete!")
        return driver
    except Exception as e:
        print(f"❌ Failed to setup browser: {e}")
        return None

def generate_emails():
    """Generate sample emails."""
    print("📧 Generating sample emails...")
    
    try:
        from src.email_system.email_generator import EmailGenerator
        
        email_generator = EmailGenerator("email_templates.xlsx")
        
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
        
        emails = []
        for i, property_data in enumerate(properties, 1):
            print(f"\n🏠 Processing Property {i}: {property_data['name']}")
            print(f"   - Electricity: €{property_data['elec_cost']:.2f}")
            print(f"   - Water: €{property_data['water_cost']:.2f}")
            print(f"   - Allowance: €{property_data['allowance']:.2f}")
            print(f"   - Total Extra: €{property_data['total_extra']:.2f}")
            
            email_data = email_generator.generate_email_for_property(property_data)
            if email_data:
                emails.append(email_data)
                print(f"   ✅ Email generated (ID: {email_data['id'][:8]}...)")
            else:
                print(f"   ⏭️  No email generated")
        
        print(f"\n✅ Generated {len(emails)} emails")
        return emails
        
    except Exception as e:
        print(f"❌ Failed to generate emails: {e}")
        return []

def open_gmail(driver):
    """Open Gmail and wait for user to log in."""
    print("📧 Opening Gmail...")
    
    try:
        driver.get("https://gmail.com")
        print("✅ Gmail opened successfully!")
        
        print("\n" + "="*60)
        print("🔐 PLEASE LOG IN TO GMAIL MANUALLY")
        print("="*60)
        print("1. The browser window should now show Gmail")
        print("2. Please log in with your Google account")
        print("3. Wait for Gmail to fully load")
        print("4. Then come back here and press Enter")
        print("="*60)
        
        input("\nPress Enter when you're logged in and Gmail is ready...")
        
        print("✅ Continuing with email creation...")
        return True
        
    except Exception as e:
        print(f"❌ Failed to open Gmail: {e}")
        return False

def create_email(driver, email_data, email_num):
    """Create a single email in Gmail."""
    print(f"\n📝 Creating Email {email_num}: {email_data['property_name']}")
    print(f"   💰 Amount: €{email_data['total_extra']:.2f}")
    
    try:
        # Look for compose button with multiple selectors
        compose_selectors = [
            "[data-tooltip='Compose']",
            "[aria-label='Compose']",
            "div[role='button'][aria-label*='Compose']",
            "div[jsname='V67aGc']",
            ".T-I.T-I-KE.L3",
            "div[aria-label='Compose']"
        ]
        
        compose_button = None
        for selector in compose_selectors:
            try:
                compose_button = driver.find_element(By.CSS_SELECTOR, selector)
                if compose_button.is_displayed():
                    print(f"   ✅ Found compose button: {selector}")
                    break
            except:
                continue
        
        if not compose_button:
            print("   ❌ Could not find compose button")
            print("   Please make sure Gmail is fully loaded and try again")
            return False
        
        # Click compose button
        compose_button.click()
        print("   ✅ Compose button clicked")
        
        # Wait for compose window
        time.sleep(3)
        
        # Fill recipient
        to_selectors = [
            "input[aria-label='To']",
            "input[aria-label='Recipients']",
            "input[placeholder*='To']",
            "div[aria-label='To'] input"
        ]
        
        to_field = None
        for selector in to_selectors:
            try:
                to_field = driver.find_element(By.CSS_SELECTOR, selector)
                if to_field.is_displayed():
                    break
            except:
                continue
        
        if to_field:
            to_field.clear()
            to_field.send_keys(email_data['email_address'])
            print(f"   ✅ Recipient: {email_data['email_address']}")
        else:
            print("   ⚠️  Could not find recipient field")
        
        # Fill subject
        subject_selectors = [
            "input[aria-label='Subject']",
            "input[placeholder*='Subject']",
            "div[aria-label='Subject'] input"
        ]
        
        subject_field = None
        for selector in subject_selectors:
            try:
                subject_field = driver.find_element(By.CSS_SELECTOR, selector)
                if subject_field.is_displayed():
                    break
            except:
                continue
        
        if subject_field:
            subject_field.clear()
            subject_field.send_keys(email_data['subject'])
            print(f"   ✅ Subject: {email_data['subject']}")
        else:
            print("   ⚠️  Could not find subject field")
        
        # Fill body
        body_selectors = [
            "div[aria-label='Message Body']",
            "div[contenteditable='true']",
            "div[role='textbox']",
            "div[data-send-message] div[contenteditable]"
        ]
        
        body_field = None
        for selector in body_selectors:
            try:
                body_field = driver.find_element(By.CSS_SELECTOR, selector)
                if body_field.is_displayed():
                    break
            except:
                continue
        
        if body_field:
            body_field.click()
            body_field.clear()
            body_field.send_keys(email_data['body'])
            print("   ✅ Email body filled")
        else:
            print("   ⚠️  Could not find body field")
        
        print(f"   📧 Email {email_num} ready!")
        print(f"   You can now review and send it manually")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to create email: {e}")
        return False

def main():
    """Run the simple Gmail demo."""
    print("🚀 Simple Gmail Demo")
    print("=" * 50)
    
    # Setup browser
    driver = setup_browser()
    if not driver:
        return
    
    try:
        # Generate emails
        emails = generate_emails()
        if not emails:
            print("❌ No emails generated, cannot continue")
            return
        
        # Open Gmail
        if not open_gmail(driver):
            return
        
        # Create emails
        for i, email_data in enumerate(emails, 1):
            print(f"\n📧 Creating Email {i} of {len(emails)}")
            
            if create_email(driver, email_data, i):
                print(f"✅ Email {i} created successfully!")
                
                if i < len(emails):
                    input(f"\nPress Enter to create email {i+1}...")
                else:
                    print(f"\n🎉 All {len(emails)} emails created!")
            else:
                print(f"❌ Failed to create email {i}")
        
        print("\n📧 Demo completed!")
        print("   All emails have been created in Gmail")
        print("   You can now review, edit, and send them manually")
        
        input("\nPress Enter to close the browser...")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
    finally:
        driver.quit()
        print("🧹 Browser closed")

if __name__ == "__main__":
    main()

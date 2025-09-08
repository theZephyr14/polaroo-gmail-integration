#!/usr/bin/env python3
"""
Email System Demo
================

A simple demonstration of the email system functionality.
This script shows how to generate and send emails for utility bill overages.
"""

import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_email_system():
    """Demonstrate the email system functionality."""
    print("🚀 EMAIL SYSTEM DEMO")
    print("=" * 50)
    
    try:
        # Import email system components
        from src.email_system.email_generator import EmailGenerator
        from src.email_system.email_sender import EmailSender
        from src.email_system.template_manager import TemplateManager
        
        print("\n📧 Setting up email system...")
        
        # Initialize components
        email_generator = EmailGenerator("email_templates.xlsx")
        email_sender = EmailSender(offline_mode=True)  # Offline mode for demo
        
        print("✅ Email system initialized successfully!")
        
        # Create sample property data
        print("\n🏠 Creating sample property data...")
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
            },
            {
                'name': 'No Overage Property',
                'elec_cost': 30.00,
                'water_cost': 15.00,
                'allowance': 50.0,
                'total_extra': -5.00,  # No overage
                'payment_link': 'https://payment.example.com/no-overage'
            }
        ]
        
        print(f"✅ Created {len(properties)} sample properties")
        
        # Generate emails for all properties
        print("\n📝 Generating emails...")
        generated_emails = []
        
        for i, property_data in enumerate(properties, 1):
            print(f"\n   Property {i}: {property_data['name']}")
            print(f"   - Electricity: €{property_data['elec_cost']:.2f}")
            print(f"   - Water: €{property_data['water_cost']:.2f}")
            print(f"   - Allowance: €{property_data['allowance']:.2f}")
            print(f"   - Total Extra: €{property_data['total_extra']:.2f}")
            
            email_data = email_generator.generate_email_for_property(property_data)
            if email_data:
                generated_emails.append(email_data)
                print(f"   ✅ Email generated (ID: {email_data['id'][:8]}...)")
            else:
                print(f"   ⏭️  No email generated (no overage or error)")
        
        print(f"\n✅ Generated {len(generated_emails)} emails")
        
        # Show email previews
        print("\n📋 EMAIL PREVIEWS:")
        print("=" * 50)
        
        for i, email_data in enumerate(generated_emails, 1):
            print(f"\n📧 Email {i}: {email_data['property_name']}")
            print("-" * 30)
            print(f"To: {email_data['email_address']}")
            print(f"Subject: {email_data['subject']}")
            print(f"Total Extra: €{email_data['total_extra']:.2f}")
            print("\nBody Preview:")
            # Show first few lines of body
            body_lines = email_data['body'].split('\n')
            for line in body_lines[:8]:  # Show first 8 lines
                if line.strip():
                    print(f"  {line}")
            if len(body_lines) > 8:
                print("  ...")
        
        # Test email sending workflow
        print("\n📤 TESTING EMAIL SENDING WORKFLOW:")
        print("=" * 50)
        
        if generated_emails:
            # Test approval workflow
            print("\n1. Testing approval workflow...")
            email_data = generated_emails[0]
            
            # Queue for approval
            send_result = email_sender.send_email(email_data, require_approval=True)
            if send_result['success']:
                print(f"   ✅ Email queued for approval")
                print(f"   Status: {send_result['status']}")
                
                # Show pending approvals
                pending = email_sender.get_pending_approvals()
                print(f"   Pending approvals: {len(pending)}")
                
                # Approve the email
                print("\n   Approving email...")
                approval_result = email_sender.approve_email(email_data['id'])
                if approval_result['success']:
                    print(f"   ✅ Email approved and sent!")
                    print(f"   Status: {approval_result['status']}")
                    print(f"   Sent at: {approval_result.get('sent_at', 'N/A')}")
                else:
                    print(f"   ❌ Failed to approve: {approval_result.get('error')}")
            
            # Test direct sending
            print("\n2. Testing direct sending...")
            if len(generated_emails) > 1:
                email_data2 = generated_emails[1]
                send_result2 = email_sender.send_email(email_data2, require_approval=False)
                if send_result2['success']:
                    print(f"   ✅ Email sent directly!")
                    print(f"   Status: {send_result2['status']}")
                else:
                    print(f"   ❌ Failed to send: {send_result2.get('error')}")
        
        # Show final statistics
        print("\n📊 FINAL STATISTICS:")
        print("=" * 50)
        stats = email_sender.get_email_statistics()
        print(f"Pending approvals: {stats['pending_approvals']}")
        print(f"Sent emails: {stats['sent_emails']}")
        print(f"Total emails: {stats['total_emails']}")
        print(f"Offline mode: {stats['offline_mode']}")
        
        print("\n🎉 EMAIL SYSTEM DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ DEMO FAILED: {e}")
        logger.error(f"Demo error: {e}", exc_info=True)
        return False

def main():
    """Run the email system demo."""
    print("🚀 Starting Email System Demo...")
    print(f"Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = demo_email_system()
    
    print(f"\nDemo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    
    return success

if __name__ == "__main__":
    main()

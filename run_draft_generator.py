#!/usr/bin/env python3
"""
Gmail Draft Generator Runner
============================

Simple script to run the Gmail Draft Generator with different modes.
Provides an easy interface to choose between single or batch draft creation.
"""

import sys
import os
from pathlib import Path

def show_menu():
    """Show the main menu."""
    print("🚀 Gmail Draft Generator")
    print("=" * 40)
    print("Choose your option:")
    print("1. Create single draft (manual recipient)")
    print("2. Create batch drafts (from Excel file)")
    print("3. List existing drafts")
    print("4. Help & Setup")
    print("5. Exit")
    print("=" * 40)

def show_help():
    """Show help and setup information."""
    print("\n📚 Gmail Draft Generator Help")
    print("=" * 40)
    
    print("\n🔧 Setup Requirements:")
    print("1. Gmail API credentials (credentials.json)")
    print("2. Python packages: google-api-python-client, google-auth-httplib2, google-auth-oauthlib")
    print("3. Supabase configuration (for PDF attachments)")
    print("4. Excel file with recipient data (for batch mode)")
    
    print("\n📁 Expected Files:")
    print("- credentials.json (Gmail API credentials)")
    print("- Book1.xlsx (recipient data for batch mode)")
    print("- token.json (auto-generated after first OAuth)")
    
    print("\n📊 Excel File Format (for batch mode):")
    print("Required columns:")
    print("- property_name: Name of the property")
    print("- email_address: Recipient email address")
    print("Optional columns:")
    print("- total_extra: Amount owed")
    print("- electricity_amount: Electricity bill amount")
    print("- water_amount: Water bill amount")
    print("- notes: Additional notes")
    
    print("\n🔗 Gmail API Setup:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create project and enable Gmail API")
    print("3. Create OAuth 2.0 credentials (Desktop application)")
    print("4. Download credentials.json to this folder")
    
    print("\n💡 Tips:")
    print("- Drafts are created, not sent automatically")
    print("- Review all drafts before sending")
    print("- PDFs are automatically attached from Supabase")
    print("- Use batch mode for multiple recipients")

def run_single_draft():
    """Run single draft creation."""
    try:
        from gmail_draft_generator import GmailDraftGenerator
        
        generator = GmailDraftGenerator()
        generator.run_draft_generator()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all required packages are installed")
    except Exception as e:
        print(f"❌ Error: {e}")

def run_batch_drafts():
    """Run batch draft creation."""
    try:
        from gmail_batch_draft_generator import GmailBatchDraftGenerator
        
        # Check if custom Excel file is provided
        excel_file = "Book1.xlsx"
        if not Path(excel_file).exists():
            print(f"❌ Excel file not found: {excel_file}")
            custom_file = input("Enter path to Excel file (or press Enter to skip): ").strip()
            if custom_file and Path(custom_file).exists():
                excel_file = custom_file
            else:
                print("❌ Cannot proceed without Excel file")
                return
        
        generator = GmailBatchDraftGenerator(excel_file)
        generator.run_batch_draft_generator()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all required packages are installed")
    except Exception as e:
        print(f"❌ Error: {e}")

def list_drafts():
    """List existing Gmail drafts."""
    try:
        from gmail_draft_generator import GmailDraftGenerator
        
        generator = GmailDraftGenerator()
        if generator.setup_gmail_api():
            generator.list_drafts()
        else:
            print("❌ Failed to setup Gmail API")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all required packages are installed")
    except Exception as e:
        print(f"❌ Error: {e}")

def check_setup():
    """Check if setup is complete."""
    issues = []
    
    # Check credentials file
    if not Path("credentials.json").exists():
        issues.append("❌ credentials.json not found")
    else:
        print("✅ credentials.json found")
    
    # Check Python packages
    try:
        import google.auth
        import googleapiclient
        print("✅ Google API packages installed")
    except ImportError:
        issues.append("❌ Google API packages not installed")
    
    # Check Excel file for batch mode
    if Path("Book1.xlsx").exists():
        print("✅ Book1.xlsx found (for batch mode)")
    else:
        print("⚠️  Book1.xlsx not found (batch mode won't work)")
    
    # Check Supabase config
    try:
        from src.pdf_storage import PDFStorage
        print("✅ PDF storage system available")
    except ImportError:
        issues.append("❌ PDF storage system not available")
    
    if issues:
        print("\n🔧 Setup Issues:")
        for issue in issues:
            print(f"   {issue}")
        print("\n   Run option 4 (Help & Setup) for instructions")
    else:
        print("\n🎉 Setup looks good!")
    
    return len(issues) == 0

def main():
    """Main runner function."""
    try:
        while True:
            show_menu()
            
            try:
                choice = input("\nEnter your choice (1-5): ").strip()
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            
            if choice == "1":
                print("\n🔄 Starting single draft creation...")
                run_single_draft()
                
            elif choice == "2":
                print("\n🔄 Starting batch draft creation...")
                run_batch_drafts()
                
            elif choice == "3":
                print("\n🔄 Listing existing drafts...")
                list_drafts()
                
            elif choice == "4":
                show_help()
                print("\n🔍 Checking current setup...")
                check_setup()
                
            elif choice == "5":
                print("\n👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please select 1-5.")
            
            # Wait for user to continue
            if choice in ["1", "2", "3"]:
                input("\nPress Enter to continue...")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")

if __name__ == "__main__":
    main()

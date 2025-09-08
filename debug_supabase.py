se documentation?#!/usr/bin/env python3
"""
Debug Supabase bucket contents
"""

from src.pdf_storage import PDFStorage
from src.config import SUPABASE_URL, SUPABASE_SERVICE_KEY, PDF_BUCKET

def main():
    print("🔍 Debugging Supabase bucket contents...")
    print(f"Bucket: {PDF_BUCKET}")
    
    try:
        from supabase import create_client
        
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # List all objects in the bucket
        print("\n📦 All objects in bucket:")
        response = supabase.storage.from_(PDF_BUCKET).list()
        
        for i, obj in enumerate(response, 1):
            print(f"   {i}. Name: {obj.get('name', 'Unknown')}")
            print(f"      Metadata: {obj.get('metadata', {})}")
            print(f"      ID: {obj.get('id', 'Unknown')}")
            print()
        
        # Try to list contents of the invoices folder
        print("\n📁 Contents of 'invoices' folder:")
        try:
            invoices_response = supabase.storage.from_(PDF_BUCKET).list("invoices")
            for i, obj in enumerate(invoices_response, 1):
                print(f"   {i}. Name: {obj.get('name', 'Unknown')}")
                print(f"      Metadata: {obj.get('metadata', {})}")
                print()
        except Exception as e:
            print(f"   Error listing invoices folder: {e}")
        
        # Try to list contents of Aribau_1_1 folder
        print("\n📁 Contents of 'Aribau_1_1' folder:")
        try:
            aribau_response = supabase.storage.from_(PDF_BUCKET).list("Aribau_1_1")
            for i, obj in enumerate(aribau_response, 1):
                print(f"   {i}. Name: {obj.get('name', 'Unknown')}")
                print(f"      Metadata: {obj.get('metadata', {})}")
                print()
        except Exception as e:
            print(f"   Error listing Aribau_1_1 folder: {e}")
        
        # Try to list contents of invoices/Aribau_1_1 folder
        print("\n📁 Contents of 'invoices/Aribau_1_1' folder:")
        try:
            nested_response = supabase.storage.from_(PDF_BUCKET).list("invoices/Aribau_1_1")
            for i, obj in enumerate(nested_response, 1):
                print(f"   {i}. Name: {obj.get('name', 'Unknown')}")
                print(f"      Metadata: {obj.get('metadata', {})}")
                print()
        except Exception as e:
            print(f"   Error listing invoices/Aribau_1_1 folder: {e}")
        
        # Try to get a specific file that we know exists
        print("\n🔍 Trying to access specific files:")
        test_files = [
            "invoices/Aribau_1_1/unknown_20250904_1005.pdf",
            "invoices/Aribau_1_1/unknown_20250904_1013.pdf"
        ]
        
        for test_file in test_files:
            try:
                # Try to get file info
                file_info = supabase.storage.from_(PDF_BUCKET).get_public_url(test_file)
                print(f"   ✅ {test_file}: {file_info}")
            except Exception as e:
                print(f"   ❌ {test_file}: {e}")
        
        # Test different property name variations
        test_names = [
            "Aribau 1º 1ª",
            "Aribau_1_1", 
            "Aribau_1º_1ª",
            "Aribau",
            "Aribau_1_1/invoices"
        ]
        
        pdf_storage = PDFStorage()
        
        print("\n🏠 Testing property name variations:")
        for name in test_names:
            pdfs = pdf_storage.list_pdfs_for_property(name)
            print(f"   '{name}': {len(pdfs)} PDFs")
            for pdf in pdfs:
                print(f"      - {pdf['filename']} ({pdf['object_key']})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

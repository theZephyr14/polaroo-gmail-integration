#!/usr/bin/env python3
"""
Check what PDFs are stored in Supabase bucket
"""

from src.pdf_storage import PDFStorage

def main():
    print("🔍 Checking Supabase PDF bucket...")
    
    pdf_storage = PDFStorage()
    
    # List all PDFs in the bucket
    try:
        from supabase import create_client
        from src.config import SUPABASE_URL, SUPABASE_SERVICE_KEY, PDF_BUCKET
        
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        response = supabase.storage.from_(PDF_BUCKET).list()
        
        print(f"📦 Bucket: {PDF_BUCKET}")
        print(f"📄 Found {len(response)} objects:")
        
        for i, obj in enumerate(response, 1):
            print(f"   {i}. {obj.get('name', 'Unknown')}")
            print(f"      Size: {obj.get('metadata', {}).get('size', 0)} bytes")
            print(f"      Created: {obj.get('created_at', 'Unknown')}")
            print()
        
        # Test listing PDFs for specific properties
        test_properties = ["Aribau 1º 1ª", "Aribau_1_1", "Aribau"]
        
        for prop in test_properties:
            pdfs = pdf_storage.list_pdfs_for_property(prop)
            print(f"🏠 PDFs for '{prop}': {len(pdfs)}")
            for pdf in pdfs:
                print(f"   - {pdf['filename']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

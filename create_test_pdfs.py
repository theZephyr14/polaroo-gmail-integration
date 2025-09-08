#!/usr/bin/env python3
"""
Create test PDFs and upload them to Supabase for Gmail testing
"""

from src.pdf_storage import PDFStorage
from pathlib import Path

def create_test_pdf(filename: str, content: str) -> bytes:
    """Create a simple test PDF with content"""
    # Create a simple PDF using reportlab
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from io import BytesIO
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Add content
        p.drawString(100, 750, f"Test Invoice: {filename}")
        p.drawString(100, 700, content)
        p.drawString(100, 650, "This is a test PDF for Gmail automation")
        
        p.showPage()
        p.save()
        
        return buffer.getvalue()
        
    except ImportError:
        # Fallback: create a simple text file with PDF extension
        return f"Test PDF Content\n{filename}\n{content}\nThis is a test PDF for Gmail automation".encode()

def main():
    print("📄 Creating test PDFs for Gmail testing...")
    
    pdf_storage = PDFStorage()
    
    # Create test PDFs for Aribau 1º 1ª
    property_name = "Aribau 1º 1ª"
    
    test_pdfs = [
        {
            'filename': 'electricity_june_2024.pdf',
            'content': 'Electricity Invoice - June 2024\nAmount: €122.88\nProperty: Aribau 1º 1ª'
        },
        {
            'filename': 'electricity_july_2024.pdf', 
            'content': 'Electricity Invoice - July 2024\nAmount: €114.94\nProperty: Aribau 1º 1ª'
        },
        {
            'filename': 'water_june_july_2024.pdf',
            'content': 'Water Invoice - June-July 2024\nAmount: €95.94\nProperty: Aribau 1º 1ª'
        }
    ]
    
    uploaded_count = 0
    
    for pdf_info in test_pdfs:
        try:
            print(f"📝 Creating {pdf_info['filename']}...")
            
            # Create PDF content
            pdf_data = create_test_pdf(pdf_info['filename'], pdf_info['content'])
            
            # Upload to Supabase
            result = pdf_storage.upload_pdf(
                file_data=pdf_data,
                filename=pdf_info['filename'],
                property_name=property_name
            )
            
            if result['success']:
                print(f"   ✅ Uploaded: {result['object_key']}")
                uploaded_count += 1
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ Error creating {pdf_info['filename']}: {e}")
    
    print(f"\n📊 Summary: {uploaded_count}/{len(test_pdfs)} PDFs uploaded successfully")
    
    if uploaded_count > 0:
        print("✅ Test PDFs ready for Gmail testing!")
    else:
        print("❌ No PDFs uploaded. Check your Supabase configuration.")

if __name__ == "__main__":
    main()

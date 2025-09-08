"""
FastAPI backend for Polaroo utility bill processing.

This API provides endpoints for:
1. Running monthly utility calculations
2. Retrieving historical data
3. Managing configuration settings
4. Exporting reports

Designed for production deployment on platforms like:
- Railway
- Renderm keepts. howto change it right?
- Heroku
- DigitalOcean App Platform
- AWS Elastic Beanstalk
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import tempfile
import json
import asyncio
from datetime import date, datetime
from pathlib import Path
import pandas as pd
import io

from src.polaroo_scrape import download_report_sync, download_report_bytes
from src.polaroo_process import process_usage, USER_ADDRESSES
from src.load_supabase import upload_raw, upsert_monthly
from src.email_system import EmailGenerator, InvoiceDownloader, EmailSender, TemplateManager
from src.pdf_storage import pdf_storage

# Import Gmail Draft Generator
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')
try:
    from gmail_draft_generator import GmailDraftGenerator
    GMAIL_DRAFT_AVAILABLE = True
except ImportError:
    GMAIL_DRAFT_AVAILABLE = False
    print("⚠️ Gmail Draft Generator not available")

# Initialize FastAPI app
app = FastAPI(
    title="Utility Bill Calculator API",
    description="API for processing Polaroo utility reports and calculating excess charges",
    version="1.0.0"
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Pydantic models for request/response
class CalculationRequest(BaseModel):
    auto_save: bool = True

class CalculationResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ConfigurationRequest(BaseModel):
    electricity_allowance: float
    water_allowance: float

# Global state for storing calculation results
calculation_results = {}

# Initialize email system components
email_generator = EmailGenerator()
invoice_downloader = InvoiceDownloader(offline_mode=True)
email_sender = EmailSender(offline_mode=True)
template_manager = TemplateManager()

@app.get("/")
async def root():
    """Serve the main application."""
    return FileResponse("src/static/index.html")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Utility Bill Calculator API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/health/detailed")
async def detailed_health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",  # Add actual DB check
        "polaroo": "configured",  # Add actual Polaroo check
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/calculate", response_model=CalculationResponse)
async def calculate_monthly_report(request: CalculationRequest):
    """
    Run the monthly utility calculation workflow.
    
    This endpoint:
    1. Downloads the latest report from Polaroo
    2. Processes the data and calculates excess charges
    3. Optionally saves results to database
    4. Returns processed data for frontend display
    """
    try:
        print("🚀 [API] Starting monthly calculation request...")
        
        # Step 1: Download report from Polaroo
        print("📥 [API] Step 1/3: Downloading report from Polaroo...")
        file_bytes, filename = await download_report_bytes()
        print(f"✅ [API] Report downloaded: {filename} ({len(file_bytes)} bytes)")
        
        # Step 2: Archive to Supabase (if requested)
        if request.auto_save:
            print("☁️ [API] Step 2/3: Archiving report to Supabase...")
            try:
                # Ensure we have bytes, not BytesIO
                if hasattr(file_bytes, 'read'):
                    file_bytes = file_bytes.read()
                upload_raw(date.today(), file_bytes, filename)
                print("✅ [API] Report archived successfully")
            except Exception as e:
                print(f"⚠️ [API] Warning: Failed to archive report: {e}")
        
        # Step 3: Process data and calculate excess charges
        print("🧮 [API] Step 3/3: Processing data and calculating excess charges...")
        
        # Create temporary file for processing
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx" if filename.endswith('.xlsx') else ".csv") as tmp:
            # Ensure we write bytes
            if hasattr(file_bytes, 'read'):
                file_bytes.seek(0)
                tmp.write(file_bytes.read())
            else:
                tmp.write(file_bytes)
            tmp_path = tmp.name
        
        try:
            print(f"📊 [API] Processing file: {tmp_path}")
            if filename.endswith('.xlsx'):
                df_raw = pd.read_excel(tmp_path, engine='openpyxl')
                print(f"🔍 [API] Excel columns found: {list(df_raw.columns)}")
                print(f"🔍 [API] First few rows:")
                print(df_raw.head().to_string())
            
            df = process_usage(tmp_path, allowances=None, delimiter=';', decimal=',')
            print(f"✅ [API] Data processed: {len(df)} properties found")
            print(f"🔍 [API] Processed DataFrame columns: {list(df.columns)}")
            
            properties = []
            book1_properties = []  # Properties in USER_ADDRESSES (book1)
            
            for _, row in df.iterrows():
                try:
                    property_data = {
                        "name": str(row.get('Property', 'Unknown')),
                        "elec_cost": float(row.get('Electricity Cost', 0)),
                        "water_cost": float(row.get('Water Cost', 0)),
                        "elec_extra": float(row.get('elec_extra', 0)),
                        "water_extra": float(row.get('water_extra', 0)),
                        "total_extra": float(row.get('Total Extra', 0)),
                        "allowance": float(row.get('Allowance', 0))
                    }
                    
                    # Add to all properties list
                    properties.append(property_data)
                    
                    # Check if this property is in book1 (USER_ADDRESSES)
                    if property_data["name"] in USER_ADDRESSES:
                        book1_properties.append(property_data)
                        
                except Exception as e:
                    print(f"⚠️ [API] Error processing row: {e}")
                    print(f"🔍 [API] Row data: {dict(row)}")
            
            print(f"📊 [API] Total properties processed: {len(properties)}")
            print(f"📊 [API] Book1 properties found: {len(book1_properties)}")
            print(f"📊 [API] Book1 property names: {[p['name'] for p in book1_properties[:5]]}...")
            
            # Use book1_properties for the response (filtered results)
            filtered_properties = book1_properties
            
            results_data = {
                "properties": filtered_properties,  # Only book1 properties
                "summary": {
                    "total_properties": len(filtered_properties),
                    "total_electricity_cost": sum(p["elec_cost"] for p in filtered_properties),
                    "total_water_cost": sum(p["water_cost"] for p in filtered_properties),
                    "total_electricity_extra": 0.0,  # No individual elec extra
                    "total_water_extra": 0.0,  # No individual water extra
                    "total_extra": sum(p["total_extra"] for p in filtered_properties),  # Total overages
                    "properties_with_overages": len([p for p in filtered_properties if p["total_extra"] > 0]),
                    "calculation_date": datetime.now().isoformat(),
                    "allowance_system": "room-based",
                    "filter_applied": "book1_only",  # Indicate filtering was applied
                    "total_properties_processed": len(properties)  # Show total processed vs filtered
                }
            }
            
            # Store results globally (in production, use Redis or database)
            calculation_results["latest"] = results_data
            
            print(f"✅ [API] Calculation completed successfully! Processed {len(properties)} properties")
            print(f"📊 [API] Summary: {len([p for p in filtered_properties if p['total_extra'] > 0])} book1 properties with total overages")
            print(f"📊 [API] Filtering: Showing {len(filtered_properties)} book1 properties out of {len(properties)} total")
            
            # Debug: Show what we're sending to frontend
            print(f"🔍 [API] First 3 book1 properties being sent to frontend:")
            for i, prop in enumerate(filtered_properties[:3]):
                print(f"  {i+1}. {prop}")
                print(f"    - elec_cost: {prop['elec_cost']}, water_cost: {prop['water_cost']}")
                print(f"    - elec_extra: {prop['elec_extra']}, water_extra: {prop['water_extra']}")
                print(f"    - allowance: {prop['allowance']}")
            
        except Exception as e:
            print(f"❌ [API] Calculation failed: {e}")
            import traceback
            traceback.print_exc()
            return CalculationResponse(
                success=False,
                message="Calculation failed",
                error=str(e)
            )
        finally:
            # Clean up temporary file
            import os
            try:
                os.unlink(tmp_path)
                print("🧹 [API] Temporary file cleaned up")
            except:
                pass
        
        return CalculationResponse(
            success=True,
            message=f"Monthly calculation completed successfully using room-based allowances",
            data=results_data
        )
        
    except Exception as e:
        return CalculationResponse(
            success=False,
            message="Calculation failed",
            error=str(e)
        )

@app.get("/api/results/latest")
async def get_latest_results():
    """Get the most recent calculation results."""
    if "latest" not in calculation_results:
        raise HTTPException(status_code=404, detail="No calculation results available")
    
    return calculation_results["latest"]

@app.get("/api/export/csv")
async def export_csv():
    """Export the latest results as CSV."""
    if "latest" not in calculation_results:
        raise HTTPException(status_code=404, detail="No calculation results available")
    
    df = pd.DataFrame(calculation_results["latest"]["properties"])
    
    # Create CSV in memory
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    return JSONResponse(
        content={"csv_data": csv_buffer.getvalue()},
        headers={"Content-Disposition": f"attachment; filename=utility_report_{date.today().strftime('%Y%m%d')}.csv"}
    )

@app.get("/api/export/excel")
async def export_excel():
    """Export the latest results as Excel."""
    if "latest" not in calculation_results:
        raise HTTPException(status_code=404, detail="No calculation results available")
    
    df = pd.DataFrame(calculation_results["latest"]["properties"])
    
    # Create Excel in memory
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Utility Report', index=False)
        
        # Create summary sheet
        summary_data = {
            'Metric': ['Total Properties', 'Properties with Elec Overages', 'Properties with Water Overages',
                      'Total Electricity Cost', 'Total Water Cost', 'Total Electricity Extra', 'Total Water Extra'],
            'Value': [
                calculation_results["latest"]["summary"]["total_properties"],
                calculation_results["latest"]["summary"]["properties_with_elec_overages"],
                calculation_results["latest"]["summary"]["properties_with_water_overages"],
                calculation_results["latest"]["summary"]["total_electricity_cost"],
                calculation_results["latest"]["summary"]["total_water_cost"],
                calculation_results["latest"]["summary"]["total_electricity_extra"],
                calculation_results["latest"]["summary"]["total_water_extra"]
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
    
    excel_buffer.seek(0)
    
    return JSONResponse(
        content={"excel_data": excel_buffer.getvalue().hex()},  # Convert bytes to hex for JSON
        headers={"Content-Disposition": f"attachment; filename=utility_report_{date.today().strftime('%Y%m%d')}.xlsx"}
    )

@app.get("/api/configuration")
async def get_configuration():
    """Get current configuration settings."""
    from src.polaroo_process import ROOM_LIMITS, SPECIAL_LIMITS, ADDRESS_ROOM_MAPPING
    return {
        "allowance_system": "room-based",
        "room_limits": ROOM_LIMITS,
        "special_limits": SPECIAL_LIMITS,
        "address_room_mapping": ADDRESS_ROOM_MAPPING,
        "properties": USER_ADDRESSES
    }

# ============================================================================
# EMAIL SYSTEM ENDPOINTS
# ============================================================================

class EmailGenerationRequest(BaseModel):
    property_name: str
    require_approval: bool = True

class EmailApprovalRequest(BaseModel):
    email_id: str
    action: str  # "approve" or "reject"
    reason: Optional[str] = None

class InvoiceDownloadRequest(BaseModel):
    property_name: str

@app.post("/api/email/generate")
async def generate_email_for_property(request: EmailGenerationRequest):
    """Generate email for a specific property with overages."""
    try:
        # Get property data from latest calculation results
        if "latest" not in calculation_results:
            raise HTTPException(status_code=404, detail="No calculation results available")
        
        properties = calculation_results["latest"]["properties"]
        property_data = None
        
        for prop in properties:
            if prop["name"] == request.property_name:
                property_data = prop
                break
        
        if not property_data:
            raise HTTPException(status_code=404, detail=f"Property '{request.property_name}' not found")
        
        # Check if property has overages
        if property_data["total_extra"] <= 0:
            return {
                "success": False,
                "message": f"No overages found for property '{request.property_name}'",
                "total_extra": property_data["total_extra"]
            }
        
        # Download invoices for this property
        print(f"📧 [EMAIL] Downloading invoices for {request.property_name}...")
        invoice_result = invoice_downloader.download_invoices_for_property(property_data)
        
        if invoice_result.get("success"):
            # Add invoice URLs to property data
            elec_invoice = invoice_result.get("electricity_invoice", {})
            water_invoice = invoice_result.get("water_invoice", {})
            
            property_data["electricity_invoice_url"] = elec_invoice.get("download_url", "")
            property_data["water_invoice_url"] = water_invoice.get("download_url", "")
            property_data["payment_link"] = f"https://payment.example.com/{request.property_name}"
        
        # Generate email
        print(f"📧 [EMAIL] Generating email for {request.property_name}...")
        email_data = email_generator.generate_email_for_property(property_data)
        
        if not email_data:
            raise HTTPException(status_code=500, detail="Failed to generate email")
        
        # Send email (with approval if required)
        print(f"📧 [EMAIL] Sending email for {request.property_name}...")
        send_result = email_sender.send_email(email_data, require_approval=request.require_approval)
        
        return {
            "success": True,
            "message": "Email generated and queued successfully",
            "email_id": email_data["id"],
            "property_name": request.property_name,
            "total_extra": property_data["total_extra"],
            "email_address": email_data["email_address"],
            "status": send_result.get("status", "unknown"),
            "require_approval": request.require_approval,
            "invoice_downloaded": invoice_result.get("success", False)
        }
        
    except Exception as e:
        print(f"❌ [EMAIL] Error generating email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/email/generate-bulk")
async def generate_emails_for_overages():
    """Generate emails for all properties with overages."""
    try:
        if "latest" not in calculation_results:
            raise HTTPException(status_code=404, detail="No calculation results available")
        
        properties = calculation_results["latest"]["properties"]
        overage_properties = [p for p in properties if p["total_extra"] > 0]
        
        if not overage_properties:
            return {
                "success": True,
                "message": "No properties with overages found",
                "generated_emails": 0,
                "properties_processed": len(properties)
            }
        
        generated_emails = []
        
        for property_data in overage_properties:
            try:
                # Download invoices
                invoice_result = invoice_downloader.download_invoices_for_property(property_data)
                
                if invoice_result.get("success"):
                    elec_invoice = invoice_result.get("electricity_invoice", {})
                    water_invoice = invoice_result.get("water_invoice", {})
                    
                    property_data["electricity_invoice_url"] = elec_invoice.get("download_url", "")
                    property_data["water_invoice_url"] = water_invoice.get("download_url", "")
                    property_data["payment_link"] = f"https://payment.example.com/{property_data['name']}"
                
                # Generate email
                email_data = email_generator.generate_email_for_property(property_data)
                
                if email_data:
                    # Queue for approval
                    send_result = email_sender.send_email(email_data, require_approval=True)
                    
                    generated_emails.append({
                        "email_id": email_data["id"],
                        "property_name": property_data["name"],
                        "total_extra": property_data["total_extra"],
                        "email_address": email_data["email_address"],
                        "status": send_result.get("status", "unknown")
                    })
                    
                    # Add 5-second delay between operations
                    import asyncio
                    await asyncio.sleep(5)
                    
            except Exception as e:
                print(f"⚠️ [EMAIL] Error processing property {property_data['name']}: {e}")
                continue
        
        return {
            "success": True,
            "message": f"Generated {len(generated_emails)} emails for properties with overages",
            "generated_emails": len(generated_emails),
            "properties_processed": len(overage_properties),
            "emails": generated_emails
        }
        
    except Exception as e:
        print(f"❌ [EMAIL] Error in bulk email generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/email/pending-approvals")
async def get_pending_approvals():
    """Get all emails pending approval."""
    try:
        pending_emails = email_sender.get_pending_approvals()
        
        # Add email preview data
        for approval in pending_emails:
            email_data = approval.get("email_data", {})
            approval["preview"] = {
                "property_name": email_data.get("property_name", ""),
                "email_address": email_data.get("email_address", ""),
                "subject": email_data.get("subject", ""),
                "total_extra": email_data.get("total_extra", 0.0)
            }
        
        return {
            "success": True,
            "pending_count": len(pending_emails),
            "emails": pending_emails
        }
        
    except Exception as e:
        print(f"❌ [EMAIL] Error getting pending approvals: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/email/approve")
async def approve_or_reject_email(request: EmailApprovalRequest):
    """Approve or reject a pending email."""
    try:
        if request.action == "approve":
            result = email_sender.approve_email(request.email_id)
        elif request.action == "reject":
            result = email_sender.reject_email(request.email_id, request.reason or "Rejected by operator")
        else:
            raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")
        
        return {
            "success": result["success"],
            "message": result.get("message", ""),
            "email_id": request.email_id,
            "action": request.action,
            "status": result.get("status", "unknown")
        }
        
    except Exception as e:
        print(f"❌ [EMAIL] Error approving/rejecting email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/email/status/{email_id}")
async def get_email_status(email_id: str):
    """Get the status of a specific email."""
    try:
        status = email_sender.get_email_status(email_id)
        
        if status is None:
            raise HTTPException(status_code=404, detail="Email not found")
        
        return {
            "success": True,
            "email_id": email_id,
            "status": status
        }
        
    except Exception as e:
        print(f"❌ [EMAIL] Error getting email status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/email/sent")
async def get_sent_emails():
    """Get all sent emails."""
    try:
        sent_emails = email_sender.get_sent_emails()
        
        return {
            "success": True,
            "sent_count": len(sent_emails),
            "emails": sent_emails
        }
        
    except Exception as e:
        print(f"❌ [EMAIL] Error getting sent emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/email/statistics")
async def get_email_statistics():
    """Get email system statistics."""
    try:
        email_stats = email_sender.get_email_statistics()
        invoice_stats = invoice_downloader.get_invoice_statistics()
        
        return {
            "success": True,
            "email_statistics": email_stats,
            "invoice_statistics": invoice_stats
        }
        
    except Exception as e:
        print(f"❌ [EMAIL] Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/invoices/download")
async def download_invoices_for_property(request: InvoiceDownloadRequest):
    """Download invoices for a specific property."""
    try:
        if "latest" not in calculation_results:
            raise HTTPException(status_code=404, detail="No calculation results available")
        
        properties = calculation_results["latest"]["properties"]
        property_data = None
        
        for prop in properties:
            if prop["name"] == request.property_name:
                property_data = prop
                break
        
        if not property_data:
            raise HTTPException(status_code=404, detail=f"Property '{request.property_name}' not found")
        
        print(f"📄 [INVOICE] Downloading invoices for {request.property_name}...")
        result = invoice_downloader.download_invoices_for_property(property_data)
        
        return {
            "success": result.get("success", False),
            "property_name": request.property_name,
            "electricity_invoice": result.get("electricity_invoice"),
            "water_invoice": result.get("water_invoice"),
            "error": result.get("error")
        }
        
    except Exception as e:
        print(f"❌ [INVOICE] Error downloading invoices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/invoices/cleanup")
async def cleanup_expired_invoices():
    """Clean up expired invoices (older than 10 minutes)."""
    try:
        cleaned_count = invoice_downloader.cleanup_expired_invoices()
        
        return {
            "success": True,
            "message": f"Cleaned up {cleaned_count} expired invoices",
            "cleaned_count": cleaned_count
        }
        
    except Exception as e:
        print(f"❌ [INVOICE] Error cleaning up invoices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/templates/properties")
async def get_template_properties():
    """Get all properties with email templates."""
    try:
        properties = template_manager.get_all_properties()
        
        return {
            "success": True,
            "properties": properties,
            "count": len(properties)
        }
        
    except Exception as e:
        print(f"❌ [TEMPLATE] Error getting template properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/invoices/download-real")
async def download_real_invoices_for_property(request: InvoiceDownloadRequest):
    """Download real invoices from Polaroo for a specific property (production mode)."""
    try:
        print(f"📄 [REAL_INVOICE] Starting real invoice download for {request.property_name}...")
        
        # Import the real Polaroo scraper
        from src.polaroo_scrape import download_invoices_for_property_sync
        
        # Download invoices using the real scraper
        downloaded_files = download_invoices_for_property_sync(request.property_name)
        
        if not downloaded_files:
            return {
                "success": False,
                "message": f"No invoices found for property '{request.property_name}'",
                "property_name": request.property_name,
                "downloaded_files": []
            }
        
        # Process downloaded files
        file_info = []
        for file_path in downloaded_files:
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                file_info.append({
                    "filename": file_path_obj.name,
                    "path": str(file_path_obj),
                    "size_bytes": file_path_obj.stat().st_size,
                    "created_at": datetime.fromtimestamp(file_path_obj.stat().st_ctime).isoformat()
                })
        
        return {
            "success": True,
            "message": f"Successfully downloaded {len(downloaded_files)} invoices for '{request.property_name}'",
            "property_name": request.property_name,
            "downloaded_files": file_info,
            "total_files": len(downloaded_files)
        }
        
    except Exception as e:
        print(f"❌ [REAL_INVOICE] Error downloading real invoices: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# PDF Storage Management Endpoints

class PDFUploadRequest(BaseModel):
    property_name: str
    invoice_type: str = "unknown"
    expiry_minutes: Optional[int] = None

@app.post("/api/pdf/upload")
async def upload_pdf_to_storage(
    request: PDFUploadRequest,
    file_data: bytes = None
):
    """Upload a PDF file to the dedicated PDF storage bucket."""
    try:
        if not file_data:
            raise HTTPException(status_code=400, detail="No file data provided")
        
        result = pdf_storage.upload_pdf(
            file_data=file_data,
            filename=f"{request.property_name}_{request.invoice_type}.pdf",
            property_name=request.property_name,
            invoice_type=request.invoice_type,
            custom_expiry_minutes=request.expiry_minutes
        )
        
        if result.get('success'):
            return {
                "success": True,
                "message": "PDF uploaded successfully",
                "pdf_info": result
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Upload failed'))
            
    except Exception as e:
        print(f"❌ [PDF_UPLOAD] Error uploading PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/pdf/delete/{object_key:path}")
async def delete_pdf_from_storage(object_key: str):
    """Delete a PDF from the storage bucket."""
    try:
        success = pdf_storage.delete_pdf(object_key)
        
        if success:
            return {
                "success": True,
                "message": f"PDF {object_key} deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="PDF not found or deletion failed")
            
    except Exception as e:
        print(f"❌ [PDF_DELETE] Error deleting PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pdf/info/{object_key:path}")
async def get_pdf_info(object_key: str):
    """Get information about a stored PDF."""
    try:
        info = pdf_storage.get_pdf_info(object_key)
        
        if info:
            return {
                "success": True,
                "pdf_info": info
            }
        else:
            raise HTTPException(status_code=404, detail="PDF not found")
            
    except Exception as e:
        print(f"❌ [PDF_INFO] Error getting PDF info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pdf/download-url/{object_key:path}")
async def get_pdf_download_url(object_key: str, expires_in_minutes: int = 60):
    """Get a download URL for a PDF."""
    try:
        download_url = pdf_storage.create_download_url(object_key, expires_in_minutes)
        
        if download_url:
            return {
                "success": True,
                "download_url": download_url,
                "expires_in_minutes": expires_in_minutes
            }
        else:
            raise HTTPException(status_code=404, detail="PDF not found or not accessible")
            
    except Exception as e:
        print(f"❌ [PDF_URL] Error creating download URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# GMAIL DRAFT GENERATOR ENDPOINTS
# ============================================================================

class GmailDraftRequest(BaseModel):
    property_name: str
    include_cc_recipients: bool = True
    attach_pdfs: bool = True

class BookOneEmailRequest(BaseModel):
    property_name: str

@app.post("/api/gmail/create-draft")
async def create_gmail_draft(request: GmailDraftRequest):
    """Create a Gmail draft for a property with overages using the integrated draft generator."""
    try:
        if not GMAIL_DRAFT_AVAILABLE:
            raise HTTPException(status_code=503, detail="Gmail Draft Generator not available")
        
        # Get property data from latest calculation results
        if "latest" not in calculation_results:
            raise HTTPException(status_code=404, detail="No calculation results available. Please run calculation first.")
        
        properties = calculation_results["latest"]["properties"]
        property_data = None
        
        for prop in properties:
            if prop["name"] == request.property_name:
                property_data = prop
                break
        
        if not property_data:
            raise HTTPException(status_code=404, detail=f"Property '{request.property_name}' not found")
        
        # Check if property has overages
        if property_data["total_extra"] <= 0:
            return {
                "success": False,
                "message": f"No overages found for property '{request.property_name}'",
                "total_extra": property_data["total_extra"]
            }
        
        print(f"📧 [GMAIL_DRAFT] Creating Gmail draft for {request.property_name}...")
        
        # Initialize Gmail Draft Generator
        draft_generator = GmailDraftGenerator()
        
        # Setup Gmail API
        if not draft_generator.setup_gmail_api():
            raise HTTPException(status_code=500, detail="Failed to setup Gmail API. Check credentials.json")
        
        # Load recipient emails from Book1.xlsx if requested
        recipients = []
        if request.include_cc_recipients:
            try:
                book1_emails = await load_book1_emails_for_property(request.property_name)
                recipients = book1_emails
                print(f"📧 [GMAIL_DRAFT] Found {len(recipients)} recipients from Book1.xlsx")
            except Exception as e:
                print(f"⚠️ [GMAIL_DRAFT] Warning: Could not load Book1 emails: {e}")
                recipients = [{"email": "default@example.com", "type": "to"}]
        else:
            recipients = [{"email": "default@example.com", "type": "to"}]
        
        # Download PDFs if requested
        pdf_files = []
        if request.attach_pdfs:
            try:
                pdf_files = draft_generator.download_pdfs_from_supabase()
                print(f"📧 [GMAIL_DRAFT] Downloaded {len(pdf_files)} PDF attachments")
            except Exception as e:
                print(f"⚠️ [GMAIL_DRAFT] Warning: Could not download PDFs: {e}")
        
        # Create the Gmail draft
        # For now, use the first recipient as the main recipient
        main_recipient = recipients[0]["email"] if recipients else "default@example.com"
        
        draft_id = draft_generator.create_draft(main_recipient, pdf_files)
        
        if not draft_id:
            raise HTTPException(status_code=500, detail="Failed to create Gmail draft")
        
        # Clean up temp files
        draft_generator.cleanup_temp_files()
        
        return {
            "success": True,
            "message": f"Gmail draft created successfully for {request.property_name}",
            "property_name": request.property_name,
            "draft_id": draft_id,
            "recipient_count": len(recipients),
            "attachment_count": len(pdf_files),
            "recipients": recipients,
            "attachments": [{"filename": Path(f).name} for f in pdf_files],
            "gmail_url": f"https://mail.google.com/mail/u/0/#drafts/{draft_id}"
        }
        
    except Exception as e:
        print(f"❌ [GMAIL_DRAFT] Error creating Gmail draft: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/book1/emails")
async def get_book1_emails(request: BookOneEmailRequest):
    """Get email addresses for a property from Book1.xlsx."""
    try:
        emails = await load_book1_emails_for_property(request.property_name)
        
        return {
            "success": True,
            "property_name": request.property_name,
            "email_count": len(emails),
            "emails": emails
        }
        
    except Exception as e:
        print(f"❌ [BOOK1] Error loading emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def load_book1_emails_for_property(property_name: str) -> List[Dict[str, str]]:
    """Load email addresses for a property from Book1.xlsx."""
    try:
        book1_path = Path("Book1.xlsx")
        
        if not book1_path.exists():
            print(f"⚠️ [BOOK1] Book1.xlsx not found, using default email")
            return [{"email": "default@example.com", "type": "to"}]
        
        # Read Excel file
        df = pd.read_excel(book1_path)
        
        # Expected columns: name, mail (based on actual file structure)
        if 'name' not in df.columns:
            print(f"⚠️ [BOOK1] name column not found in Book1.xlsx")
            return [{"email": "default@example.com", "type": "to"}]
        
        # Find the property row
        property_rows = df[df['name'].str.strip() == property_name.strip()]
        
        if property_rows.empty:
            print(f"⚠️ [BOOK1] Property '{property_name}' not found in Book1.xlsx")
            return [{"email": "default@example.com", "type": "to"}]
        
        # Get the first matching row
        row = property_rows.iloc[0]
        
        # Extract email addresses (using actual column structure)
        emails = []
        
        # Check if mail column exists and has a valid email
        if 'mail' in df.columns and pd.notna(row['mail']):
            email = str(row['mail']).strip()
            if email and '@' in email:
                emails.append({"email": email, "type": "to"})
        
        if not emails:
            print(f"⚠️ [BOOK1] No valid emails found for '{property_name}' in Book1.xlsx")
            return [{"email": "default@example.com", "type": "to"}]
        
        print(f"✅ [BOOK1] Found {len(emails)} emails for '{property_name}'")
        return emails
        
    except Exception as e:
        print(f"❌ [BOOK1] Error reading Book1.xlsx: {e}")
        return [{"email": "default@example.com", "type": "to"}]

@app.get("/gmail-draft")
async def gmail_draft_page():
    """Serve the Gmail draft creation page."""
    return FileResponse("src/static/gmail_draft.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

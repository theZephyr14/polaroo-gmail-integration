"""
FastAPI backend for Polaroo utility bill processing.

This API provides endpoints for:
1. Running monthly utility calculations
2. Retrieving historical data
3. Managing configuration settings
4. Exporting reports

Designed for production deployment on platforms like:
- Railway
- Render
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

# Import from src directory
from src.polaroo_scrape import download_report_sync
from src.polaroo_process import process_usage, USER_ADDRESSES
from src.load_supabase import upload_raw, upsert_monthly

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
    print("🚀 [API] Starting monthly calculation request...")
    try:
        # Step 1: Download latest report from Polaroo
        print("📥 [API] Step 1/3: Downloading report from Polaroo...")
        file_bytes, filename = download_report_sync()
        print(f"✅ [API] Report downloaded: {filename} ({len(file_bytes)} bytes)")
        
        # Step 2: Upload to Supabase for archival (if auto_save is enabled)
        if request.auto_save:
            print("☁️ [API] Step 2/3: Archiving report to Supabase...")
            try:
                upload_raw(date.today(), file_bytes, filename)
                print("✅ [API] Report archived successfully")
            except Exception as e:
                # Log warning but continue processing
                print(f"⚠️ [API] Warning: Failed to archive report: {e}")
        else:
            print("⏭️ [API] Step 2/3: Skipping archive (auto_save disabled)")
        
        # Step 3: Process the data using room-based allowances
        print("🧮 [API] Step 3/3: Processing data and calculating excess charges...")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx" if filename.endswith('.xlsx') else ".csv") as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        
        try:
            # Process with room-based allowances (no manual allowances needed)
            df = process_usage(tmp_path, allowances=None)
            print(f"✅ [API] Data processed: {len(df)} properties found")
            
            # Convert DataFrame to frontend-compatible format
            properties = []
            for _, row in df.iterrows():
                properties.append({
                    "name": row['unit'],
                    "elec_cost": float(row['electricity_cost']),
                    "water_cost": float(row['water_cost']),
                    "elec_extra": float(row['elec_extra']),
                    "water_extra": float(row['water_extra']),
                    "allowance": float(row['allowance'])
                })
            
            results_data = {
                "properties": properties,
                "summary": {
                    "total_properties": len(properties),
                    "total_electricity_cost": sum(p["elec_cost"] for p in properties),
                    "total_water_cost": sum(p["water_cost"] for p in properties),
                    "total_electricity_extra": sum(p["elec_extra"] for p in properties),
                    "total_water_extra": sum(p["water_extra"] for p in properties),
                    "properties_with_elec_overages": len([p for p in properties if p["elec_extra"] > 0]),
                    "properties_with_water_overages": len([p for p in properties if p["water_extra"] > 0]),
                    "calculation_date": datetime.now().isoformat(),
                    "allowance_system": "room-based"
                }
            }
            
            # Store results globally (in production, use Redis or database)
            calculation_results["latest"] = results_data
            
            print(f"✅ [API] Calculation completed successfully! Processed {len(properties)} properties")
            print(f"📊 [API] Summary: {results_data['summary']['properties_with_elec_overages']} elec overages, {results_data['summary']['properties_with_water_overages']} water overages")
            
            return CalculationResponse(
                success=True,
                message=f"Monthly calculation completed successfully using room-based allowances. Processed {len(properties)} properties.",
                data=results_data
            )
            
        finally:
            # Clean up temporary file
            try:
                Path(tmp_path).unlink()
                print("🧹 [API] Temporary file cleaned up")
            except Exception:
                pass
        
    except Exception as e:
        print(f"❌ [API] Calculation failed: {e}")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

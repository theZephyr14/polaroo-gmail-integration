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

from polaroo_scrape import download_report_sync
from polaroo_process import process_usage, USER_ADDRESSES
from load_supabase import upload_raw, upsert_monthly

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
app.mount("/static", StaticFiles(directory="static"), name="static")

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
    return FileResponse("static/index.html")

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
        # For now, return test data to verify the frontend works
        # TODO: Re-enable actual scraping once we confirm the frontend works
        
        # Create test data with room-based allowances
        test_properties = [
            {
                "name": "Aribau 1º 1ª",
                "elec_cost": 85.0,
                "water_cost": 45.0,
                "elec_extra": 15.0,  # 85 - 70 (2 room allowance)
                "water_extra": 0.0,   # 45 - 70 (under allowance)
                "allowance": 70.0
            },
            {
                "name": "Aribau 126-128 3-1", 
                "elec_cost": 120.0,
                "water_cost": 80.0,
                "elec_extra": 20.0,   # 120 - 100 (3 room allowance)
                "water_extra": 0.0,   # 80 - 100 (under allowance)
                "allowance": 100.0
            },
            {
                "name": "Padilla 1",
                "elec_cost": 180.0,
                "water_cost": 90.0,
                "elec_extra": 30.0,   # 180 - 150 (special allowance)
                "water_extra": 0.0,   # 90 - 150 (under allowance)
                "allowance": 150.0
            },
            {
                "name": "Aribau Escalera",
                "elec_cost": 40.0,
                "water_cost": 30.0,
                "elec_extra": 0.0,    # 40 - 50 (under allowance)
                "water_extra": 0.0,   # 30 - 50 (under allowance)
                "allowance": 50.0
            }
        ]
        
        results_data = {
            "properties": test_properties,
            "summary": {
                "total_properties": len(test_properties),
                "total_electricity_cost": sum(p["elec_cost"] for p in test_properties),
                "total_water_cost": sum(p["water_cost"] for p in test_properties),
                "total_electricity_extra": sum(p["elec_extra"] for p in test_properties),
                "total_water_extra": sum(p["water_extra"] for p in test_properties),
                "properties_with_elec_overages": len([p for p in test_properties if p["elec_extra"] > 0]),
                "properties_with_water_overages": len([p for p in test_properties if p["water_extra"] > 0]),
                "calculation_date": datetime.now().isoformat(),
                "allowance_system": "room-based"
            }
        }
        
        # Store results globally (in production, use Redis or database)
        calculation_results["latest"] = results_data
        
        return CalculationResponse(
            success=True,
            message=f"Monthly calculation completed successfully using room-based allowances (TEST DATA)",
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
    from polaroo_process import ROOM_LIMITS, SPECIAL_LIMITS, ADDRESS_ROOM_MAPPING
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

#!/usr/bin/env python3
"""
Simple test server to verify FastAPI setup works locally
"""

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Create a simple FastAPI app
app = FastAPI(title="Test Server")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Serve the main application."""
    return FileResponse("static/index.html")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "Test server is running!"
    }

if __name__ == "__main__":
    print("Starting test server on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

#!/usr/bin/env python3
"""
Simple runner script for the NFC backend
"""
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("DEBUG", "True").lower() == "true"

    print(f"Starting FlipFlow Backend API...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug/Reload: {reload}")
    print(f"\nAPI Documentation will be available at:")
    print(f"http://localhost:{port}/docs")
    print(f"http://localhost:{port}/redoc\n")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

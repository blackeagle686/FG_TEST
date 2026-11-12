#!/usr/bin/env python3
"""
Dashboard Launcher for FortyGuard Urban Thermal AI
Starts the FastAPI backend and serves the Prime UI/UX on http://localhost:8000
"""

import os
import sys
from pathlib import Path

# Add project root and dashboard to Python path
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BASE_DIR))

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")
    
    print("=" * 65)
    print(" FORTYGUARD URBAN THERMAL AI - PRIME DASHBOARD")
    print("=" * 65)
    print(f" * Backend   : FastAPI & Uvicorn")
    print(f" * UI/UX     : Prime Glassmorphism (Gold, Black, White)")
    print(f" * Framework : Bootstrap 5 + Leaflet + Chart.js")
    print(f" * Serving at: http://{host}:{port}")
    print("=" * 65)
    
    uvicorn.run("app:app", app_dir=str(BASE_DIR), host=host, port=port, reload=True)

"""
Run script for Examination Middleware
Starts the FastAPI application with uvicorn
"""

import uvicorn
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Run the FastAPI application."""
    # Render sets PORT env var; default to 8000 for local dev
    port = int(os.environ.get("PORT", 8000))
    is_production = os.environ.get("RENDER", "") == "true" or os.environ.get("DEBUG", "true").lower() == "false"
    
    print("=" * 60)
    print("  Examination Middleware - Starting Server")
    print("=" * 60)
    print()
    print(f"  Port:           {port}")
    print(f"  Mode:           {'Production' if is_production else 'Development'}")
    print(f"  Staff Portal:   /portal/staff")
    print(f"  Student Portal: /portal/student")
    print(f"  API Docs:       /docs")
    print(f"  Health Check:   /health")
    print()
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=not is_production,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()

"""
Startup script for the FastAPI server.
Run this to start the Eval Dashboard API.
"""
import os
import sys

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 Starting Eval Dashboard API Server")
    print("=" * 80)
    print("\nAPI will be available at:")
    print("  - Main API: http://127.0.0.1:8000")
    print("  - Interactive docs: http://127.0.0.1:8000/docs")
    print("  - ReDoc: http://127.0.0.1:8000/redoc")
    print("\nPress CTRL+C to stop the server\n")
    print("=" * 80)

    # Run uvicorn
    os.system("uvicorn api.main:app --reload --host 127.0.0.1 --port 8000")

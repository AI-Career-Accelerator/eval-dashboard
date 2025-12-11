"""
Startup script for the FastAPI server.
Run this to start the Eval Dashboard API.
"""
import os
import sys

if __name__ == "__main__":
    # Change to project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)

    print("=" * 80)
    print("🚀 Starting Eval Dashboard API Server")
    print("=" * 80)
    print(f"\nProject root: {project_root}")
    print("\nAPI will be available at:")
    print("  - Main API: http://127.0.0.1:8000")
    print("  - Interactive docs: http://127.0.0.1:8000/docs")
    print("  - ReDoc: http://127.0.0.1:8000/redoc")
    print("\nPress CTRL+C to stop the server\n")
    print("=" * 80)

    # Run uvicorn
    os.system("uvicorn api.main:app --reload --host 127.0.0.1 --port 8000")

"""
Start the Streamlit dashboard.
Convenience script to launch the dashboard with proper configuration.
"""
import subprocess
import sys
import os

def main():
    """Launch the Streamlit dashboard."""

    # Get the dashboard directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    dashboard_dir = os.path.join(project_root, "dashboard")
    app_path = os.path.join(dashboard_dir, "app.py")

    # Check if app.py exists
    if not os.path.exists(app_path):
        print(f"❌ Error: Dashboard app not found at {app_path}")
        sys.exit(1)

    print("🚀 Starting Streamlit Dashboard...")
    print(f"📁 Dashboard location: {dashboard_dir}")
    print("🌐 Dashboard will open at: http://localhost:8501")
    print("\n⚠️  Make sure the FastAPI backend is running:")
    print("   python scripts/start_api.py\n")

    # Start Streamlit
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                app_path,
                "--server.port=8501",
                "--server.headless=false"
            ],
            cwd=dashboard_dir,
            check=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting dashboard: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n❌ Error: Streamlit not installed")
        print("Install it with: pip install streamlit")
        sys.exit(1)


if __name__ == "__main__":
    main()

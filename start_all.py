"""
Unified Launcher - Start all Eval Dashboard services at once
Simplifies the startup process by launching everything in separate terminal windows
"""
import subprocess
import sys
import time
import os

def start_service(name, command, wait=2):
    """Start a service in a new terminal window."""
    print(f"🚀 Starting {name}...")

    try:
        if os.name == 'nt':  # Windows
            subprocess.Popen(
                f'start cmd /k "python {command}"',
                shell=True
            )
        else:  # Linux/Mac
            # Try different terminal emulators
            terminals = ['gnome-terminal', 'xterm', 'konsole']
            for terminal in terminals:
                try:
                    subprocess.Popen([terminal, '--', 'python', command])
                    break
                except FileNotFoundError:
                    continue

        time.sleep(wait)
        print(f"✅ {name} started\n")
        return True
    except Exception as e:
        print(f"❌ Failed to start {name}: {e}\n")
        return False

def main():
    print("="*70)
    print("🎯 Eval Dashboard - Unified Launcher")
    print("="*70)
    print("\nThis will start all services in separate terminal windows.\n")

    # Ask user what to start
    print("What do you want to start?")
    print("1. Minimal (LiteLLM only) - Just run evaluations")
    print("2. Development (LiteLLM + FastAPI + Streamlit) - With dashboard")
    print("3. Full Stack (Everything + Phoenix) - Complete observability")
    print("4. Custom - Choose what to start")

    choice = input("\nEnter choice (1-4) [default: 2]: ").strip() or "2"

    print("\n" + "="*70)
    print("Starting services...")
    print("="*70 + "\n")

    services_started = []

    # Always start LiteLLM
    if start_service("LiteLLM Proxy (Port 4000)", "start_server.py", wait=3):
        services_started.append(("LiteLLM Proxy", "http://localhost:4000"))

    # Development and Full Stack
    if choice in ["2", "3", "4"]:
        if choice == "4":
            if input("Start FastAPI backend? (y/n) [y]: ").strip().lower() != 'n':
                if start_service("FastAPI Backend (Port 8000)", "scripts/start_api.py", wait=2):
                    services_started.append(("FastAPI Backend", "http://localhost:8000/docs"))

                if input("Start Streamlit dashboard? (y/n) [y]: ").strip().lower() != 'n':
                    if start_service("Streamlit Dashboard (Port 8501)", "scripts/start_dashboard.py", wait=3):
                        services_started.append(("Streamlit Dashboard", "http://localhost:8501"))
        else:
            if start_service("FastAPI Backend (Port 8000)", "scripts/start_api.py", wait=2):
                services_started.append(("FastAPI Backend", "http://localhost:8000/docs"))

            if start_service("Streamlit Dashboard (Port 8501)", "scripts/start_dashboard.py", wait=3):
                services_started.append(("Streamlit Dashboard", "http://localhost:8501"))

    # Full Stack or Custom
    if choice in ["3", "4"]:
        start_phoenix = True
        if choice == "4":
            start_phoenix = input("Start Phoenix observability? (y/n) [n]: ").strip().lower() == 'y'

        if start_phoenix:
            if start_service("Phoenix Server (Port 6006)", "scripts/start_phoenix.py", wait=2):
                services_started.append(("Phoenix Observability", "http://localhost:6006"))

    # Summary
    print("\n" + "="*70)
    print("✅ Services Started Successfully")
    print("="*70)

    if services_started:
        print("\n📊 Access Points:")
        for service, url in services_started:
            print(f"   {service:.<50} {url}")

    print("\n💡 Next Steps:")
    print("   1. Wait 10 seconds for all services to fully initialize")
    print("   2. Run evaluation: python core/evaluate.py")
    print("   3. Or trigger via API: python scripts/run_full_eval.py")
    print("   4. View results in dashboard: http://localhost:8501")

    print("\n⚠️  Important:")
    print("   - Keep this window open (services are running)")
    print("   - Close individual terminal windows to stop specific services")
    print("   - Press Ctrl+C here to exit (services will keep running)")

    print("\n📚 Documentation:")
    print("   - Simplified usage: docs/SIMPLIFIED_USAGE.md")
    print("   - Phoenix guide: docs/PHOENIX_USAGE.md")

    print("\n" + "="*70)

    input("\nPress Enter to exit this launcher (services will continue running)...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Launcher interrupted. Services are still running.")
        print("   Close individual terminal windows to stop them.\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)

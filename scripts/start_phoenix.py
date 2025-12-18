"""
Launch Phoenix observability server.
Provides trace visualization UI at http://localhost:6006
"""
import sys
import os

# Set UTF-8 encoding for Windows
if os.name == 'nt' and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

import phoenix as px

def main():
    """Start Phoenix server and keep it running."""
    print("=" * 60)
    print("🦅 Phoenix Observability Server")
    print("=" * 60)
    print("\nStarting Phoenix server...")
    print("This will open the Phoenix UI in your browser.\n")

    try:
        # Launch Phoenix with browser
        session = px.launch_app()

        print("✅ Phoenix is running at: http://localhost:6006")
        print("\n📊 Phoenix Dashboard Features:")
        print("   - Trace waterfall visualization")
        print("   - LLM call inspection (prompts + responses)")
        print("   - Performance metrics (latency, tokens, cost)")
        print("   - Search and filter traces")

        print("\n💡 How to Use:")
        print("   1. Run evaluations: python core/evaluate.py")
        print("   2. View traces in Phoenix UI (auto-opens in browser)")
        print("   3. Or check Streamlit dashboard: Phoenix Traces page")

        print("\n⏸️  Press Ctrl+C to stop Phoenix server")
        print("=" * 60)

        # Keep server running
        print("\nServer running... (waiting for traces)")
        import time
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down Phoenix server...")
        print("✅ Phoenix stopped")
    except Exception as e:
        print(f"\n❌ Error starting Phoenix: {e}")
        print("\n💡 Troubleshooting:")
        print("   - Check if port 6006 is available")
        print("   - Try: pip install --upgrade arize-phoenix")
        sys.exit(1)

if __name__ == "__main__":
    main()

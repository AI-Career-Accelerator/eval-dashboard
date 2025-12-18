"""
Phoenix (Arize) observability integration for LLM tracing.
Provides OpenTelemetry instrumentation for automatic trace capture.
"""

import os
from typing import Optional
import phoenix as px
from openinference.instrumentation.openai import OpenAIInstrumentor
from opentelemetry import trace as trace_api
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# Phoenix session
_phoenix_session: Optional[px.Client] = None
_is_instrumented = False


def check_phoenix_running():
    """Check if Phoenix is already running on port 6006."""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 6006))
        sock.close()
        return result == 0  # 0 means port is in use (Phoenix running)
    except:
        return False


def start_phoenix_server(launch_app: bool = True):
    """
    Start the Phoenix server for trace collection and visualization.

    Args:
        launch_app: If True, opens Phoenix UI in browser (default: True)

    Returns:
        Phoenix session object
    """
    global _phoenix_session

    if _phoenix_session is not None:
        print("[Phoenix] Server already running in this session")
        return _phoenix_session

    # Check if Phoenix is already running from another process
    if check_phoenix_running():
        print("[Phoenix] Server already running at http://localhost:6006")
        print("[Phoenix] Skipping launch (using existing instance)")
        return None

    try:
        # Set UTF-8 encoding for Windows compatibility
        if os.name == 'nt':  # Windows
            import sys
            if hasattr(sys.stdout, 'reconfigure'):
                try:
                    sys.stdout.reconfigure(encoding='utf-8')
                    sys.stderr.reconfigure(encoding='utf-8')
                except:
                    pass

        # Launch Phoenix server (runs on http://localhost:6006 by default)
        _phoenix_session = px.launch_app() if launch_app else px.Client()
        print(f"[Phoenix] Server started at http://localhost:6006")
        return _phoenix_session
    except RuntimeError as e:
        if "Failed to bind" in str(e) or "4317" in str(e):
            print(f"[Phoenix] Server already running at http://localhost:6006")
            print(f"[Phoenix] Using existing instance for traces")
            return None
        else:
            print(f"[Phoenix] Failed to start server: {e}")
            print(f"[Phoenix] Continuing with tracing only")
            return None
    except Exception as e:
        print(f"[Phoenix] Failed to start server: {e}")
        print(f"[Phoenix] Continuing with tracing only")
        return None


def setup_phoenix_tracing(endpoint: str = "http://localhost:6006/v1/traces"):
    """
    Configure OpenTelemetry instrumentation to send traces to Phoenix.

    Args:
        endpoint: Phoenix OTLP endpoint URL
    """
    global _is_instrumented

    if _is_instrumented:
        print("[Phoenix] Tracing already configured")
        return

    try:
        # Configure OTLP exporter to send traces to Phoenix
        tracer_provider = trace_sdk.TracerProvider()
        tracer_provider.add_span_processor(
            SimpleSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
        )
        trace_api.set_tracer_provider(tracer_provider)

        # Auto-instrument OpenAI calls (works with LiteLLM too since it uses OpenAI SDK)
        OpenAIInstrumentor().instrument()

        _is_instrumented = True
        print("[Phoenix] OpenTelemetry tracing configured")
        print(f"[Phoenix] Traces will be sent to: {endpoint}")

    except Exception as e:
        print(f"[Phoenix] Failed to setup tracing: {e}")


def initialize_phoenix(launch_server: bool = True, enable_tracing: bool = True):
    """
    Complete Phoenix initialization - starts server and configures tracing.

    Args:
        launch_server: Whether to start the Phoenix UI server
        enable_tracing: Whether to enable automatic trace instrumentation

    Returns:
        Phoenix session object (or None if failed)
    """
    session = None

    if launch_server:
        session = start_phoenix_server()

    if enable_tracing:
        setup_phoenix_tracing()

    return session


def get_phoenix_url():
    """Get the Phoenix UI URL for viewing traces."""
    return "http://localhost:6006"


def shutdown_phoenix():
    """Gracefully shutdown Phoenix session."""
    global _phoenix_session, _is_instrumented

    if _phoenix_session:
        try:
            # Suppress cleanup errors on Windows
            import warnings
            import tempfile

            # Ignore ResourceWarnings about unclosed files
            warnings.filterwarnings('ignore', category=ResourceWarning)

            _phoenix_session.close()
            print("[Phoenix] Session closed")
        except Exception:
            # Silently ignore cleanup errors
            pass
        finally:
            _phoenix_session = None
            _is_instrumented = False

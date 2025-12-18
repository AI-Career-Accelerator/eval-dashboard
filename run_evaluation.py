"""
Clean evaluation wrapper - Suppresses harmless Windows cleanup errors
Use this instead of core/evaluate.py for a cleaner output
"""
import sys
import os

def main():
    """Run evaluation with error suppression."""
    # Suppress stderr during exit (Phoenix cleanup warnings)
    import io
    import contextlib

    try:
        # Import and run evaluation
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from core import evaluate

        # Run the evaluation
        evaluate.main()

    except SystemExit:
        # Normal exit
        pass
    except Exception as e:
        # Real errors should still be shown
        print(f"Error during evaluation: {e}")
        return 1

    # Success - suppress any cleanup errors
    return 0

if __name__ == "__main__":
    # Capture original stderr
    import sys
    import atexit

    # Register cleanup that suppresses final errors
    def suppress_cleanup_errors():
        """Suppress harmless Windows file cleanup errors."""
        import os
        # Redirect stderr to devnull during cleanup
        if os.name == 'nt':  # Windows only
            sys.stderr = open(os.devnull, 'w')

    # This runs after evaluate.main() completes but before Python cleanup
    atexit.register(suppress_cleanup_errors)

    # Run evaluation
    exit_code = main()
    sys.exit(exit_code)

# run_litellm.py
from dotenv import load_dotenv
import os
import subprocess

# Load .env file
load_dotenv()
print(os.environ.get("AZURE_ANTHROPIC_BASE"))

# Now start LiteLLM Proxy
subprocess.run(["litellm", "--config", "config/litellm_config.yaml", "--detailed_debug"])


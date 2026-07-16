"""Central configuration for the application.

Imported first by every network-touching module, so this is where we make
Python trust the OS certificate store. On machines behind a TLS-inspecting
proxy (corporate Zscaler-style setups) the proxy's root CA lives in the OS
trust store but not in certifi's bundle, so Groq / HuggingFace calls fail with
CERTIFICATE_VERIFY_FAILED. truststore fixes that without disabling verification;
it's a no-op on a normal network. Best-effort: if truststore isn't installed we
carry on with the default cert bundle.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

try:
    import truststore

    truststore.inject_into_ssl()
except Exception:  # truststore missing or injection failed -> default certs
    pass

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT_DIR / "data"
KB_DIR = ROOT_DIR / "knowledge-base"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

LLM_TEMPERATURE = 0.0
LLM_SEED = 42

TOP_K_CHUNKS = 3
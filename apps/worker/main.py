import os
import logging
import warnings
from dotenv import load_dotenv

# Suppress harmless aiohttp task cancellation warnings from Langchain / Google GenAI SDKs
warnings.filterwarnings("ignore", message="coroutine 'ClientResponse.json' was never awaited", category=RuntimeWarning)

# Load .env FIRST — before any Google/Firebase imports so emulator vars are set
load_dotenv()

# Configure structured logging so every agent log is visible
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("worker")

# Suppress noisy google_genai logs
logging.getLogger("google_genai").setLevel(logging.WARNING)

# Propagate emulator host to os.environ immediately (dotenv may have loaded it)
_firestore_host = os.environ.get("FIRESTORE_EMULATOR_HOST")
_pubsub_host = os.environ.get("PUBSUB_EMULATOR_HOST")

if _firestore_host:
    os.environ["FIRESTORE_EMULATOR_HOST"] = _firestore_host
    logger.info(f"[Worker] Firestore emulator → {_firestore_host}")
else:
    logger.warning("[Worker] FIRESTORE_EMULATOR_HOST not set — will use real Firestore!")

if _pubsub_host:
    os.environ["PUBSUB_EMULATOR_HOST"] = _pubsub_host
    logger.info(f"[Worker] Pub/Sub emulator → {_pubsub_host}")

_google_api_key = os.environ.get("GOOGLE_API_KEY")
if _google_api_key:
    os.environ["GOOGLE_API_KEY"] = _google_api_key
    logger.info("[Worker] GOOGLE_API_KEY loaded")
else:
    logger.warning("[Worker] GOOGLE_API_KEY not set!")

# ── Merge API App Path for Shared Code ───────────────────────────────────────
import sys
import pkgutil
import importlib

api_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../api"))
if api_path not in sys.path:
    sys.path.append(api_path)

import app as _app_module
api_app_path = os.path.join(api_path, "app")
if hasattr(_app_module, "__path__") and api_app_path not in _app_module.__path__:
    _app_module.__path__.append(api_app_path)

def _merge_paths(base_pkg, source_path):
    for _, name, ispkg in pkgutil.iter_modules([source_path]):
        if ispkg:
            full_name = f"{base_pkg.__name__}.{name}"
            try:
                mod = importlib.import_module(full_name)
                sub_source = os.path.join(source_path, name)
                if hasattr(mod, '__path__') and sub_source not in mod.__path__:
                    mod.__path__.append(sub_source)
                _merge_paths(mod, sub_source)
            except ImportError:
                pass

_merge_paths(_app_module, api_app_path)

# ── FastAPI app ──────────────────────────────────────────────────────────────
from fastapi import FastAPI   # noqa: E402
from app.routers import ingest  # noqa: E402

app = FastAPI(title="OmniMind v2 Worker")
app.include_router(ingest.router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "firestore_emulator": os.environ.get("FIRESTORE_EMULATOR_HOST", "NOT SET"),
        "pubsub_emulator": os.environ.get("PUBSUB_EMULATOR_HOST", "NOT SET"),
    }

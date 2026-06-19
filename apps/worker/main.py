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

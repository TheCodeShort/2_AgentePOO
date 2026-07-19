from pathlib import Path
import os

# -------------------------------------------------
# RUTA BASE DEL PROYECTO
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PDF_NAME = "0_todo_poo.pdf"
PDF_PATH = DATA_DIR / PDF_NAME

# -------------------------------------------------
# CONFIGURACIÓN DEL MODELO
# -------------------------------------------------
MODEL_NAME = "gemini-2.5-flash"
MAX_OUTPUT_TOKENS = 900
TEMPERATURE = 0.2
MAX_RELEVANT_CHUNKS = 4

# -------------------------------------------------
# CONFIGURACIÓN DEL FILTRADO
# -------------------------------------------------
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 120

# Chroma persistente en disco
CHROMA_COLLECTION = "todo_poo"
CHROMA_PERSIST_DIR = BASE_DIR / "chroma_db"

# Reintentos para 429 / RESOURCE_EXHAUSTED
EMBEDDING_BATCH_SIZE = 16
MAX_EMBEDDING_RETRIES = 5
EMBEDDING_BACKOFF_BASE = 2

EMBEDDING_MODEL = "gemini-embedding-2-preview"

# -------------------------------------------------
# API KEY: PC LOCAL + OCI
# -------------------------------------------------
def obtener_api_key() -> str | None:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if api_key:
        os.environ.setdefault("GEMINI_API_KEY", api_key)
        os.environ.setdefault("GOOGLE_API_KEY", api_key)
        return api_key

    try:
        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / ".env")
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

        if api_key:
            os.environ.setdefault("GEMINI_API_KEY", api_key)
            os.environ.setdefault("GOOGLE_API_KEY", api_key)

        return api_key
    except ImportError:
        return None
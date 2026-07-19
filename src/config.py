from pathlib import Path
import os

# Intentamos cargar el archivo .env de forma segura para desarrollo local.
# Si el archivo no existe o python-dotenv no está instalado, fallará silenciosamente
# y el sistema leerá directamente del entorno del SO (lo cual ocurre al desplegar en OCI).
try:
    from dotenv import load_dotenv
    BASE_DIR = Path(__file__).resolve().parent.parent
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

# -------------------------------------------------
# RUTA BASE DEL PROYECTO (Dinámica para local y OCI)
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
    """
    Obtiene la API Key buscando directamente en las variables de entorno del sistema operativo
    (cargadas previamente desde el .env en desarrollo local, o provistas por el entorno en OCI).
    Sincroniza las claves de entorno para asegurar compatibilidad entre Google GenAI SDK y LangChain.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if api_key:
        # Sincronizamos las claves usando asignación directa para sobreescribir posibles llaves viejas
        os.environ["GEMINI_API_KEY"] = api_key
        os.environ["GOOGLE_API_KEY"] = api_key
        return api_key

    return None
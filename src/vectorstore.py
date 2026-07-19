from pathlib import Path
import time

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config import (
    CHROMA_COLLECTION,
    CHROMA_PERSIST_DIR,
    EMBEDDING_BACKOFF_BASE,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_MODEL,
    MAX_EMBEDDING_RETRIES,
    MAX_RELEVANT_CHUNKS,
    PDF_PATH,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    obtener_api_key,
)
from splitter import preparar_chunks_desde_pdf

# verificamos si el archivo existe
def _indice_existe(ruta: Path) -> bool:
    """
    Verifica si el directorio del índice existe, contiene el archivo sqlite
    y tiene documentos reales indexados. Esto evita cargar un índice vacío.
    """
    sqlite_file = ruta / "chroma.sqlite3"
    # Si la carpeta o el archivo de base de datos no existen, el índice no está listo
    if not ruta.exists() or not sqlite_file.exists():
        return False

    try:
        # Inicializamos el vectorstore para verificar cuántos documentos contiene
        embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
        vectorstore = Chroma(
            collection_name=CHROMA_COLLECTION,
            embedding_function=embeddings,
            persist_directory=str(ruta),
        )
        # Consultamos los documentos guardados
        datos = vectorstore.get()
        # Retorna True solo si la base de datos ya tiene fragmentos (IDs) registrados
        return len(datos.get('ids', [])) > 0
    except Exception:
        # Ante cualquier error de conexión o lectura, asumimos que el índice no sirve
        return False


def _crear_documentos(chunks: list[str], source_name: str) -> list[Document]:
    return [
        Document(
            page_content=chunk,
            metadata={"source": source_name, "chunk": i + 1},
        )
        for i, chunk in enumerate(chunks)
    ]


def _indexar_con_reintentos(vectorstore: Chroma, documentos: list[Document]) -> None:
    for inicio in range(0, len(documentos), EMBEDDING_BATCH_SIZE):
        lote = documentos[inicio:inicio + EMBEDDING_BATCH_SIZE]
        intento = 0

        while True:
            try:
                vectorstore.add_documents(lote)
                break
            except Exception as exc:
                texto_error = str(exc)
                es_rate_limit = "429" in texto_error or "RESOURCE_EXHAUSTED" in texto_error

                if not es_rate_limit or intento >= MAX_EMBEDDING_RETRIES:
                    raise

                espera = min(60, EMBEDDING_BACKOFF_BASE ** intento)
                print(f"⏳ Límite temporal al indexar lote {inicio // EMBEDDING_BATCH_SIZE + 1}. Reintento en {espera}s...")
                time.sleep(espera)
                intento += 1


def crear_retriever_desde_pdf(
    ruta_pdf: str = str(PDF_PATH),
    k: int = MAX_RELEVANT_CHUNKS,
):
    # Validamos que se tenga una API KEY de Gemini configurada antes de iniciar
    if not obtener_api_key():
        raise RuntimeError("No se detectó GEMINI_API_KEY / GOOGLE_API_KEY.")

    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    persist_dir = Path(CHROMA_PERSIST_DIR)

    # Si la base de datos existe y tiene datos válidos, la cargamos directamente para ahorrar tokens y tiempo
    if _indice_existe(persist_dir):
        vectorstore = Chroma(
            collection_name=CHROMA_COLLECTION,
            embedding_function=embeddings,
            persist_directory=str(persist_dir),
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        return retriever, f"Índice local cargado desde {persist_dir}"

    # Si no existe o estaba vacía/corrupta, limpiamos el directorio anterior para evitar conflictos
    import shutil
    if persist_dir.exists():
        try:
            shutil.rmtree(persist_dir)
            print(f"🧹 Limpiando índice anterior vacío o incompleto en {persist_dir}...")
        except Exception as e:
            print(f"⚠️ Advertencia al limpiar la carpeta de la base de datos: {e}")

    # Inicializamos una base de datos limpia de Chroma
    vectorstore = Chroma(
        collection_name=CHROMA_COLLECTION,
        embedding_function=embeddings,
        persist_directory=str(persist_dir),
    )

    # Procesamos el PDF aplicando el filtro de limpieza y dividiéndolo en fragmentos (chunks)
    chunks = preparar_chunks_desde_pdf(
        ruta_pdf=ruta_pdf,
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    if not chunks:
        raise ValueError("El PDF no generó chunks.")

    # Convertimos los fragmentos de texto planos en objetos Document de LangChain
    documentos = _crear_documentos(chunks, Path(ruta_pdf).name)
    
    # Generamos los embeddings y los guardamos en la base de datos Chroma local
    _indexar_con_reintentos(vectorstore, documentos)

    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    return retriever, f"Índice creado con {len(chunks)} chunks y guardado en {persist_dir}"
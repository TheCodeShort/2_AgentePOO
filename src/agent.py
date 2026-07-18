import os
import re
import sys
import unicodedata
from pathlib import Path

from google import genai
from google.genai import types

# from langchain_text_splitters import RecursiveCharacterTextSplitter

# Cargamos los chunks ya preparados desde splitter.py
try:
    from splitter import preparar_chunks_desde_pdf
except ImportError:
    print("❌ Error: No se encontró 'splitter.py' en la carpeta src.")
    sys.exit(1)


def normalizar_texto(texto: str) -> str:
    """
    Convierte el texto a una forma más fácil de comparar:
    - minúsculas
    - sin tildes
    - sin signos raros
    """
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def buscar_chunks_relevantes(pregunta: str, chunks: list[str], cantidad: int = 4) -> list[str]:
    """
    Busca los fragmentos más relevantes usando coincidencia por palabras clave.
    Esto ayuda a no mandar todo el PDF al modelo y ahorrar tokens.
    """
    stopwords = {
        "que", "cual", "cuales", "como", "cuando", "donde", "porque", "para", "por",
        "del", "de", "la", "el", "los", "las", "una", "uno", "unos", "unas",
        "sobre", "este", "esta", "estas", "estos", "eso", "esa", "ese", "hay",
        "ser", "estar", "tiene", "tener", "puede", "puedo", "puedes", "hacer",
        "hace", "hacen", "mas", "menos"
    }

    pregunta_norm = normalizar_texto(pregunta)
    palabras = [
        palabra
        for palabra in pregunta_norm.split()
        if len(palabra) > 3 and palabra not in stopwords
    ]

    chunks_con_puntaje = []

    for chunk in chunks:
        chunk_norm = normalizar_texto(chunk)
        puntaje = sum(1 for palabra in palabras if palabra in chunk_norm)

        if puntaje > 0:
            chunks_con_puntaje.append((puntaje, chunk))

    # Ordenar por relevancia descendente
    chunks_con_puntaje.sort(key=lambda x: x[0], reverse=True)

    resultados = [chunk for _, chunk in chunks_con_puntaje[:cantidad]]

    # Si no encontró nada, usamos los primeros fragmentos como respaldo
    if not resultados:
        resultados = chunks[:cantidad]

    return resultados


# -----------------------------
# 2) CONFIGURACIÓN DE API KEY
# -----------------------------
def obtener_api_key() -> str | None:
    """
    Intenta obtener GEMINI_API_KEY primero desde el sistema.
    Si no existe, intenta cargarla desde .env.
    Esto sirve tanto para PC local como para OCI.
    """
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            api_key = os.environ.get("GEMINI_API_KEY")
        except ImportError:
            pass

    return api_key


# -----------------------------
# 3) AGENTE INTERACTIVO
# -----------------------------
def iniciar_agente_interactivo(todos_los_chunks: list[str]) -> None:
    """
    Bucle de chat interactivo.
    Usa Gemini con contexto reducido para responder sobre el PDF.
    """
    api_key_gemini = obtener_api_key()

    if not api_key_gemini:
        print("\n❌ ERROR DE CONFIGURACIÓN:")
        print("No se detectó la variable GEMINI_API_KEY.")
        print("- En tu PC: revisa tu archivo .env")
        print('- En OCI: define la variable en el entorno con export GEMINI_API_KEY="tu_llave"')
        return

    client = genai.Client(api_key=api_key_gemini)

    system_instruction = (
        "Eres un asistente académico experto en el documento proporcionado. "
        "Responde solo con información respaldada por el contexto. "
        "Si la respuesta no aparece en el texto, dilo claramente. "
        "Sé claro, breve y preciso."
    )

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        max_output_tokens=900,
        temperature=0.2,
    )

    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=config
    )

    print("\n========================================================")
    print("🤖 AGENTE ACTIVO")
    print("Escribe tu pregunta sobre el documento. Para salir: salir")
    print("========================================================\n")

    while True:
        try:
            pregunta_usuario = input("Tú: ").strip()

            if pregunta_usuario.lower() in {"salir", "exit", "quit"}:
                print("\n🤖 Agente: ¡Hasta luego! Éxitos en tu estudio.")
                break

            if not pregunta_usuario:
                continue

            print("⏳ Buscando contexto relevante en el PDF...")

            chunks_contexto = buscar_chunks_relevantes(
                pregunta_usuario,
                todos_los_chunks,
                cantidad=4
            )

            contexto_formateado = "\n---\n".join(chunks_contexto)

            prompt_final = (
                "Usa SOLO el contexto siguiente si realmente sirve para responder.\n\n"
                f"CONTEXTO DEL DOCUMENTO:\n{contexto_formateado}\n\n"
                f"PREGUNTA DEL USUARIO:\n{pregunta_usuario}\n\n"
                "Si la respuesta no está en el contexto, responde: "
                "'No encuentro esa información en el documento.'"
            )

            print("🧠 Generando respuesta...")

            response = chat.send_message(prompt_final)

            print("\n🤖 Agente:")
            print(response.text)
            print("-" * 56 + "\n")

        except Exception as error:
            print(f"\n❌ Ocurrió un inconveniente durante el chat: {error}\n")


# -----------------------------
# 4) BLOQUE PRINCIPAL
# -----------------------------
if __name__ == "__main__":
    ruta_pdf = str(Path(__file__).resolve().parent.parent / "data" / "0_todo_poo.pdf")

    print("⚙️ Paso 1: Preparando chunks desde el PDF...")

    try:
        chunks_libro = preparar_chunks_desde_pdf(
            ruta_pdf=ruta_pdf,
            chunk_size=800,
            chunk_overlap=80
        )
    except Exception as error:
        print(f"❌ Error preparando el documento: {error}")
        sys.exit(1)

    print(f"✅ Documento preparado con éxito. Total de chunks: {len(chunks_libro)}")

    iniciar_agente_interactivo(chunks_libro)
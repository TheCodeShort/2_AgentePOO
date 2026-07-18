# para manejar rutas de archivos en los diferentes SO como la => "/"
from pathlib import Path
# desifrar la estructura de un PDF
from pypdf import PdfReader
import re

# Importamos la herramienta industrial de Chunking de LangChain
from langchain_text_splitters import RecursiveCharacterTextSplitter


def cargar_pdf(ruta_pdf: str) -> str:
    """Lee un PDF, elimina la grasa digital y devuelve el texto optimizado."""
    ruta = Path(ruta_pdf)

    if not ruta.exists():
        raise FileNotFoundError(f"No existe el archivo: {ruta_pdf}")

    lector = PdfReader(str(ruta))
    texto_total = []

    # Procesamos las páginas limpiando el texto de raíz
    for pagina in lector.pages:
        texto = pagina.extract_text()
        if texto:
            # 1. Elimina encabezados y números de página sueltos
            texto = re.sub(r"^\s*(Página|Pag|Pág)?\s*\d+\s*$", "", texto, flags=re.MULTILINE)

            # 2. Reemplazar espacios dobles y tabulaciones por espacios simples
            texto = re.sub(r"[ \t]+", " ", texto)

            # Elimina enlaces web (URLs) que inflan los tokens con letras aleatorias
            texto = re.sub(r'https?://\S+|www\.\S+', '', texto)
            # Elimina líneas decorativas de código comunes (ej: ---------- o =========)
            texto = re.sub(r'[-_+=*]{3,}', '', texto)

            # 3. Normalizar comillas y guiones extraños del formato PDF
            texto = (
                texto.replace("“", '"')
                .replace("”", '"')
                .replace("—", "-")
                .replace("•", "-")
            )

            texto_total.append(texto)

    # Unimos el libro respetando saltos de línea normales
    contenido_limpio = "\n".join(texto_total)

    # Evitamos ráfagas de más de 2 saltos de línea seguidos
    contenido_limpio = re.sub(r"\n{3,}", "\n\n", contenido_limpio)

    print(f"📄 Total de páginas procesadas en el PDF: {len(lector.pages)}")
    return contenido_limpio.strip()


if __name__ == "__main__":
    # --- PASO 1: TU LIMPIEZA PERSONALIZADA ---
    pdf = "../data/0_todo_poo.pdf"
    texto_magro = cargar_pdf(pdf)

    print("\n=== 1. PDF PROCESADO Y OPTIMIZADO ===")
    print(f"Cantidad de caracteres limpios: {len(texto_magro)}")  # Tus 272,791 caracteres

    # --- PASO 2: EL CHUNKING INDUSTRIAL DE LANGCHAIN ---
    print("\n=== 2. APLICANDO CHUNKING CON LANGCHAIN ===")

    # Configuramos el picador el CHUNKs inteligente de texto de LangChain
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,  # Tamaño máximo de caracteres por pedazo (~350 palabras) 1500
        chunk_overlap=80,  # Margen para que las frases no queden cortadas a la mitad 150
        length_function=len,  # Mide el tamaño basándose en la longitud del texto
        separators=["\n\n", "\n", " ", ""]  # Corta primero en párrafos, luego en frases
    )

    # Le pasamos tu texto limpio al formateador de LangChain
    # split_text acepta una cadena de texto directo (str) y devuelve una lista de chunks
    chunks_industriales = text_splitter.split_text(texto_magro)

    print(f"🔥 LangChain recibio tu texto limpio y lo picó en {len(chunks_industriales)} fragmentos inteligentes.")
    print("¡Estructura perfecta lograda al 80/20!")

    # Muestra visual de cómo quedó el primer pedacito inteligente
    print("\n--- MUESTRA DEL PRIMER CHUNK INDUSTRIAL ---")
    # print(chunks_industriales[0][:400] + "...")

    # Cambia la muestra visual por esta para ver más contenido:
    # print("\n--- PRIMEROS 3 CHUNKS INDUSTRIALES ---")
    # for i in range(3):
    #     print(f"\n--- FRAGMENTO {i} ---")
    #     print(chunks_industriales[i])

   # print(type(chunks_industriales))
   #  print(f"📉 Tu libro fue dividido en {len(chunks_industriales)} fragmentos de alta densidad.")
   #  print("Cada fragmento ahora viaja ultra ligero. ¡El desperdicio de tokens es CERO!")

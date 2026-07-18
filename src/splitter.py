from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from loader import cargar_pdf


def dividir_texto(texto: str,
                  chunk_size: int = 800,
                  chunk_overlap: int = 80) -> list[str]:

    """
    Divide un texto grande en fragmentos más pequeños y útiles para búsqueda.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )

    return text_splitter.split_text(texto)


def preparar_chunks_desde_pdf(ruta_pdf: str, chunk_size: int = 800, chunk_overlap: int = 80) -> list[str]:
    """
    Lee el PDF con loader.py y luego lo divide en chunks.
    """
    texto = cargar_pdf(ruta_pdf)
    return dividir_texto(texto, chunk_size=chunk_size, chunk_overlap=chunk_overlap)


def _ruta_pdf() -> str:
    """
    Ruta por defecto del PDF dentro del proyecto.
    """
    return str(Path(__file__).resolve().parent.parent / "data" / "0_todo_poo.pdf")


if __name__ == "__main__":
    pdf = _ruta_pdf()

    texto = cargar_pdf(pdf)
    chunks = dividir_texto(texto, chunk_size=800, chunk_overlap=80)

    print("PDF procesado y dividido correctamente.")
    print(f"Cantidad de chunks generados: {len(chunks)}")

    print("\n--- PRIMER CHUNK ---\n")
    print(chunks[0][:4000])
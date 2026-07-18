from pathlib import Path
import sys

from splitter import preparar_chunks_desde_pdf
from agent import iniciar_agente_interactivo


def main() -> None:
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


if __name__ == "__main__":
    main()
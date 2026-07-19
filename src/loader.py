# para manejar rutas de archivos en los diferentes SO como la => "/"
from pathlib import Path
# desifrar la estructura de un PDF
from pypdf import PdfReader
import re



def cargar_pdf(ruta_pdf: str) -> str:
    """
    Lee un PDF de forma segura, maneja excepciones de entrada/salida (E/S),
    elimina la grasa digital y devuelve el texto optimizado.
    Lanza excepciones legibles si el archivo está corrupto o vacío.
    """
    ruta = Path(ruta_pdf)

    # Validación preventiva antes de intentar abrir el archivo
    if not ruta.exists():
        raise FileNotFoundError(f"El archivo PDF especificado no existe en la ruta: {ruta_pdf}")

    # Controlamos fallos físicos al abrir la estructura del archivo PDF
    try:
        lector = PdfReader(str(ruta))
    except Exception as e:
        raise RuntimeError(f"No se pudo inicializar la lectura del PDF ({ruta_pdf}). Verifique si el archivo está corrupto: {e}")

    texto_total = []

    # Procesamos las páginas individualmente
    for i, pagina in enumerate(lector.pages):
        try:
            texto = pagina.extract_text()
            if texto:
                # 1. Elimina encabezados y números de página sueltos
                texto = re.sub(r"^\s*(Página|Pag|Pág)?\s*\d+\s*$", "", texto, flags=re.MULTILINE)

                # 2. Reemplazar espacios dobles y tabulaciones por espacios simples
                texto = re.sub(r"[ \t]+", " ", texto)

                # 3. Elimina enlaces web (URLs) que inflan los tokens con letras aleatorias
                texto = re.sub(r'https?://\S+|www\.\S+', '', texto)

                # 4. Elimina líneas decorativas de código comunes (ej: ---------- o =========)
                texto = re.sub(r'[-_+=*]{3,}', '', texto)

                # 5. Normalizar comillas y guiones extraños del formato PDF
                texto = (
                    texto.replace("“", '"')
                    .replace("”", '"')
                    .replace("—", "-")
                    .replace("•", "-")
                )

                texto_total.append(texto.strip())
        except Exception as e:
            # Si falla la extracción de una sola página, avisamos en consola pero permitimos continuar con el resto
            print(f"⚠️ Advertencia: No se pudo extraer texto de la página {i+1} en {ruta_pdf}: {e}")

    # Unimos el libro respetando saltos de línea normales
    contenido_limpio = "\n".join(texto_total)

    # Evitamos ráfagas de más de 2 saltos de línea seguidos
    contenido_limpio = re.sub(r"\n{3,}", "\n\n", contenido_limpio)
    contenido_limpio = contenido_limpio.strip()

    # Si tras la limpieza el resultado es vacío, alertamos que el PDF no contiene texto copiable o es imagen
    if not contenido_limpio:
        raise ValueError(
            f"El archivo PDF '{ruta_pdf}' se leyó correctamente, pero no se pudo extraer texto útil. "
            "Esto ocurre normalmente con PDFs escaneados (que contienen solo imágenes) o protegidos contra copia."
        )

    return contenido_limpio

def _ruta_pdf() -> str:
    """
    Ruta por defecto del PDF dentro del proyecto.
    """
    return str(Path(__file__).resolve().parent.parent / "data" / "0_todo_poo.pdf")

if __name__ == "__main__":
    pdf = _ruta_pdf()
    #pdf = "../data/0_todo_poo.pdf"
    texto = cargar_pdf(pdf)

    print("PDF leído correctamente.")
    print(f"Cantidad de caracteres limpios: {len(texto)}")
    print("\n--- INICIO DEL TEXTO ---\n")
    print(texto[:2000])

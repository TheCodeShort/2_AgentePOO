# para manejar rutas de archivos en los diferentes SO como la => "/"
from pathlib import Path
# desifrar la estructura de un PDF
from pypdf import PdfReader
import re



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
        if  texto:
            # 1. Elimina encabezados y números de página sueltos
            texto = re.sub(r"^\s*(Página|Pag|Pág)?\s*\d+\s*$", "", texto, flags=re.MULTILINE)

            # 2. Reemplazar espacios dobles y tabulaciones por espacios simples
            texto = re.sub(r"[ \t]+", " ", texto)

            # 3. Elimina enlaces web (URLs) que inflan los tokens con letras aleatorias
            texto = re.sub(r'https?://\S+|www\.\S+', '', texto)

            # 4. Elimina líneas decorativas de código comunes (ej: ---------- o =========)
            texto = re.sub(r'[-_+=*]{3,}', '', texto)

            # 5.Normalizar comillas y guiones extraños del formato PDF
            texto = (
                texto.replace("“", '"')
                .replace("”", '"')
                .replace("—", "-")
                .replace("•", "-")
            )

            texto_total.append(texto.strip())


    # Unimos el libro respetando saltos de línea normales
    contenido_limpio = "\n".join(texto_total)

    # Evitamos ráfagas de más de 2 saltos de línea seguidos
    contenido_limpio = re.sub(r"\n{3,}", "\n\n", contenido_limpio)

    return contenido_limpio.strip()

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

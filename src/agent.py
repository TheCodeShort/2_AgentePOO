import os
import sys
from google import genai
from google.genai import types
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. IMPORTACIÓN COHERENTE: Traemos tu limpiador optimizado
from loader import cargar_pdf


def buscar_chunks_relevantes(pregunta: str, chunks: list, cantidad: int = 4) -> list:
    """
    Buscador básico y ultra rápido (80/20).
    Filtra los fragmentos del libro que contienen palabras clave de la pregunta.
    Esto evita enviarle los 200+ chunks a Gemini, ahorrando miles de tokens.
    """
    palabras_clave = [p.lower() for p in pregunta.split() if len(p) > 3]
    chunks_con_puntaje = []

    for chunk in chunks:
        # Contamos cuántas palabras de la pregunta aparecen en este fragmento
        puntaje = sum(1 for palabra in palabras_clave if palabra in chunk.lower())
        if puntaje > 0:
            chunks_con_puntaje.append((puntaje, chunk))

    # Ordenamos de mayor a menor relevancia
    chunks_con_puntaje.sort(key=lambda x: x[0], reverse=True)

    # Extraemos solo el texto de los mejores resultados
    resultados = [chunk for puntaje, chunk in chunks_con_puntaje[:cantidad]]

    # Si la búsqueda no encontró nada, pasamos los primeros fragmentos por defecto
    if not resultados:
        resultados = chunks[:cantidad]

    return resultados


def consultar_gemini_con_contexto(pregunta_usuario: str, fragmentos_libro: list) -> str:
    """Se conecta con Gemini enviando únicamente las cápsulas de texto necesarias."""

    # Inicializa el cliente oficial buscando automáticamente la variable GEMINI_API_KEY
    client = genai.Client()

    # Juntamos los fragmentos seleccionados en una sola cadena de texto clara
    contexto_inyectado = "\n---\n".join(fragmentos_libro)

    # ESTRUCTURA INDUSTRIAL DEL PROMPT: Le damos el rol, el contexto magro y la pregunta
    system_instruction = (
        "Eres un Agente experto en programación. Tu única fuente de verdad es el documento proveído. "
        "Utiliza el siguiente contexto técnico para responder la pregunta del usuario de forma detallada, "
        "clara y estructurada. Si el contexto no contiene la información para responder, dilo amablemente."
    )

    prompt_final = f"CONTEXTO DEL DOCUMENTO:\n{contexto_inyectado}\n\nPREGUNTA:\n{pregunta_usuario}"

    # Configuración de optimización de salida (max_tokens generoso para respuestas largas)
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        max_output_tokens=2000,  # <-- Permite respuestas largas y bien explicadas
        temperature=0.3,  # <-- Temperatura baja para que sea preciso y no invente cosas (alucine)
    )

    # Realizamos la llamada al modelo más rápido, económico y eficiente: gemini-2.5-flash
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt_final,
        config=config
    )

    return response.text


if __name__ == "__main__":
    # --- PASO 1: CAPA DE DATOS ---
    ruta_libro = "../data/0_todo_poo.pdf"
    print("⏳ Leyendo y optimizando el PDF base...")
    texto_limpio = cargar_pdf(ruta_libro)

    # --- PASO 2: CHUNKING INDUSTRIAL ---
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,  # Cápsulas de bajo consumo
        chunk_overlap=80,  # Solapamiento proporcional
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    todos_los_chunks = text_splitter.split_text(texto_limpio)
    print(f"✅ Libro picado con éxito en {len(todos_los_chunks)} fragmentos.")

    # --- PASO 3: PREGUNTA DEL USUARIO ---
    pregunta = "¿Qué es el acoplamiento y la cohesión y por qué son importantes?"
    print(f"\n🙋‍♂️ Usuario pregunta: {pregunta}")

    # --- PASO 4: FILTRADO QUIRÚRGICO (Ahorro de tokens de entrada) ---
    chunks_relevantes = buscar_chunks_relevantes(pregunta, todos_los_chunks, cantidad=4)
    print(f"🎯 Seleccionados los {len(chunks_relevantes)} fragmentos más cercanos a la pregunta.")

    # --- PASO 5: LLAMADA A LA IA ---
    print("🤖 El Agente está procesando la respuesta con Gemini...")
    try:
        respuesta_ia = consultar_gemini_con_contexto(pregunta, chunks_relevantes)
        print("\n=== 📄 RESPUESTA DEL AGENTE ===")
        print(respuesta_ia)
        print("================================\n")
        print("🎉 ¡Prueba inicial completada con éxito y optimización al 100%!")
    except Exception as e:
        print(f"\n❌ Error al conectar con Gemini: {e}")
        print("Asegúrate de haber configurado tu GEMINI_API_KEY correctamente en la terminal.")

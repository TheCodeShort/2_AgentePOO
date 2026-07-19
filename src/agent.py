import sys

from google import genai
from google.genai import types


from config import (
    MODEL_NAME,
    MAX_OUTPUT_TOKENS,
    TEMPERATURE,
    obtener_api_key,
)

def generar_documento_hipotetico(client: genai.Client, pregunta: str) -> str:
    """
    Genera un documento o párrafo académico hipotético aproximado (HyDE)
    para optimizar la precisión de la búsqueda vectorial semántica.
    """
    prompt = (
        f"Escribe un párrafo académico corto que responda a la siguiente pregunta: '{pregunta}'. "
        "No digas 'según el texto' ni agregues introducciones. Escribe la explicación técnica directamente, "
        "como si fuera un fragmento extraído de un libro técnico de programación."
    )

    config_rapida = types.GenerateContentConfig(
        max_output_tokens=120,  # Limitamos la salida para ser eficientes en tokens
        temperature=0.4,       # Temperatura baja para coherencia técnica
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=config_rapida
        )
        return response.text.strip()
    except Exception as e:
        # Fallback seguro: si la API falla, notificamos y buscamos usando la pregunta original
        print(f"⚠️ Advertencia HyDE: No se pudo generar el documento hipotético ({e}). Usando pregunta original.")
        return pregunta


def iniciar_agente_interactivo(retriever) -> None:
    """Bucle de chat que usa un retriever semántico para armar contexto."""
    api_key_gemini = obtener_api_key()

    if not api_key_gemini:
        print("\n❌ ERROR DE CONFIGURACIÓN:")
        print("No se detectó la variable GEMINI_API_KEY / GOOGLE_API_KEY.")
        print("- En tu PC: revisa tu archivo .env")
        print('- En OCI: define la variable en el entorno con export GEMINI_API_KEY="tu_llave"')
        return

    client = genai.Client(api_key=api_key_gemini)

    # Instrucción del sistema para forzar el anclaje de las respuestas en el contexto provisto
    system_instruction = (
        "Eres un asistente académico experto en el documento proporcionado. "
        "Responde solo con información respaldada por el contexto. "
        "Si la respuesta no está en el texto, dilo claramente. "
        "Sé claro, breve y preciso."
    )

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        temperature=TEMPERATURE,
    )

    # Historial conversacional limpio: guardará solo preguntas y respuestas para mantener coherencia
    # sin almacenar los pesados fragmentos de contexto recuperados (evitando fugas y altos costos de tokens)
    historial_conversacion = []

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

            print("⏳ Optimizando consulta para búsqueda vectorial (HyDE)...")
            pregunta_mejorada = generar_documento_hipotetico(client, pregunta_usuario)

            print("⏳ Buscando contexto relevante en el PDF...")
            documentos_relevantes = retriever.invoke(pregunta_mejorada)
            contexto_formateado = "\n---\n".join(
                doc.page_content for doc in documentos_relevantes
            )

            if not contexto_formateado.strip():
                print("\n🤖 Agente:")
                print("No encuentro esa información en el documento.")
                print("-" * 56 + "\n")
                continue

            # Construimos la secuencia de turnos para el modelo
            # 1. Agregamos el historial limpio de turnos anteriores (rol: 'user' y 'model')
            contents = []
            for msg in historial_conversacion:
                contents.append(
                    types.Content(
                        role=msg["role"],
                        parts=[types.Part.from_text(text=msg["text"])]
                    )
                )

            # 2. Creamos el prompt final que integra el RAG únicamente para el turno actual
            prompt_final = (
                "Usa SOLO el contexto siguiente si realmente sirve para responder.\n\n"
                f"CONTEXTO DEL DOCUMENTO:\n{contexto_formateado}\n\n"
                f"PREGUNTA DEL USUARIO:\n{pregunta_usuario}\n\n"
                "Si la respuesta no está en el contexto, responde exactamente: "
                "'No encuentro esa información en el documento.'"
            )

            # 3. Lo añadimos como el mensaje del usuario en el turno actual
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt_final)]
                )
            )

            print("🧠 Generando respuesta...")

            # Realizamos una llamada stateless para no acumular los contextos viejos en el backend de la API
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=config
            )

            respuesta_texto = response.text

            print("\n🤖 Agente:")
            print(respuesta_texto)
            print("-" * 56 + "\n")

            # Guardamos la conversación limpia en el historial local del proceso
            historial_conversacion.append({"role": "user", "text": pregunta_usuario})
            historial_conversacion.append({"role": "model", "text": respuesta_texto})

        except Exception as error:
            print(f"\n❌ Ocurrió un inconveniente durante el chat: {error}\n")
import sys

from google import genai
from google.genai import types


from config import (
    MODEL_NAME,
    MAX_OUTPUT_TOKENS,
    TEMPERATURE,
    obtener_api_key,
)

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

    chat = client.chats.create(
        model=MODEL_NAME,
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

            documentos_relevantes = retriever.invoke(pregunta_usuario)
            contexto_formateado = "\n---\n".join(
                doc.page_content for doc in documentos_relevantes
            )

            if not contexto_formateado.strip():
                print("\n🤖 Agente:")
                print("No encuentro esa información en el documento.")
                print("-" * 56 + "\n")
                continue

            prompt_final = (
                "Usa SOLO el contexto siguiente si realmente sirve para responder.\n\n"
                f"CONTEXTO DEL DOCUMENTO:\n{contexto_formateado}\n\n"
                f"PREGUNTA DEL USUARIO:\n{pregunta_usuario}\n\n"
                "Si la respuesta no está en el contexto, responde exactamente: "
                "'No encuentro esa información en el documento.'"
            )

            print("🧠 Generando respuesta...")

            response = chat.send_message(prompt_final)

            print("\n🤖 Agente:")
            print(response.text)
            print("-" * 56 + "\n")

        except Exception as error:
            print(f"\n❌ Ocurrió un inconveniente durante el chat: {error}\n")
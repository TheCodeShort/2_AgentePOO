import streamlit as st
from google import genai
from google.genai import types

# Importaciones de la lógica de negocio actual
from config import MODEL_NAME, MAX_OUTPUT_TOKENS, TEMPERATURE, obtener_api_key
from vectorstore import crear_retriever_desde_pdf
from agent import generar_documento_hipotetico

# 1. Configuración básica de la aplicación
st.set_page_config(
    page_title="Asistente Académico POO",
    page_icon="🤖",
    layout="centered"
)

st.title("📚 Asistente de Programación Orientada a Objetos")
st.caption("Consulta el material académico del curso utilizando Inteligencia Artificial.")

# 2. Inicialización de recursos compartidos (Cache para evitar reruns lentos)
@st.cache_resource
def inicializar_recursos():
    """Carga el índice ChromaDB y valida la API Key de Gemini."""
    retriever, estado_db = crear_retriever_desde_pdf()
    api_key_gemini = obtener_api_key()
    
    if not api_key_gemini:
        st.error("❌ Error de configuración: No se detectó GEMINI_API_KEY en el entorno.")
        st.stop()
        
    client = genai.Client(api_key=api_key_gemini)
    return retriever, client, estado_db

try:
    retriever, client, estado_carga = inicializar_recursos()
    # Mostramos el estado del índice de forma discreta en la barra lateral
    st.sidebar.success(f"Configuración: {estado_carga}")
except Exception as error:
    st.error(f"❌ Error al iniciar el índice: {error}")
    st.stop()

# 3. Inicialización del historial en session_state
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. Renderizar el historial conversacional existente
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["text"])

# 5. Captura y procesamiento de nuevos mensajes
if pregunta_usuario := st.chat_input("Escribe tu pregunta sobre el documento..."):
    # Renderizar el mensaje de inmediato
    with st.chat_message("user"):
        st.markdown(pregunta_usuario)
    
    # Procesar la respuesta con el spinner de carga
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                # A. Optimización de consulta (HyDE)
                # Envolvemos esta llamada dentro del try-except robusto global
                pregunta_mejorada = generar_documento_hipotetico(client, pregunta_usuario)
                
                # B. Búsqueda semántica en el PDF indexado
                documentos_relevantes = retriever.invoke(pregunta_mejorada)
                contexto_formateado = "\n---\n".join(
                    doc.page_content for doc in documentos_relevantes
                )
                
                if not contexto_formateado.strip():
                    respuesta_texto = "No encuentro esa información en el documento."
                else:
                    # C. Construir secuencia de turnos stateless para evitar inflación de tokens
                    contents = []
                    for msg in st.session_state.messages:
                        # Mapeo estricto: Streamlit 'assistant' -> Gemini 'MODEL', 'user' -> 'USER'
                        role_mapeado = "MODEL" if msg["role"] == "assistant" else "USER"
                        contents.append(
                            types.Content(
                                role=role_mapeado,
                                parts=[types.Part.from_text(text=msg["text"])]
                            )
                        )
                    
                    # Inyectamos el RAG exclusivamente en el prompt final del turno activo
                    prompt_final = (
                        "Usa SOLO el contexto siguiente si realmente sirve para responder.\n\n"
                        f"CONTEXTO DEL DOCUMENTO:\n{contexto_formateado}\n\n"
                        f"PREGUNTA DEL USUARIO:\n{pregunta_usuario}\n\n"
                        "Si la respuesta no está en el contexto, responde exactamente: "
                        "'No encuentro esa información en el documento.'"
                    )
                    contents.append(
                        types.Content(
                            role="USER",
                            parts=[types.Part.from_text(text=prompt_final)]
                        )
                    )
                    
                    # D. Configuración y llamada de inferencia a Gemini
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
                    
                    # Llamada crítica a la API de Gemini
                    response = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=contents,
                        config=config
                    )
                    respuesta_texto = response.text
                
                # Mostrar la respuesta final
                st.markdown(respuesta_texto)
                
                # E. Guardar en el historial limpio local de la sesión (evitando re-escribir el RAG)
                st.session_state.messages.append({"role": "user", "text": pregunta_usuario})
                st.session_state.messages.append({"role": "assistant", "text": respuesta_texto})
                
            except Exception as api_error:
                # Escudo Protector de UX: Muestra mensaje empático y limpio si falla la API
                mensaje_error = (
                    "Lo siento, experimentamos un inconveniente temporal con el motor de IA. "
                    "Por favor, intenta realizar otra pregunta o redactarla de forma diferente en unos momentos."
                )
                st.error(mensaje_error)
                
                # Registrar el error técnico en los logs de consola del servidor
                import sys
                print(f"❌ Error crítico en API de Gemini / Inferencia: {api_error}", file=sys.stderr)

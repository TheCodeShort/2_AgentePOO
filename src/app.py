from agent import iniciar_agente_interactivo
from vectorstore import crear_retriever_desde_pdf


def main() -> None:
    print("⚙️ Paso 1: Preparando índice semántico desde el PDF...")

    try:
        retriever, estado = crear_retriever_desde_pdf()
    except Exception as error:
        print(f"❌ Error preparando el documento: {error}")
        raise SystemExit(1)

    print(f"✅ {estado}")

    iniciar_agente_interactivo(retriever)


if __name__ == "__main__":
    main()

    """bueno en este momento tengo un problema basicamente mi codigo en general es
  que una IA me responda con respecto a mi documento pero cuando intententa
  responder al parecer no encuentra el archivo aun asi se ejecuta el codigo
  bien pero cuando uno le pregunta al respecto el dice que no encuentra nada 
  informacion y te alcaro algo y es que antes de que lo modificara si respond
  y funcionaba exelentemente pero mi objetivo es irlo mejorarlo empece con la
  limpiesa del documento de basura para que la IA en este caso GEMINI pueda
  leer el documento si gastar tokens demas por links o caracteres adicionales
  estos los quite y entre otros y despues quise que todo se dividiera en
  fragmentos no se como se llaman pero antes de la modificacion el lo ejecuta
  de manera perfecta y asi hasta llegar a la parte de los vectores asi que
  revisa => @[src] y el documento es @[data] antes de aplicar alguna
  modificaion quiero que me expliques cual es el problema"""
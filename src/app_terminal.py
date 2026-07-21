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


# if __name__ == "__main__":
#     main()
#

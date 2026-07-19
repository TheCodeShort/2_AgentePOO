# para asegurar la configuracion como librerias instaladas y asi evitamos volver a instalarlas a mano o recordar como es el comando por lo general se nobra el archivo asi **requirements.txt** se puede nombrar de manera diferente pero este es el estandar
 comando => pip freeze > requirements.txt


# Para instalar lo que ya se configuro en cuestion de instalacion de librerias y demas
comando => pip install -r requirements.txt


# Para activar el entorno virtual

comando SO_Win-PoweShell => .venv\Scripts\Activate.ps1

comando SO_Win-CMD => .venv\Scripts\activate.bat

comando SO_Win-Linux/Git pero en Window => source .venv/Scripts/activate

comando SO_Linux/macOS => source .venv/bin/activate


# Para desactivar el entorno
deactivate



# Bibliotecas usadas
python -m pip install pypdf  
python -m pip install langchain langchain-text-splitters
python -m pip install google-genai langchain langchain-text-splitters
python -m pip install python-dotenv 
## chroma nos ayudara a convertir todo en enveding y con gemini se traduce 
python -m pip install langchain-chroma langchain-google-genai




import os
import sys
import webbrowser
import threading
import time
import uvicorn
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env local se existir
base_path = os.path.dirname(os.path.abspath(sys.argv[0])) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
env_file = os.path.join(base_path, ".env")
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    load_dotenv()

from app.main import app

def open_browser():
    time.sleep(1.5)
    url = "http://127.0.0.1:8000"
    print(f"\n=======================================================")
    print(f"🚀 ConcurseiroAI Iniciado com Sucesso!")
    print(f"🌐 Acesse no seu navegador: {url}")
    print(f"📖 Documentação da API: {url}/docs")
    print(f"Pressione CTRL+C para encerrar o aplicativo.")
    print(f"=======================================================\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

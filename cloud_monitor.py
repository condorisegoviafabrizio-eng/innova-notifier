import os, json, time, logging, urllib.parse, requests, sys
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

# --- Configuracion (GitHub Secrets) ---
INNOVA_EMAIL = os.getenv("INNOVA_EMAIL"); INNOVA_PASSWORD = os.getenv("INNOVA_PASSWORD")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER"); CALLMEBOT_API_KEY = os.getenv("CALLMEBOT_API_KEY")
BASE_URL = "https://innovafamily.pe"; LOGIN_URL = f"{{BASE_URL}}/Account/Login"
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("InnovaDebug")

def login(session):
    log.info(f"Diagnóstico de acceso para: {{INNOVA_EMAIL}}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9"
    }
    try:
        r = session.get(LOGIN_URL, timeout=30, headers=headers)
        log.info(f"Status: {{r.status_code}}")
        soup = BeautifulSoup(r.text, "html.parser")
        token = soup.find("input", {{"name": "__RequestVerificationToken"}})
        
        if not token:
            log.error("¡TICKET DE SEGURIDAD NO ENCONTRADO!")
            log.info("--- LO QUE VE EL ROBOT (Snippet): ---")
            log.info(r.text[:1000]) # Ver los primeros 1000 caracteres
            log.info("--- FIN DEL SNIPPET ---")
            return False
            
        log.info("Token encontrado. Intentando entrar...")
        data = {{"Correo": INNOVA_EMAIL, "Password": INNOVA_PASSWORD, "__RequestVerificationToken": token["value"]}}
        r = session.post(LOGIN_URL, data=data, timeout=30, allow_redirects=True, headers=headers)
        if "Login" not in r.url:
            log.info("✅ ¡Acceso exitoso!")
            return True
        return False
    except Exception as e:
        log.error(f"Error: {{e}}"); return False

def main():
    if not all([INNOVA_EMAIL, INNOVA_PASSWORD]): sys.exit(1)
    if not login(requests.Session()): sys.exit(1)
    log.info("Robot listo y funcionando.")

if __name__ == "__main__": main()

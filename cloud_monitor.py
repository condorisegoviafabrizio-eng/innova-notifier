import os, json, time, logging, urllib.parse, requests, sys
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

# --- Configuracion (GitHub Secrets) ---
INNOVA_EMAIL = os.getenv("INNOVA_EMAIL")
INNOVA_PASSWORD = os.getenv("INNOVA_PASSWORD")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")
CALLMEBOT_API_KEY = os.getenv("CALLMEBOT_API_KEY")

BASE_URL = "https://innovafamily.pe"
LOGIN_URL = f"{BASE_URL}/Account/Login"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("InnovaDebug")

def login(session):
    log.info(f"Iniciando diagnóstico para: {INNOVA_EMAIL}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        log.info(f"Conectando a: {LOGIN_URL}")
        r = session.get(LOGIN_URL, timeout=30, headers=headers)
        log.info(f"Respuesta recibida. Código: {r.status_code}")
        
        soup = BeautifulSoup(r.text, "html.parser")
        token_tag = soup.find("input", {"name": "__RequestVerificationToken"})
        
        if not token_tag:
            log.error("¡TICKET DE SEGURIDAD NO ENCONTRADO!")
            log.info("--- CONTENIDO RECIBIDO (Snippet): ---")
            log.info(r.text[:500])
            log.info("--- FIN DEL SNIPPET ---")
            return False
            
        log.info("Token encontrado. Intentando entrar...")
        data = {
            "Correo": INNOVA_EMAIL,
            "Password": INNOVA_PASSWORD,
            "__RequestVerificationToken": token_tag["value"]
        }
        r = session.post(LOGIN_URL, data=data, timeout=30, allow_redirects=True, headers=headers)
        log.info(f"URL final tras login: {r.url}")
        
        if "Login" not in r.url:
            log.info("✅ ¡Acceso exitoso!")
            return True
        else:
            log.error("❌ Acceso denegado (Credenciales o bloqueo).")
            return False
            
    except Exception as e:
        log.error(f"Error de conexión: {e}")
        return False

def main():
    if not INNOVA_EMAIL:
        log.error("Falta el correo en Secrets.")
        sys.exit(1)
    
    session = requests.Session()
    if not login(session):
        sys.exit(1)
        
    log.info("Proceso terminado correctamente.")

if __name__ == "__main__":
    main()

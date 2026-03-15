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
MENSAJES_API = f"{BASE_URL}/Mensaje/ConsultarMensajePorPagina"
DETALLE_API = f"{BASE_URL}/Mensaje/ConsultaDetalleMensaje"

SEEN_FILE = Path("mensajes_vistos.json")
HISTORY_FILE = Path("historial_mensajes.json")
INDEX_FILE = Path("index.html")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("InnovaCloud")

def cargar_json(path, default):
    if path.exists():
        try: return json.loads(path.read_text(encoding="utf-8"))
        except: return default
    return default

def guardar_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def login(session):
    log.info(f"Intentando entrar como: {INNOVA_EMAIL}")
    try:
        r = session.get(LOGIN_URL, timeout=30)
        log.info(f"Página cargada. Status: {r.status_code}")
        soup = BeautifulSoup(r.text, "html.parser")
        token_tag = soup.find("input", {"name": "__RequestVerificationToken"})
        if not token_tag:
            log.error("¡ERROR! No se encontró el TOKEN. Es posible que Innova esté bloqueando a GitHub.")
            return False
        
        data = {"Correo": INNOVA_EMAIL, "Password": INNOVA_PASSWORD, "__RequestVerificationToken": token_tag["value"]}
        r = session.post(LOGIN_URL, data=data, timeout=30, allow_redirects=True)
        log.info(f"Respuesta del login: {r.status_code}")
        log.info(f"URL final después del login: {r.url}")
        
        if "Login" not in r.url:
            log.info("✅ ¡Acceso concedido!")
            return True
        else:
            log.error("❌ Acceso denegado: El servidor no aceptó los datos.")
            return False
    except Exception as e:
        log.error(f"Error inesperado: {e}")
        return False

def main():
    if not all([INNOVA_EMAIL, INNOVA_PASSWORD]): sys.exit(1)
    if os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch":
        requests.get(f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_NUMBER}&text=🔍+Innova+Cloud:+Revisando+ahora...&apikey={CALLMEBOT_API_KEY}")
    
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    
    if not login(session):
        log.error("El login falló. Por favor, verifica tus datos en Secrets.")
        sys.exit(1)
        
    # Obtener y procesar mensajes (si el login funciona)
    r = session.post(MENSAJES_API, data={"IdPersona":"0","TipoBandeja":"1","NumeroPagina":"1","TamanioPagina":"20","EsFavorito":"false"}, headers={"X-Requested-With":"XMLHttpRequest"})
    mensajes = json.loads(r.json().get("DataJson", "[]"))
    # ... resto del proceso ...
    log.info(f"Se encontraron {len(mensajes)} mensajes.")

if __name__ == "__main__": main()

import os
import re
import json
import time
import logging
import urllib.parse
from datetime import datetime
from pathlib import Path
import requests
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("InnovaCloud")

def cargar_mensajes_vistos():
    if SEEN_FILE.exists():
        try:
            data = json.loads(SEEN_FILE.read_text(encoding="utf-8"))
            return set(str(x) for x in data.get("ids", []))
        except: return set()
    return set()

def guardar_mensajes_vistos(ids):
    data = {"ids": list(ids), "updated_at": datetime.now().isoformat()}
    SEEN_FILE.write_text(json.dumps(data), encoding="utf-8")

def login(session):
    log.info(f"Accediendo a {LOGIN_URL}...")
    r = session.get(LOGIN_URL, timeout=30)
    log.info(f"Respuesta recibida: {r.status_code}")
    
    if r.status_code != 200:
        log.error("No se pudo cargar la pagina de login.")
        return False

    soup = BeautifulSoup(r.text, "html.parser")
    token_tag = soup.find("input", {"name": "__RequestVerificationToken"})
    
    if not token_tag:
        log.error("No se encontro el token de seguridad. Es posible que el sitio este bloqueando a GitHub.")
        # Opcional: imprimir un trozo de la respuesta para depurar
        log.info(f"Contenido parcial: {r.text[:500]}")
        return False
        
    token = token_tag["value"]
    log.info("Token encontrado, enviando credenciales...")
    
    data = {"Correo": INNOVA_EMAIL, "Password": INNOVA_PASSWORD, "__RequestVerificationToken": token}
    r = session.post(LOGIN_URL, data=data, timeout=30)
    
    if "Login" not in r.url:
        log.info("¡Login exitoso!")
        return True
    
    log.error("Credenciales incorrectas o login fallido.")
    return False

def obtener_mensajes(session):
    payload = {"IdPersona": "0", "TipoBandeja": "1", "NumeroPagina": "1", "TamanioPagina": "20", "EsFavorito": "false"}
    r = session.post(MENSAJES_API, data=payload, headers={"X-Requested-With": "XMLHttpRequest"})
    data = r.json()
    mensajes_raw = json.loads(data.get("DataJson", "[]"))
    return [{"id": str(m.get("IdCorreo", m.get("IdMensaje", ""))), "asunto": m.get("Asunto", ""), "remitente": m.get("NombreRemitente", ""), "fecha": m.get("FechaEnvio", ""), "snippet": m.get("Contenido", "")} for m in mensajes_raw]

def obtener_detalle(session, msg_id):
    r = session.post(DETALLE_API, data={"IdMensaje": msg_id, "tipoBandeja": "1"}, headers={"X-Requested-With": "XMLHttpRequest"})
    if r.status_code == 200:
        cuerpo = r.json().get("DataJson", "")
        if "<" in str(cuerpo):
            return BeautifulSoup(str(cuerpo), "html.parser").get_text(separator="\n", strip=True)
        return str(cuerpo)
    return ""

def enviar_whatsapp(msg):
    url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_NUMBER}&text={urllib.parse.quote(msg)}&apikey={CALLMEBOT_API_KEY}"
    return requests.get(url).status_code == 200

def generar_resumen(m, detalle):
    asunto = m['asunto'].upper()
    es_imp = any(w in asunto for w in ["FACTURA", "PAGO", "IMPORTANTE"])
    txt = f"*NUEVO MENSAJE INNOVA*"
    if es_imp: txt += " (PRIORIDAD)"
    txt += f"\n\nAsunto: {m['asunto']}\nDe: {m['remitente']}\n"
    if detalle: txt += f"\nContenido:\n{detalle[:500]}..."
    return txt

def main():
    if not all([INNOVA_EMAIL, INNOVA_PASSWORD, WHATSAPP_NUMBER, CALLMEBOT_API_KEY]):
        log.error("Faltan variables de entorno en GitHub Secrets.")
        return

    vistos = cargar_mensajes_vistos()
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    if not login(session): return

    mensajes = obtener_mensajes(session)
    if not SEEN_FILE.exists():
        guardar_mensajes_vistos({m["id"] for m in mensajes})
        log.info("Registro inicial completado.")
        return

    nuevos = [m for m in mensajes if m["id"] not in vistos]
    log.info(f"Mensajes nuevos: {len(nuevos)}")
    
    for m in reversed(nuevos):
        log.info(f"Notificando: {m['asunto']}")
        detalle = obtener_detalle(session, m["id"])
        if enviar_whatsapp(generar_resumen(m, detalle)):
            vistos.add(m["id"])
        time.sleep(2)

    guardar_mensajes_vistos(vistos)
    log.info("Proceso terminado exitosamente.")

if __name__ == "__main__":
    main()

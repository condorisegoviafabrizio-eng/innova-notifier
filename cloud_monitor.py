"""
Version para la Nube (GitHub Actions)
=====================================
Este script se ejecuta una vez, revisa innovafamily.pe,
notifica por WhatsApp y termina.
Disenado para correr cada hora automaticamente en GitHub.
"""

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

# --- Configuracion (desde Secretos de GitHub) ---
INNOVA_EMAIL = os.getenv("INNOVA_EMAIL")
INNOVA_PASSWORD = os.getenv("INNOVA_PASSWORD")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")
CALLMEBOT_API_KEY = os.getenv("CALLMEBOT_API_KEY")

# URLs
BASE_URL = "https://innovafamily.pe"
LOGIN_URL = f"{BASE_URL}/Account/Login"
MENSAJES_API = f"{BASE_URL}/Mensaje/ConsultarMensajePorPagina"
DETALLE_API = f"{BASE_URL}/Mensaje/ConsultaDetalleMensaje"

# Archivo de persistencia (se guarda en el repositorio)
SEEN_FILE = Path("mensajes_vistos.json")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("InnovaCloud")

def cargar_mensajes_vistos() -> set:
      if SEEN_FILE.exists():
                try:
                              data = json.loads(SEEN_FILE.read_text(encoding="utf-8"))
                              return set(str(x) for x in data.get("ids", []))
except Exception: return set()
    return set()

def guardar_mensajes_vistos(ids: set):
      SEEN_FILE.write_text(json.dumps({"ids": list(ids), "updated_at": datetime.now().isoformat()}), encoding="utf-8")

def login(session):
      log.info("Iniciando sesion en Innova Family...")
      r = session.get(LOGIN_URL)
      soup = BeautifulSoup(r.text, "html.parser")
      token = soup.find("input", {"name": "__RequestVerificationToken"})["value"]

    data = {"Correo": INNOVA_EMAIL, "Password": INNOVA_PASSWORD, "__RequestVerificationToken": token}
    r = session.post(LOGIN_URL, data=data, timeout=30)

    if "Login" not in r.url:
              log.info("Login exitoso!")
              return True
          return False

def obtener_mensajes(session):
      payload = {"IdPersona": "0", "TipoBandeja": "1", "NumeroPagina": "1", "TamanioPagina": "20", "EsFavorito": "false"}
      headers = {"X-Requested-With": "XMLHttpRequest"}
      r = session.post(MENSAJES_API, data=payload, headers=headers)

    data = r.json()
    mensajes_raw = json.loads(data.get("DataJson", "[]"))

    mensajes = []
    for m in mensajes_raw:
              mensajes.append({
                            "id": str(m.get("IdCorreo", m.get("IdMensaje", ""))),
                            "asunto": m.get("Asunto", "Sin asunto"),
                            "remitente": m.get("NombreRemitente", ""),
                            "fecha": m.get("FechaEnvio", ""),
                            "snippet": m.get("Contenido", "")
              })
          return mensajes

def obtener_detalle(session, msg_id):
      payload = {"IdMensaje": msg_id, "tipoBandeja": "1"}
      headers = {"X-Requested-With": "XMLHttpRequest"}
      r = session.post(DETALLE_API, data=payload, headers=headers)
      if r.status_code == 200:
                data = r.json()
                cuerpo = data.get("DataJson", "")
                if "<" in str(cuerpo):
                              soup = BeautifulSoup(str(cuerpo), "html.parser")
                              return soup.get_text(separator="\n", strip=True)
                          return str(cuerpo)
            return ""

def generar_resumen(m, detalle):
      """Genera un resumen formateado del mensaje para WhatsApp."""
    # Detectar si es una factura o mensaje importante
    asunto = m['asunto'].upper()
    es_importante = any(word in asunto for word in ["FACTURA", "PAGO", "IMPORTANTE", "CIRCULAR", "COMUNICADO"])

    header = f"*MENSAJE INNOVA FAMILY*"
    if es_importante:
              header += " (Prioridad) "

    lineas = [
              header,
                          "------------------------------",
              f"*Asunto:* {m['asunto']}",
              f"*De:* {m['remitente']}",
              f"*Fecha:* {m['fecha']}",
              "------------------------------",
    ]

    # Limpiar y limitar detalle
    if detalle:
              # WhatsApp limit is ~4096, but we keep it concise
              detalle_corto = detalle[:800].strip()
              if len(detalle) > 800:
                            detalle_corto += "..."
                        lineas.append(f"*Contenido:*\n{detalle_corto}")
elif m['snippet']:
        lineas.append(f"*Vista previa:* {m['snippet']}")

    lineas.append("\n innovafamily.pe")
    return "\n".join(lineas)

def enviar_whatsapp(msg):
      # This is a stub for cloud execution, callmebot API is used
      WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")
    CALLMEBOT_API_KEY = os.getenv("CALLMEBOT_API_KEY")
    url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_NUMBER}&text={urllib.parse.quote(msg)}&apikey={CALLMEBOT_API_KEY}"
    r = requests.get(url)
    return r.status_code == 200

def main():
      if not all([INNOVA_EMAIL, INNOVA_PASSWORD, WHATSAPP_NUMBER, CALLMEBOT_API_KEY]):
                log.error("Faltan variables de entorno (Secrets de GitHub).")
                return

    vistos = cargar_mensajes_vistos()
    session = requests.Session()
    session.headers.update({
              "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    if not login(session):
              log.error("Error de login - revisa tus credenciales en Secrets.")
        return

    mensajes = obtener_mensajes(session)

    # Si es la primera vez (archivo no existe), registramos los actuales y no enviamos nada
    if not SEEN_FILE.exists():
              log.info("Primera ejecucion: registrando mensajes existentes...")
        guardar_mensajes_vistos({m["id"] for m in mensajes})
        log.info(f"Se registraron {len(mensajes)} mensajes. No se enviaran notificaciones esta vez.")
        return

    nuevos = [m for m in mensajes if m["id"] not in vistos]
    log.info(f"Mensajes nuevos encontrados: {len(nuevos)}")

    # Procesar de mas antiguo a mas nuevo
    for m in reversed(nuevos):
              log.info(f"Notificando: {m['asunto']}")
              detalle = obtener_detalle(session, m["id"])
              texto = generar_resumen(m, detalle)

        if enviar_whatsapp(texto):
                      vistos.add(m["id"])
                      log.info(f"Enviado: {m['id']}")
else:
            log.error(f"Fallo al enviar: {m['id']}")

        # Pequena pausa para no saturar CallMeBot
          time.sleep(5)

    guardar_mensajes_vistos(vistos)
    log.info("Proceso completado y registro actualizado.")

if __name__ == "__main__":
      main()
          

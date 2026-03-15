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
    log.info(f"Intentando login para {INNOVA_EMAIL}...")
    try:
        r = session.get(LOGIN_URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(r.text, "html.parser")
        token_tag = soup.find("input", {"name": "__RequestVerificationToken"})
        if not token_tag: return False
        data = {"Correo": INNOVA_EMAIL, "Password": INNOVA_PASSWORD, "__RequestVerificationToken": token_tag["value"]}
        r = session.post(LOGIN_URL, data=data, timeout=30)
        return "Login" not in r.url
    except: return False

def obtener_mensajes(session):
    r = session.post(MENSAJES_API, data={"IdPersona": "0", "TipoBandeja": "1", "NumeroPagina": "1", "TamanioPagina": "20", "EsFavorito": "false"}, headers={"X-Requested-With": "XMLHttpRequest"})
    return [{"id": str(m.get("IdCorreo", m.get("IdMensaje", ""))), "asunto": m.get("Asunto", ""), "remitente": m.get("NombreRemitente", ""), "fecha": m.get("FechaEnvio", ""), "snippet": m.get("Contenido", "")} for m in json.loads(r.json().get("DataJson", "[]"))]

def enviar_whatsapp(msg):
    if not WHATSAPP_NUMBER or not CALLMEBOT_API_KEY: return False
    url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_NUMBER}&text={urllib.parse.quote(msg)}&apikey={CALLMEBOT_API_KEY}"
    try: return requests.get(url, timeout=20).status_code == 200
    except: return False

def generar_dashboard(mensajes):
    ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    trigger = "https://github.com/condorisegoviafabrizio-eng/innova-notifier/actions/workflows/github_workflow.yml"
    msg_html = ""
    for m in mensajes:
        es_imp = any(w in str(m['asunto']).upper() for w in ["FACTURA", "PAGO", "IMPORTANTE", "CIRCULAR"])
        msg_html += f'<div class="card {"important" if es_imp else ""}"><div class="card-header"><span class="icon">{"🚨" if es_imp else "📩"}</span><span class="date">{m["fecha"]}</span></div><h3>{m["asunto"]}</h3><p class="sender">👤 {m["remitente"]}</p><div class="snippet">{m["snippet"][:200]}...</div></div>'
    html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>Innova Notifier</title><link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap" rel="stylesheet"><style>:root{{--bg:#0f172a;--card-bg:rgba(30, 41, 59, 0.7);--accent:#38bdf8;--text:#f8fafc;--text-dim:#94a3b8;--important:#ef4444}}*{{box-sizing:border-box}}body{{font-family:'Outfit',sans-serif;background:var(--bg);color:var(--text);margin:0;padding:20px;background:radial-gradient(circle at top right,#1e293b,#0f172a);min-height:100vh}}.container{{max-width:800px;margin:0 auto}}header{{text-align:center;margin-bottom:40px;padding:20px;background:var(--card-bg);border-radius:20px;backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.1)}}h1{{margin:0;color:var(--accent);font-size:2rem}}.status{{color:var(--text-dim);font-size:0.9rem;margin-top:10px}}.btn{{display:inline-block;background:var(--accent);color:#0f172a;text-decoration:none;padding:12px 24px;border-radius:12px;font-weight:600;margin-top:20px;transition:transform 0.2s}}.btn:active{{transform:scale(0.95)}}.grid{{display:grid;gap:20px}}.card{{background:var(--card-bg);padding:20px;border-radius:16px;border:1px solid rgba(255,255,255,0.05);transition:0.3;position:relative;overflow:hidden}}.card:hover{{border-color:var(--accent);transform:translateY(-2px)}}.card.important{{border-left:5px solid var(--important)}}.card-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px}}.date{{color:var(--text-dim);font-size:0.8rem}}h3{{margin:0 0 10px 0;font-size:1.1rem;line-height:1.4}}.sender{{color:var(--accent);font-size:0.9rem;margin:5px 0}}.snippet{{color:var(--text-dim);font-size:0.85rem;line-height:1.5}}</style></head><body><div class="container"><header><h1>Innova Notifier</h1><div class="status">Actualizado: {ts}</div><a href="{trigger}" class="btn">🚀 Revisar Ahora</a></header><div class="grid">{msg_html}</div></div></body></html>"""
    INDEX_FILE.write_text(html, encoding="utf-8")

def main():
    if not all([INNOVA_EMAIL, INNOVA_PASSWORD]): sys.exit(1)
    if os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch": enviar_whatsapp("🔍 *Innova Cloud:* Revisando manualmente...")
    vistos_raw = cargar_json(SEEN_FILE, {"ids": []})["ids"]
    vistos = set(str(i) for i in vistos_raw if not isinstance(i, dict))
    session = requests.Session(); session.headers.update({"User-Agent": "Mozilla/5.0"})
    if not login(session):
        log.error("Login fallido"); sys.exit(1)
    mensajes = obtener_mensajes(session); historial = cargar_json(HISTORY_FILE, [])
    ids_h = {str(m["id"]) for m in historial}
    for m in mensajes:
        if str(m["id"]) not in ids_h: historial.insert(0, m)
    historial = historial[:50]; guardar_json(HISTORY_FILE, historial); generar_dashboard(historial)
    if not SEEN_FILE.exists():
        guardar_json(SEEN_FILE, {"ids": list(vistos | {str(m["id"]) for m in mensajes})}); return
    nuevos = [m for m in mensajes if str(m["id"]) not in vistos]
    for m in reversed(nuevos):
        log.info(f"Notificando: {m['asunto']}")
        asunto = str(m['asunto']).upper()
        h = "🚨 *PRIORIDAD* 🚨" if any(w in asunto for w in ["FACTURA", "PAGO", "IMPORTANTE"]) else "📩"
        msg = f"{h} *INNOVA*: {m['asunto']}\nDe: {m['remitente']}\n\n🌍 Dashboard: condorisegoviafabrizio-eng.github.io/innova-notifier"
        if enviar_whatsapp(msg): vistos.add(str(m["id"]))
        time.sleep(2)
    guardar_json(SEEN_FILE, {"ids": list(vistos)})

if __name__ == "__main__": main()

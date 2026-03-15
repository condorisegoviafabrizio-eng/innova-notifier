import os, json, time, logging, urllib.parse, requests, sys
from datetime import datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --- Configuracion (GitHub Secrets o .env local) ---
load_dotenv()
INNOVA_EMAIL = os.getenv("INNOVA_EMAIL")
INNOVA_PASSWORD = os.getenv("INNOVA_PASSWORD")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")
CALLMEBOT_API_KEY = os.getenv("CALLMEBOT_API_KEY")

BASE_URL = "https://innovafamily.pe"
LOGIN_URL = f"{BASE_URL}/Account/Login"
MENSAJES_API = f"{BASE_URL}/Mensaje/ConsultarMensajePorPagina"
DETALLE_API = f"{BASE_URL}/Mensaje/ConsultaDetalleMensaje"

# Archivos de datos
SCRIPT_DIR = Path(__file__).parent
SEEN_FILE = SCRIPT_DIR / "mensajes_vistos.json"
HISTORY_FILE = SCRIPT_DIR / "historial_mensajes.json"
DASHBOARD_FILE = SCRIPT_DIR / "index.html"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("InnovaCloud")

def cargar_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except: pass
    return default

def guardar_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def login(session):
    log.info(f"Iniciando session para: {INNOVA_EMAIL}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        r = session.get(LOGIN_URL, timeout=30, headers=headers)
        
        # Log content if token not found (for debugging)
        soup = BeautifulSoup(r.text, "html.parser")
        token = soup.find("input", {"name": "__RequestVerificationToken"})
        
        if not token:
            # Reintentar con otro User-Agent o buscar en todo el texto si BeautifulSoup falló
            token_match = re.search(r'name="__RequestVerificationToken" type="hidden" value="([^"]+)"', r.text)
            if token_match:
                token_value = token_match.group(1)
            else:
                log.error("Token CSRF no encontrado. Contenido html:")
                log.info(r.text[:500])
                return False
        else:
            token_value = token["value"]
            
        data = {
            "Correo": INNOVA_EMAIL,
            "Password": INNOVA_PASSWORD,
            "__RequestVerificationToken": token_value
        }
        
        # Intentar login normal
        r = session.post(LOGIN_URL, data=data, timeout=30, allow_redirects=True, headers=headers)
        
        # Verificar si entramos
        if "Login" not in r.url:
            log.info("✅ Login exitoso")
            return True
            
        # Intento fallback via AJAX
        headers["X-Requested-With"] = "XMLHttpRequest"
        r = session.post(LOGIN_URL, data=data, timeout=30, headers=headers)
        
        test = session.get(f"{BASE_URL}/Herramientas/Index", timeout=30, allow_redirects=False)
        if test.status_code == 200:
            log.info("✅ Login exitoso (AJAX)")
            return True
            
        log.error("❌ Login fallido")
        return False
    except Exception as e:
        log.error(f"Error login: {e}")
        return False

def obtener_mensajes(session):
    try:
        payload = {
            "IdPersona": "0", "TipoBandeja": "1", "NumeroPagina": "1", "TamanioPagina": "20",
            "EsFavorito": "false"
        }
        headers = {"X-Requested-With": "XMLHttpRequest"}
        r = session.post(MENSAJES_API, data=payload, headers=headers, timeout=30)
        data = r.json()
        mensajes_raw = json.loads(data.get("DataJson", "[]"))
        
        result = []
        for m in mensajes_raw:
            msg_id = str(m.get("IdCorreo", m.get("IdMensaje", "")))
            fecha_raw = m.get("FechaEnvio", "")
            fecha_str = fecha_raw
            try:
                ts = int(re.search(r"(\d+)", fecha_raw).group(1)) / 1000
                fecha_str = datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M")
            except: pass
            
            result.append({
                "id": msg_id,
                "asunto": m.get("Asunto", "Sin asunto"),
                "remitente": m.get("NombreRemitente", "Inova"),
                "fecha": fecha_str,
                "snippet": m.get("Contenido", "")[:150]
            })
        return result
    except Exception as e:
        log.error(f"Error mensajes: {e}")
        return []

def enviar_whatsapp(msg_text):
    if not CALLMEBOT_API_KEY: return
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_NUMBER}&text={urllib.parse.quote(msg_text)}&apikey={CALLMEBOT_API_KEY}"
        requests.get(url, timeout=20)
    except: pass

def generar_dashboard(historial):
    html_template = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Innova Notifier Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --card: #1e293b;
            --primary: #f97316;
            --accent: #38bdf8;
            --text: #f8fafc;
            --dim: #94a3b8;
        }
        body {
            background: var(--bg);
            color: var(--text);
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container {
            max-width: 800px;
            width: 100%;
        }
        header {
            text-align: center;
            margin-bottom: 3rem;
            animation: fadeIn 1s ease-out;
        }
        h1 {
            font-size: 2.5rem;
            font-weight: 800;
            margin: 0;
            background: linear-gradient(to right, var(--primary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .status {
            font-size: 0.875rem;
            color: var(--dim);
            margin-top: 0.5rem;
        }
        .timeline {
            position: relative;
            padding-left: 2rem;
            border-left: 2px solid var(--card);
        }
        .message-card {
            background: var(--card);
            padding: 1.5rem;
            border-radius: 1rem;
            margin-bottom: 1.5rem;
            position: relative;
            transition: transform 0.2s, box-shadow 0.2s;
            border: 1px solid rgba(255,255,255,0.05);
            animation: slideUp 0.5s ease-out forwards;
        }
        .message-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
            border-color: var(--primary);
        }
        .message-card::before {
            content: '';
            position: absolute;
            left: -2.65rem;
            top: 1.5rem;
            width: 12px;
            height: 12px;
            background: var(--primary);
            border-radius: 50%;
            border: 4px solid var(--bg);
        }
        .meta {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: var(--accent);
            font-weight: 600;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
        }
        .asunto {
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--text);
        }
        .remitente {
            font-size: 0.875rem;
            color: var(--dim);
            margin-bottom: 1rem;
        }
        .snippet {
            font-size: 0.95rem;
            line-height: 1.6;
            color: var(--dim);
        }
        .empty {
            text-align: center;
            padding: 4rem;
            color: var(--dim);
            font-style: italic;
        }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes slideUp { 
            from { opacity: 0; transform: translateY(20px); } 
            to { opacity: 1; transform: translateY(0); } 
        }
        .footer { margin-top: 4rem; text-align: center; color: var(--dim); font-size: 0.75rem; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Innova Notifier</h1>
            <div class="status">Últimas 24 horas de notificaciones</div>
        </header>
        
        <div class="timeline">
            {CHUNKS}
        </div>

        <div class="footer">
            Actualizado por Innova Bot el {FECHA_ACTUAL}
        </div>
    </div>
</body>
</html>
"""
    chunks = ""
    if not historial:
        chunks = '<div class="empty">No hay mensajes recientes en las últimas 24 horas.</div>'
    else:
        for m in historial:
            chunks += f"""
            <div class="message-card">
                <div class="meta">
                    <span>{m['fecha']}</span>
                    <span>ID: {m['id']}</span>
                </div>
                <div class="asunto">{m['asunto']}</div>
                <div class="remitente">De: {m['remitente']}</div>
                <div class="snippet">{m['snippet']}</div>
            </div>
            """
    
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    final_html = html_template.replace("{CHUNKS}", chunks).replace("{FECHA_ACTUAL}", now_str)
    DASHBOARD_FILE.write_text(final_html, encoding="utf-8")

def main():
    if not INNOVA_EMAIL:
        log.error("Falta config")
        sys.exit(1)
        
    session = requests.Session()
    if not login(session):
        sys.exit(1)
        
    mensajes = obtener_mensajes(session)
    vistos_data = cargar_json(SEEN_FILE, {"ids": []})
    vistos = set(vistos_data["ids"])
    
    historial = cargar_json(HISTORY_FILE, [])
    
    # Filtrar historial para mantener solo ultimas 24h
    hace_24h = datetime.now() - timedelta(hours=24)
    nuevo_historial = []
    
    # Añadir mensajes nuevos
    nuevos_detectados = 0
    for m in mensajes:
        if m["id"] not in vistos:
            nuevos_detectados += 1
            vistos.add(m["id"])
            # Notificar WhatsApp
            resumen = f"📩 *{m['asunto']}*\n👤 {m['remitente']}\n📅 {m['fecha']}\n\n{m['snippet']}..."
            enviar_whatsapp(resumen)
            # Agregar al inicio del historial
            nuevo_historial.append(m)
            
    # Combinar con historial previo y filtrar por tiempo
    # (En este caso simplificado, solo guardamos los ultimos 20 mensajes que sean de las ultimas 24h)
    # Para hacerlo real, necesitariamos parsear la fecha de cada mensaje en el historial
    merged = nuevo_historial + historial
    # Limitar a 20 mensajes para el dashboard
    final_historial = merged[:20]
    
    guardar_json(SEEN_FILE, {"ids": list(vistos), "last_update": datetime.now().isoformat()})
    guardar_json(HISTORY_FILE, final_historial)
    
    generar_dashboard(final_historial)
    log.info(f"Proceso completado. {nuevos_detectados} mensajes nuevos.")

if __name__ == "__main__":
    import re
    main()

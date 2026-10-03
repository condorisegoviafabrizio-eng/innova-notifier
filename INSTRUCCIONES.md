# Guía de configuración

Esta guía complementa el [README del proyecto](README.md).

## 1. Preparar el servicio de notificaciones

Habilita tu número de WhatsApp para recibir mensajes de CallMeBot siguiendo las instrucciones vigentes del servicio. Conserva la API Key como dato privado.

## 2. Configurar GitHub Actions

1. Utiliza un repositorio privado si el monitor va a almacenar mensajes reales.
2. Comprueba que el workflow esté en `.github/workflows/github_workflow.yml`.
3. En **Settings → Secrets and variables → Actions**, agrega los siguientes secretos:
   - `INNOVA_EMAIL`
   - `INNOVA_PASSWORD`
   - `WHATSAPP_NUMBER`
   - `CALLMEBOT_API_KEY`
4. En **Actions**, abre **Innova Notifier Cloud** y selecciona **Run workflow**.
5. Revisa el resultado de la ejecución y los archivos generados.

El workflow está programado cada 30 minutos. El archivo `mensajes_vistos.json` conserva el estado para evitar notificaciones repetidas.

## 3. Ejecutar localmente

Desde la carpeta del proyecto:

```bash
pip install -r requirements.txt
python cloud_monitor.py
```

Antes de ejecutar el script, configura las cuatro variables de entorno anteriores en tu terminal. Un archivo `.env` no se carga automáticamente por sí solo.

## Datos privados

No incluyas contraseñas, API Keys, números personales ni rutas locales en la documentación pública. El historial de mensajes y el panel generado también pueden contener información personal; revisa su acceso antes de publicarlos.

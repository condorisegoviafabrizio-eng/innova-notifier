# Innova Family -> WhatsApp Notificador

## Instrucciones de Configuracion

### Paso 1: Activar CallMeBot (OBLIGATORIO)

CallMeBot es un servicio gratuito que permite enviar mensajes a WhatsApp.

1. En el celular del numero **918369717**, guarda este contacto:
2.    - **Nombre:** CallMeBot
      -    - **Numero:** `+34 644 71 81 48`
       
           - 2. Abre WhatsApp y envia este mensaje exacto a CallMeBot:
             3.    ```
                      I allow callmebot to send me messages
                      ```

                   3. CallMeBot te respondera con un **API Key** (un numero). Ejemplo: `123456`
               
                   4. 4. Abre el archivo `.env` y reemplaza `TU_API_KEY_AQUI` con tu API Key:
                      5.    ```
                               CALLMEBOT_API_KEY=123456
                               ```

                            ### Paso 2: Instalar Dependencias

                        Abre una terminal (CMD o PowerShell) y ejecuta:

                      ```
                      cd C:\Users\fabri\.gemini\antigravity\scratch\email_notifier
                      pip install -r requirements.txt
                      ```

                      ### Paso 4: Configurar en la NUBE (GitHub Actions)

                      Para que el notificador funcione **sin tener la computadora prendida**:

                      1. **Crea un Repositorio Privado en GitHub:**
                      2.    - Ve a [GitHub](https://github.com/new) y crea un repo llamado `innova-notifier`.
                            -    - **IMPORTANTE:** Eligelo como **Private** (Privado).
                             
                                 - 2. **Sube los archivos:**
                                   3.    - Sube estos archivos a tu repo: `cloud_monitor.py`, `github_workflow.yml`, `requirements.txt`.
                                         -    - El archivo `github_workflow.yml` debe ir dentro de una carpeta llamada `.github/workflows/`.
                                          
                                              - 3. **Configura los "Secrets" (Tus datos privados):**
                                                4.    - En tu repo de GitHub, ve a **Settings** -> **Secrets and variables** -> **Actions**.
                                                      -    - Haz clic en **New repository secret** y agrega estos 4:
                                                           -      - `INNOVA_EMAIL`: Tu correo de Innova.
                                                           -       - `INNOVA_PASSWORD`: Tu contrasena de Innova.
                                                           -        - `WHATSAPP_NUMBER`: Tu numero (ej: `51918369717`).
                                                           -         - `CALLMEBOT_API_KEY`: Tu API Key de CallMeBot.
                                                       
                                                           -     4. **Activa el proceso:**
                                                           -    - Ve a la pestana **Actions** en GitHub.
                                                                -    - Veras "Innova Notifier Cloud".
                                                                     -    - Haz clic en **Run workflow** para probarlo por primera vez.
                                                                          -    - El sistema se ejecutara solo cada 30 minutos automaticamente.
                                                                           
                                                                               - ### Notas y Mejoras
                                                                           
                                                                               - - **Deteccion de Facturas:** El sistema ahora resalta automaticamente mensajes con palabras como "Factura", "Pago", "Importante".
                                                                                 - - **Privacidad:** Nunca compartas tu API Key ni subas el archivo `.env` a repositorios publicos.
                                                                                   - - **Registro:** El archivo `mensajes_vistos.json` se actualizara solo en el repo para no repetir notificaciones.
                                                                                     - 

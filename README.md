# Innova Notifier

Monitor de mensajes de **Innova Family** con notificaciones por WhatsApp y un panel HTML. Automatiza la consulta de mensajes y conserva un registro para evitar notificaciones repetidas.

## Funcionalidades

- Consulta de mensajes mediante una sesión autenticada.
- Detección de mensajes nuevos a partir de los identificadores ya procesados.
- Envío de notificaciones por WhatsApp mediante CallMeBot.
- Generación de un panel HTML y almacenamiento del historial en JSON.
- Ejecución programada y manual con GitHub Actions.

## Tecnologías

| Componente | Tecnología |
| --- | --- |
| Monitor | Python; el workflow utiliza Python 3.12 |
| Consultas HTTP | Requests |
| Procesamiento HTML | Beautiful Soup |
| Automatización | GitHub Actions |
| Panel e historial | HTML y JSON |

## Funcionamiento

1. El monitor inicia sesión con las credenciales configuradas.
2. Consulta los mensajes y los compara con el registro de mensajes vistos.
3. Envía las nuevas notificaciones al número configurado.
4. Actualiza los archivos de estado y el panel.

## Configuración

En **Settings → Secrets and variables → Actions**, configura estos secretos del repositorio:

| Secreto | Uso |
| --- | --- |
| `INNOVA_EMAIL` | Correo de la cuenta de Innova Family |
| `INNOVA_PASSWORD` | Contraseña de esa cuenta |
| `WHATSAPP_NUMBER` | Número de destino con código de país |
| `CALLMEBOT_API_KEY` | Clave del servicio de notificaciones |

El número de destino debe estar habilitado para recibir mensajes a través de CallMeBot. Utiliza una cuenta y un número que tengas autorización para usar.

## Ejecución

En la pestaña **Actions**, abre **Innova Notifier Cloud** y selecciona **Run workflow** para una ejecución manual. El workflow también tiene una programación cada 30 minutos; las ejecuciones programadas pueden demorarse.

Para ejecutar el monitor localmente, instala las dependencias y configura las mismas cuatro variables de entorno antes de iniciarlo:

```bash
pip install -r requirements.txt
python cloud_monitor.py
```

Crear un archivo `.env` por sí solo no configura las variables de entorno del proceso.

## Estructura

```text
.github/workflows/github_workflow.yml  Automatización
cloud_monitor.py                       Monitor y generación del panel
requirements.txt                       Dependencias
index.html                             Panel generado
historial_mensajes.json                 Historial de mensajes
mensajes_vistos.json                    Registro de mensajes procesados
INSTRUCCIONES.md                        Guía de configuración
```

## Privacidad

Las credenciales se configuran como secretos, nunca dentro del código. El panel y el historial pueden contener mensajes personales: para trabajar con datos reales, utiliza un repositorio privado y controla el acceso al panel. No publiques archivos `.env`, claves ni números personales.

## Autor

[Roger Fabrizio Segovia Condori](https://github.com/condorisegoviafabrizio-eng)

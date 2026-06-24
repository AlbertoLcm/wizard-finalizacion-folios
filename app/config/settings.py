from pathlib import Path

# Raíz del proyecto (wizard-finalizacion-folios/)
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Carpeta de salida: todos los artefactos generados en runtime van aquí ──
DIST_DIR = BASE_DIR / "dist"

# Rutas de entrada (archivos que el usuario provee manualmente)
INPUT_FILE = BASE_DIR / "Oficios.xlsx"

# Rutas de salida (generadas / gestionadas por el bot)
DOCUMENTS_UPLOAD = DIST_DIR / "Documentos"
FILE_EXITOS       = DIST_DIR / "resultados_procesados.csv"
USER_DATA_DIR     = DIST_DIR / "perfil_google_drive"

# Otros
BATCH_GUARDADO = 10

# Assets de la UI
ASSETS_DIR = BASE_DIR / "assets"

# URLs
URL_WIZARD_MIS_TAREAS = "https://bbva-wizardautomexpress-am.appspot.com/wizardautomexpr-am/manager/manager-tasks"
URL_LOGIN             = "https://acprod.intranet.com.mx/mbom_mx_ws/mbom_mx_web/PortalLogon"
URL_CIERRE_OPERACIONES = "https://acprod.intranet.com.mx/boixp_mx_web/boixp_mx_web/servlet/ServletOperacionWeb?OPERACION=VGOMX060&LOCALE=es_ES&DATOS_ENTRADA.FLUJO_LANZAR=GOMXFL15230"
URL_SUGO              = "https://acprod.intranet.com.mx/mbom_mx_ws/mbom_mx_web/mbom_mx_web_jsp/portal3.jsp"

APP_TITLE = "Bot Wizard - Panel de Control"
APP_GEOMETRY = "1000x650"

COLOR_ELECTRIC = "#001391"
COLOR_MIDNIGHT = "#070E46"
COLOR_DARK_BLUE = "#000519"

COLOR_WHITE = "#FFFFFF"
COLOR_SAND = "#F7F8F8"
COLOR_GREEN = "#9CE67E"

COLOR_TEXT_MUTED = "#7A8599"
COLOR_CYAN = "#00E5C0"
COLOR_STATUS_BG = "#EDF8F4"
COLOR_HOVER = "#9FDAFF"
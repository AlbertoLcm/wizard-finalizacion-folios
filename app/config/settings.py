import sys
from pathlib import Path

# ── DETECTAR SI ES UN EJECUTABLE (.EXE) O MODO DESARROLLO ──
IS_FROZEN = getattr(sys, 'frozen', False)

if IS_FROZEN:
    BASE_DIR = Path(sys.executable).parent
    
    INTERNAL_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    INTERNAL_DIR = BASE_DIR

DIST_DIR = BASE_DIR / "dist"
INPUT_FILE = BASE_DIR / "Oficios.xlsx"

DOCUMENTS_UPLOAD = DIST_DIR / "Documentos"
FILE_EXITOS       = DIST_DIR / "resultados_procesados.csv"
USER_DATA_DIR     = DIST_DIR / "perfil_google_drive"

ASSETS_DIR = INTERNAL_DIR / "app" / "assets"

BATCH_GUARDADO = 10

# URLs
URL_WIZARD_MIS_TAREAS = "https://bbva-wizardautomexpress-am.appspot.com/wizardautomexpr-am/manager/manager-tasks"
URL_LOGIN             = "https://acprod.intranet.com.mx/mbom_mx_ws/mbom_mx_web/PortalLogon"
URL_CIERRE_OPERACIONES = "https://acprod.intranet.com.mx/boixp_mx_web/boixp_mx_web/servlet/ServletOperacionWeb?OPERACION=VGOMX060&LOCALE=es_ES&DATOS_ENTRADA.FLUJO_LANZAR=GOMXFL15230"
URL_SUGO              = "https://acprod.intranet.com.mx/mbom_mx_ws/mbom_mx_web/mbom_mx_web_jsp/portal3.jsp"
URL_ASIGNACION_SUGO = "https://acprod.intranet.com.mx:443/boixp_mx_web/boixp_mx_web/servlet/ServletOperacionWeb?OPERACION=VGOMX021&LOCALE=es_ES&DATOS_ENTRADA.FLUJO_LANZAR=GOMXFL13020"

APP_TITLE = "Bot Wizard - Finalización Folios"
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
import asyncio
import os
import pandas as pd
import getpass
from tqdm import tqdm
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError

# --- CONFIGURACIÓN ---
BASE_DIR = "Resultados"
DOCUMENTS_UPLOAD = "Documentos"
INPUT_FILE = "Oficios.xlsx"
FILE_EXITOS = os.path.join(BASE_DIR, "resultados_procesados.csv")
USER_DATA_DIR = os.path.join(BASE_DIR, "perfil_google_drive")
BATCH_GUARDADO = 10

# URLs
URL_WIZARD_MIS_TAREAS = "https://bbva-wizardautomexpress-am.appspot.com/wizardautomexpr-am/manager/manager-tasks"
URL_LOGIN = "https://acprod.intranet.com.mx/mbom_mx_ws/mbom_mx_web/PortalLogon"
URL_CIERRE_OPERACIONES = "https://acprod.intranet.com.mx/boixp_mx_web/boixp_mx_web/servlet/ServletOperacionWeb?OPERACION=VGOMX060&LOCALE=es_ES&DATOS_ENTRADA.FLUJO_LANZAR=GOMXFL15230"
URL_SUGO = "https://acprod.intranet.com.mx/mbom_mx_ws/mbom_mx_web/mbom_mx_web_jsp/portal3.jsp"

def obtener_argumentos_navegador():
    return [
        "--disable-blink-features=AutomationControlled",
        "--disable-gpu",
        "--no-sandbox",
        "--window-size=1920,1080"
    ]


async def autenticar_google():
    print(f"\n--- FASE DE AUTENTICACIÓN (Carpeta: {USER_DATA_DIR}) ---")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            channel="chrome",
            args=obtener_argumentos_navegador()
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://drive.google.com")
        print("Inicia sesión. Cierra el navegador")
        await page.wait_for_event("close", timeout=120_000)


def preparar_entorno():
    """Crea carpetas necesarias si no existen."""
    for carpeta in [BASE_DIR, DOCUMENTS_UPLOAD]:
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)
            print(f"Carpeta creada: {carpeta}")


def cargar_datos(columnas_requeridas, columna_status):
    """Carga el progreso o el archivo inicial de forma genérica."""
    if os.path.exists(FILE_EXITOS):
        opcion = input(f"Se encontró progreso previo en {FILE_EXITOS}. ¿Continuar? (si/no): ").lower()
        if opcion == 'si':
            df = pd.read_csv(FILE_EXITOS)
            if set(columnas_requeridas).issubset(df.columns):
                return df
            print("[ERROR] El Excel no tiene las columnas necesarias. Cargando original...")

    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] No existe {INPUT_FILE}")
        return None

    df = pd.read_excel(INPUT_FILE)
    if not set(columnas_requeridas).issubset(df.columns):
        print(f"[ERROR] El Excel debe contener las columnas: {', '.join(columnas_requeridas)}")
        return None
    df[columna_status] = "Pendiente"

    return df


async def manejar_login_intranet(browser, user, password):
    """Encapsula la lógica de autenticación en SUGO/Intranet."""
    context = await browser.new_context(ignore_https_errors=True)
    page = await context.new_page()
    try:
        await page.goto(URL_LOGIN, wait_until="domcontentloaded")
        await page.fill(".name", user)
        await page.fill(".pass", password)
        
        async with context.expect_page() as page_info:
            # Intento de login por click o enter
            if await page.locator("//p[@onclick='validaCampos()']").is_visible():
                await page.evaluate("validaCampos()")
            else:
                await page.keyboard.press("Enter")
        
        print(f"Usuario {user} autenticado con éxito.")
        popup = await page_info.value
        await popup.wait_for_load_state()
        storage = await context.storage_state()
        await context.close()
        return storage
    except Exception as e:
        print(f"[ERROR] en login: {e}")
        return None
    

async def cierre_operaciones_asig_juridico(datos: dict, page: Page):
    folio_sugo = str(datos.get("Folio Sugo", "")).strip()
    archivo = str(datos.get("Informe", "")).strip()

    pagina_upload = None
    page_visor = None

    try:
        await page.goto(URL_CIERRE_OPERACIONES, wait_until="domcontentloaded", timeout=6000)

        checkbox = page.locator("#porFolio")
        await checkbox.wait_for(state="visible")
        await checkbox.click()

        await page.fill("#noFolio", folio_sugo)

        async with page.expect_navigation():
            await page.evaluate("buscar();")

        await page.wait_for_selector("#tablaResultados", timeout=3000)

        checkbox_folio = page.locator("input[name='Tipo'][type='radio']")
        await checkbox_folio.wait_for(state="visible")
        await checkbox_folio.click()

        filtro_url = lambda p: "image-viewer.jsp" in p.url
        async with page.context.expect_page(
            predicate=filtro_url, timeout=5000
        ) as new_page_visor:
            await page.evaluate("generarInforme();")

        page_visor = await new_page_visor.value
        await page_visor.wait_for_load_state()

        frame_visor = page_visor.frame_locator('frame[name="viewerFrame"]')
        link_upload = frame_visor.locator('a[href*="imageManager(2)"]')

        async with page_visor.context.expect_page() as upload_popup_info:
            await link_upload.click()

        pagina_upload = await upload_popup_info.value
        await pagina_upload.wait_for_load_state("domcontentloaded")

        ruta_archivo_acuse = os.path.abspath(os.path.join(DOCUMENTS_UPLOAD, archivo))
        input_file0 = pagina_upload.locator("#file0")
        await input_file0.set_input_files(ruta_archivo_acuse)

        # Submit
        await pagina_upload.click("//input[@type='submit']")

        try:
            await pagina_upload.wait_for_event("close", timeout=10000)
        except:
            if not pagina_upload.is_closed():
                await pagina_upload.close()

        return {
            "status": "OK",
            "folio": folio_sugo,
            "message": "Proceso completado",
            "motivo": "",
        }

    except PlaywrightTimeoutError:
        texto_error_sistema = "No se detectó el mensaje de éxito (Timeout)"

        try:
            await page.wait_for_selector("#BTACEPTAR", timeout=15000)
            texto_error_sistema = await page.locator(
                ".TextoAlerta .txtAlertArqVN"
            ).inner_text()

            async with page.expect_navigation():
                await page.click("#BTACEPTAR")

        except Exception as e_inner:
            print(f"No se pudo interactuar con el modal de error: {e_inner}")
            await page.goto(URL_CIERRE_OPERACIONES, wait_until="domcontentloaded")

        return {
            "status": "ERROR",
            "folio": folio_sugo,
            "message": "Error en registro insumos",
            "motivo": texto_error_sistema.strip(),
        }

    except Exception as e:
        await page.goto(URL_CIERRE_OPERACIONES, wait_until="domcontentloaded")
        return {
            "status": "ERROR",
            "folio": folio_sugo,
            "message": "Error inesperado en el script",
            "motivo": str(e),
        }

    finally:
        # --- LIMPIEZA DE VENTANAS ---
        # Cerramos de la más nueva a la más vieja
        if pagina_upload:
            try:
                if not pagina_upload.is_closed():
                    await pagina_upload.close()
            except:
                pass

        if page_visor:
            try:
                if not page_visor.is_closed():
                    await page_visor.close()
            except:
                pass

        # Opcional: Volver a poner el foco en la página principal
        await page.bring_to_front()


async def finalizacion_wizard(datos: dict, page: Page):
    """Lógica específica para Wizard (Opción 2)."""
    folio_sugo = str(datos.get("Folio Sugo", "")).strip()
    folio_wizard = str(datos.get("Folio Wizard")).strip()
    tipo_respuesta = str(datos.get("Tipo Respuesta")).strip().lower()
    selfservice = str(datos.get("Selfservice", "")).strip().lower()
    dictamen_wizard = str(datos.get("Dictamen Wizard")).strip().lower()

    if not folio_wizard or not tipo_respuesta or not dictamen_wizard:
        return "Folio Wizard o Tipo Respuesta faltante"
    
    if 'ine' in selfservice:
        print(f"Folio INE. Omitiendo: {folio_sugo}")
        #TODO: Implementar logica para los INE
        return "Omitido INE"

    try:
        await page.goto(URL_WIZARD_MIS_TAREAS, timeout=60000)
        await asyncio.sleep(3)
        await page.get_by_role("button", name="Filtros").click()
        await page.fill("textarea[aria-label='Id solicitud']", folio_wizard)
        await asyncio.sleep(2)
        await page.get_by_role("button", name="Buscar").click()

        # Validación de resultados
        try:
            await page.locator(".q-tab-panel").get_by_text(folio_wizard).wait_for(timeout=10_000)
        except:
            return "No encontrado"
        
        await asyncio.sleep(1)
        
        await page.locator(".q-tab-panel").get_by_text(folio_wizard).click()
        await page.get_by_text("Detalle del caso").wait_for(timeout=15_000)
        await page.get_by_text("Detalle del caso").click()

        # Asignación de acuerdo a tipo de respuesta
        if 'negativa' in tipo_respuesta:
            # Respuesta del oficio
            await page.locator(".q-px-lg.q-mb-xl.col-md-3.col-sm-5.col-xs-12.q-mb-lg.field-cell", has_text="Respuesta del oficio").click()
            await page.get_by_role("option", name="Negativa SITI").click()
            await asyncio.sleep(1)

            if 'cargar la respuesta negativa' in dictamen_wizard:
                # ¿Haz validado la carta?
                chekbox_validacion = page.locator("div[aria-label='¿Has validado la  carta de respuesta?']")
                await chekbox_validacion.wait_for(state="visible")
                await chekbox_validacion.click()
                await asyncio.sleep(1)

            if 'positivas insumos' in dictamen_wizard:
                # Acción de cierre
                await page.locator(".q-px-lg.q-mb-xl.col-md-3.col-sm-5.col-xs-12.q-mb-lg.field-cell", has_text="Acciones de cierre - Insumos").click()
                await page.get_by_role("option", name="Cierre Operaciones").click()
                await asyncio.sleep(1)
        
        else:
            # Acción de cierre
            await page.locator(".q-px-lg.q-mb-xl.col-md-3.col-sm-5.col-xs-12.q-mb-lg.field-cell", has_text="Acciones de cierre - Insumos").click()
            await page.get_by_role("option", name="Adjuntar Informe y Cierre Jurídico").click()
            await asyncio.sleep(1)

        # Enio de respuesta
        await page.locator(".q-px-lg.q-mb-xl.col-md-3.col-sm-5.col-xs-12.q-mb-lg.field-cell", has_text="Envio de respuesta").click()
        await page.get_by_role("option", name="Automático").click()
        await asyncio.sleep(1)

        # Botón finalizar
        await page.get_by_role("button", name="Finalizar tarea").click()
        await asyncio.sleep(2)
        
        return "Completado"
    
    except Exception as e:
        print(f"Error en folio {folio_wizard}: {e}")
        return "Error"


async def orchestrator(tipo_tarea: str, modo_oculto: bool):
    """Orquestador único para evitar repetir bucles de ejecución."""
    preparar_entorno()
    
    col_status = "Status Asignacion" if tipo_tarea == "wizard" else "Status SUGO"
    cols_necesarias = ["Folio Sugo", "Folio Wizard", "Tipo Respuesta", "Selfservice", "Dictamen Wizard", "Informe"]
    
    df = cargar_datos(cols_necesarias, col_status)
    if df is None: return

    async with async_playwright() as p:
        # Selección de contexto según la tarea
        if tipo_tarea == "wizard":
            context = await p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                channel="chrome",
                headless=modo_oculto,
                accept_downloads=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--window-size=1920,1080"
                ]
            )
        else:
            user = input("Usuario: ")
            password = getpass.getpass("Contraseña: ")
            browser = await p.chromium.launch(
                headless=modo_oculto,
                channel="chrome",
                args=["--disable-gpu", "--no-sandbox", "--window-size=1920,1080"]
            )
            storage = await manejar_login_intranet(browser, user, password)
            if not storage: return
            context = await browser.new_context(storage_state=storage)

        try:
            page = context.pages[0] if context.pages else await context.new_page()
            
            pendientes = df[df[col_status] == "Pendiente"].index.tolist()
            pbar = tqdm(total=len(pendientes), desc=f"Procesando {tipo_tarea}")

            for i, idx in enumerate(pendientes):
                datos = df.loc[idx].to_dict()
                
                if tipo_tarea == "wizard":
                    resultado = await finalizacion_wizard(datos, page)
                else:
                    resultado = await cierre_operaciones_asig_juridico(datos, page)
                    resultado = resultado.get("status", "Error")

                df.at[idx, col_status] = resultado
                
                # Guardado incremental
                if (i + 1) % BATCH_GUARDADO == 0:
                    df.to_csv(FILE_EXITOS, index=False)
                
                pbar.update(1)

            df.to_csv(FILE_EXITOS, index=False)
            pbar.close()
        finally:
            await context.close()
            if tipo_tarea != "wizard" and 'browser' in locals():
                await browser.close()


def mostrar_menu():
    print("\n" + "="*40)
    print(" BOT WIZARD (Especiales)")
    print("="*40)
    print("1. Iniciar Sesion")
    print("2. Cierre Folio Wizard")
    print("3. Adjuntar Informe SUGO")
    print("4. Salir")
    print("="*40)

# --- MENÚ PRINCIPAL ---
if __name__ == "__main__":

    while True:
        mostrar_menu()
        op = input("Seleccione: ")
        if op == '1':
            asyncio.run(autenticar_google())
        elif op == '2':
            asyncio.run(orchestrator("wizard", modo_oculto=False))
        elif op == '3':
            asyncio.run(orchestrator("sugo", modo_oculto=False))
        elif op == '4':
            break
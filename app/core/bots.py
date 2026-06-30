import asyncio
from app.config import settings
import os
from pathlib import Path
import pandas as pd
from typing import Callable, Optional
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError


def obtener_argumentos_navegador():
    return [
        "--disable-blink-features=AutomationControlled",
        "--disable-gpu",
        "--no-sandbox",
        "--window-size=1920,1080"
    ]


async def autenticar_google(log_callback: Optional[Callable] = None):
    def _log(msg, **kw):
        if log_callback:
            log_callback(msg, **kw)
        else:
            print(msg)

    _log(f"Iniciando autenticación Google (perfil: {settings.USER_DATA_DIR})...")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=settings.USER_DATA_DIR,
            headless=False,
            channel="chrome",
            args=obtener_argumentos_navegador()
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://drive.google.com")
        _log("Navegador abierto. Inicia sesión y cierra la ventana del navegador cuando termines.", success=True)
        await page.wait_for_event("close", timeout=120_000)


def preparar_entorno():
    """Crea la carpeta dist/ y sus subcarpetas necesarias si no existen."""
    carpetas = [
        settings.DIST_DIR,
        settings.DOCUMENTS_UPLOAD,
        settings.USER_DATA_DIR,
    ]
    for carpeta in carpetas:
        Path(carpeta).mkdir(parents=True, exist_ok=True)


def cargar_datos(columnas_requeridas, columna_status, excel_path: Optional[str] = None, progreso_file: Optional[str] = None, log_callback: Optional[Callable] = None):
    """Carga el progreso o el archivo inicial de forma genérica."""
    def _log(msg, **kw):
        if log_callback:
            log_callback(msg, **kw)
        else:
            print(msg)

    ruta_excel = excel_path if excel_path else settings.INPUT_FILE
    
    if not progreso_file:
        if ruta_excel:
            excel_name = Path(ruta_excel).stem
            progreso_file = Path(ruta_excel).parent / f"{excel_name}_resultados.csv"
        else:
            progreso_file = settings.FILE_EXITOS

    if os.path.exists(progreso_file):
        _log(f"Progreso previo encontrado. Continuando desde {progreso_file}...", success=True)
        df = pd.read_csv(progreso_file)
        if set(columnas_requeridas).issubset(df.columns):
            return df
        _log("El archivo de progreso no tiene las columnas necesarias. Cargando original...", warning=True)

    if not ruta_excel or not os.path.exists(ruta_excel):
        _log(f"No se encontró el archivo de entrada: {ruta_excel}", error=True)
        return None

    df = pd.read_excel(ruta_excel)
    if not set(columnas_requeridas).issubset(df.columns):
        _log(f"El Excel debe contener las columnas: {', '.join(columnas_requeridas)}", error=True)
        return None
    df[columna_status] = "Pendiente"

    return df


async def manejar_login_intranet(browser, user, password, log_callback: Optional[Callable] = None):
    """Encapsula la lógica de autenticación en SUGO/Intranet."""
    def _log(msg, **kw):
        if log_callback:
            log_callback(msg, **kw)
        else:
            print(msg)

    context = await browser.new_context(ignore_https_errors=True)
    page = await context.new_page()
    try:
        _log(f"Conectando al portal de autenticación...")
        await page.goto(settings.URL_LOGIN, wait_until="domcontentloaded")
        await page.fill(".name", user)
        await page.fill(".pass", password)
        
        async with context.expect_page() as page_info:
            # Intento de login por click o enter
            if await page.locator("//p[@onclick='validaCampos()']").is_visible():
                await page.evaluate("validaCampos()")
            else:
                await page.keyboard.press("Enter")
        
        _log(f"Usuario '{user}' autenticado con éxito en Intranet.", success=True)
        popup = await page_info.value
        await popup.wait_for_load_state()
        storage = await context.storage_state()
        await context.close()
        return storage
    except Exception as e:
        _log(f"Error durante el login en Intranet: {e}", error=True)
        return None
    

async def cierre_operaciones_asig_juridico(datos: dict, page: Page, informes_dir: Optional[str] = None):
    folio_sugo = str(datos.get("Folio Sugo", "")).strip()
    archivo = str(datos.get("Informe", "")).strip()

    pagina_upload = None
    page_visor = None

    try:
        await page.goto(settings.URL_CIERRE_OPERACIONES, wait_until="domcontentloaded", timeout=6000)

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

        base_dir = Path(informes_dir) if informes_dir else Path(settings.DOCUMENTS_UPLOAD)
        ruta_archivo_acuse = base_dir / archivo
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
            await page.goto(settings.URL_CIERRE_OPERACIONES, wait_until="domcontentloaded")

        return {
            "status": "ERROR",
            "folio": folio_sugo,
            "message": "Error en registro insumos",
            "motivo": texto_error_sistema.strip(),
        }

    except Exception as e:
        await page.goto(settings.URL_CIERRE_OPERACIONES, wait_until="domcontentloaded")
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
        await page.goto(settings.URL_WIZARD_MIS_TAREAS, timeout=60000)
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


async def orchestrator(
    tipo_tarea: str,
    modo_oculto: bool,
    log_callback: Optional[Callable] = None,
    done_callback: Optional[Callable] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    excel_path: Optional[str] = None,
    informes_dir: Optional[str] = None,
    status_callback: Optional[Callable[[int, str], None]] = None,
):
    """
    Orquestador único para ambas tareas RPA.

    Args:
        tipo_tarea:    'wizard' | 'sugo'
        modo_oculto:   True = headless (sin ventana de navegador)
        log_callback:  función(msg, *, success, error, warning) para enviar logs a la UI
        done_callback: función() llamada al finalizar (exitoso o con error)
        user:          usuario de Intranet (solo para tipo_tarea='sugo')
        password:      contraseña de Intranet (solo para tipo_tarea='sugo')
        excel_path:    ruta del archivo Excel de entrada
        informes_dir:  ruta del directorio de informes a cargar
        status_callback: función(row_index, status) para actualizar el estado visual de cada fila
    """
    def _log(msg, **kw):
        if log_callback:
            log_callback(msg, **kw)
        else:
            print(msg)

    try:
        preparar_entorno()

        col_status = "Status Asignacion" if tipo_tarea == "wizard" else "Status SUGO"
        cols_necesarias = ["Folio Sugo", "Folio Wizard", "Tipo Respuesta", "Selfservice", "Dictamen Wizard", "Informe"]

        ruta_excel = excel_path if excel_path else settings.INPUT_FILE
        excel_name = Path(ruta_excel).stem if ruta_excel else "Oficios"
        progreso_file = Path(ruta_excel).parent / f"{excel_name}_resultados.csv" if ruta_excel else settings.FILE_EXITOS

        df = cargar_datos(cols_necesarias, col_status, excel_path, progreso_file, log_callback)
        if df is None:
            _log("No se pudo cargar el archivo de datos. Proceso cancelado.", error=True)
            return

        pendientes = df[df[col_status] == "Pendiente"].index.tolist()
        total = len(pendientes)
        _log(f"Folios pendientes a procesar: {total}")

        if total == 0:
            _log("No hay folios pendientes. El proceso ha finalizado.", success=True)
            return

        async with async_playwright() as p:
            # ── Preparar contexto de navegador según tipo de tarea ──
            if tipo_tarea == "wizard":
                _log(f"Iniciando navegador (modo_oculto={modo_oculto})...")
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=settings.USER_DATA_DIR,
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
                browser = None
            else:
                if not user or not password:
                    _log("Se requieren credenciales para ejecutar el proceso SUGO.", error=True)
                    return
                _log(f"Iniciando navegador para SUGO (modo_oculto={modo_oculto})...")
                browser = await p.chromium.launch(
                    headless=modo_oculto,
                    channel="chrome",
                    args=["--disable-gpu", "--no-sandbox", "--window-size=1920,1080"]
                )
                storage = await manejar_login_intranet(browser, user, password, log_callback)
                if not storage:
                    _log("Error de autenticación. No se puede continuar.", error=True)
                    await browser.close()
                    return
                context = await browser.new_context(storage_state=storage)

            try:
                page = context.pages[0] if context.pages else await context.new_page()

                for i, idx in enumerate(pendientes):
                    datos = df.loc[idx].to_dict()
                    folio = str(datos.get("Folio Sugo", datos.get("Folio Wizard", idx))).strip()
                    _log(f"[{i+1}/{total}] Procesando folio: {folio}")

                    if status_callback:
                        status_callback(idx, "Procesando")

                    if tipo_tarea == "wizard":
                        resultado = await finalizacion_wizard(datos, page)
                    else:
                        resultado_dict = await cierre_operaciones_asig_juridico(datos, page, informes_dir=informes_dir)
                        resultado = resultado_dict.get("status", "Error")
                        motivo = resultado_dict.get("motivo", "")
                        if resultado == "ERROR" and motivo:
                            _log(f"  → Error en folio {folio}: {motivo}", error=True)

                    df.at[idx, col_status] = resultado

                    if status_callback:
                        status_callback(idx, resultado)

                    if resultado in ("Completado", "OK"):
                        _log(f"  → Folio {folio}: {resultado}", success=True)
                    elif resultado in ("Omitido INE", "No encontrado"):
                        _log(f"  → Folio {folio}: {resultado}", warning=True)
                    elif resultado == "Error":
                        _log(f"  → Folio {folio}: Error inesperado", error=True)

                    # Guardado incremental
                    if (i + 1) % settings.BATCH_GUARDADO == 0:
                        df.to_csv(progreso_file, index=False)
                        _log(f"  Progreso guardado ({i+1}/{total} procesados)")

                df.to_csv(progreso_file, index=False)
                _log(f"Proceso finalizado. Resultados guardados en: {progreso_file}", success=True)

            finally:
                await context.close()
                if browser:
                    try:
                        await browser.close()
                    except Exception:
                        pass

    except Exception as e:
        _log(f"Error crítico en el proceso: {e}", error=True)
    finally:
        if done_callback:
            done_callback()

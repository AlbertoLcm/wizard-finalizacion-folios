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
        try:
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto("https://drive.google.com")
            _log("Navegador abierto. Inicia sesión y cierra la ventana del navegador cuando termines.", success=True)
            await page.wait_for_event("close", timeout=120_000)
        finally:
            await context.close()


def preparar_entorno():
    """Crea la carpeta dist/ y sus subcarpetas necesarias si no existen."""
    carpetas = [
        settings.DIST_DIR,
        settings.DOCUMENTS_UPLOAD,
        settings.USER_DATA_DIR,
    ]
    for carpeta in carpetas:
        Path(carpeta).mkdir(parents=True, exist_ok=True)


def cargar_datos(
    columnas_requeridas,
    col_status: str,
    excel_path: Optional[str] = None,
    progreso_file: Optional[str] = None,
    log_callback: Optional[Callable] = None,
):
    """
    Carga el progreso o el archivo inicial de forma genérica.

    Args:
        columnas_requeridas: columnas mínimas que debe tener el Excel de entrada.
        col_status:          columna de status de la tarea actual; se inicializa
                             con "Pendiente" solo si no existe ya en el CSV/Excel.
        excel_path:          ruta del Excel de entrada (usa settings.INPUT_FILE si None).
        progreso_file:       ruta del CSV de progreso (se calcula automáticamente si None).
        log_callback:        función de log opcional.
    """
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
            # Asegurar que la columna de la tarea actual exista sin sobrescribir
            if col_status not in df.columns:
                df[col_status] = "Pendiente"
            return df
        _log("El archivo de progreso no tiene las columnas necesarias. Cargando original...", warning=True)

    if not ruta_excel or not os.path.exists(ruta_excel):
        _log(f"No se encontró el archivo de entrada: {ruta_excel}", error=True)
        return None

    df = pd.read_excel(ruta_excel)
    if not set(columnas_requeridas).issubset(df.columns):
        _log(f"El Excel debe contener las columnas: {', '.join(columnas_requeridas)}", error=True)
        return None

    # Inicializar solo la columna de la tarea actual
    df[col_status] = "Pendiente"

    return df

# =========================================
# Funciones de ejecución de procesos
# =========================================


async def sugo_login(browser, user, password, log_callback: Optional[Callable] = None):
    """Encapsula la lógica de autenticación en SUGO/Intranet."""
    def _log(msg, **kw):
        if log_callback:
            log_callback(msg, **kw)
        else:
            print(msg)

    context = await browser.new_context(ignore_https_errors=True)
    page = await context.new_page()
    try:
        await page.goto(settings.URL_LOGIN, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        await page.fill(".name", user)
        await page.fill(".pass", password)
        await asyncio.sleep(1)

        async with context.expect_page() as page_info:
            if await page.locator("//p[@onclick='validaCampos()']").is_visible():
                await page.evaluate("""() => validaCampos()""")
            else:
                await page.keyboard.press("Enter")

        _log(f"Usuario {user} autenticado exitosamente.", success=True)

        popup = await page_info.value
        await popup.wait_for_load_state()
        await asyncio.sleep(3)

        storage = await context.storage_state()
        await context.close()
        return storage
    except Exception as e:
        _log(f"Error durante el login: {e}", error=True)
        return None
    

async def sugo_cierre_operaciones_asig_juridico(datos: dict, page: Page, informes_dir: Optional[str] = None, log_callback: Optional[Callable] = None):
    def _log(msg, **kw):
        if log_callback:
            log_callback(msg, **kw)
        else:
            print(msg)
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
            await page.locator("#btnAdjOpeC1").click()

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
        except Exception:
            if not pagina_upload.is_closed():
                await pagina_upload.close()

        return "Completado"

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
            _log(f"No se pudo interactuar con el modal de error: {e_inner}", warning=True)
            await page.goto(settings.URL_CIERRE_OPERACIONES, wait_until="domcontentloaded")

        _log(f"Error SUGO Informe: {texto_error_sistema}", error=True)
        return "Error"

    except Exception as e:
        _log(f"Error inesperado en SUGO Informe: {e}", error=True)
        await page.goto(settings.URL_CIERRE_OPERACIONES, wait_until="domcontentloaded")
        return "Error"

    finally:
        # --- LIMPIEZA DE VENTANAS ---
        # Cerramos de la más nueva a la más vieja
        if pagina_upload:
            try:
                if not pagina_upload.is_closed():
                    await pagina_upload.close()
            except Exception:
                pass

        if page_visor:
            try:
                if not page_visor.is_closed():
                    await page_visor.close()
            except Exception:
                pass

        # Opcional: Volver a poner el foco en la página principal
        await page.bring_to_front()


async def sugo_asignacion(folio_sugo, page: Page, log_callback: Optional[Callable] = None):
    def _log(msg, **kw):
        if log_callback:
            log_callback(msg, **kw)
        else:
            print(msg)
    """
        Asignación de folio en SUGO. Gestiona el flujo de asignacion aseguramientos:
        Buscar folio → Seleccionar folio → Confirmar asignación
        (sin seleccionar al abogado, ya que se asigna automáticamente al usuario logueado)
    """
    estado = {"mensajes": [], "finalizado": False}

    async def manejar_dialogos(dialog):
        mensaje = dialog.message.upper()
        estado["mensajes"].append(mensaje)

        await dialog.accept()

        # Si detectamos el mensaje de éxito, marcamos como finalizado
        if "ASIGNADO EXITOSAMENTE" in mensaje:
            estado["finalizado"] = True

    # Activamos el escuchador permanente
    page.on("dialog", manejar_dialogos)

    try:
        await page.goto(settings.URL_ASIGNACION_SUGO, wait_until="domcontentloaded", timeout=6000)

        checkbox = page.locator("#radFolio")
        await checkbox.wait_for(state="visible")
        await checkbox.click()

        await page.fill("#txtFolio", folio_sugo)

        async with page.expect_navigation():
            await page.evaluate("preBuscar()")

        await page.wait_for_selector("#tablaAñadidos1", timeout=3000)

        checkbox_folio = page.locator("#seleccionFolio0")
        await checkbox_folio.wait_for(state="visible")
        await checkbox_folio.click()

        await page.evaluate("preAutoasignar()")

        intentos = 0
        while intentos < 20:  # Espera máxima de 10 segundos (20 * 0.5)
            if estado["finalizado"]:
                return "Completado"

            # Verificamos si apareció el modal de error en lugar del alert
            if await page.locator("#BTACEPTAR").is_visible():
                raise PlaywrightTimeoutError("Apareció modal de error #BTACEPTAR")

            await asyncio.sleep(0.5)
            intentos += 1

        raise PlaywrightTimeoutError("No se recibió confirmación de éxito a tiempo")

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
            _log(f"No se pudo interactuar con el modal de error: {e_inner}", warning=True)
            await page.goto(settings.URL_ASIGNACION_SUGO, wait_until="domcontentloaded")

        _log(f"Error Asignación SUGO: {texto_error_sistema}", error=True)
        return "Error"

    except Exception as e:
        _log(f"Error inesperado en Asignación SUGO: {e}", error=True)
        await page.goto(settings.URL_ASIGNACION_SUGO, wait_until="domcontentloaded")
        return "Error"

    finally:
        try:
            page.remove_listener("dialog", manejar_dialogos)
        except Exception:
            pass
  

async def wizard_finalizacion(datos: dict, page: Page, log_callback: Optional[Callable] = None):
    def _log(msg, **kw):
        if log_callback:
            log_callback(msg, **kw)
        else:
            print(msg)

    folio_wizard = str(datos.get("Folio Wizard")).strip()
    tipo_respuesta = str(datos.get("Tipo Respuesta")).strip().lower()
    selfservice = str(datos.get("Selfservice", "")).strip().lower()
    dictamen_wizard = str(datos.get("Dictamen Wizard")).strip().lower()

    if not folio_wizard or not tipo_respuesta or not dictamen_wizard:
        return "Folio Wizard o Tipo Respuesta faltante"

    if 'ine' in selfservice:
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
        except Exception:
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

        # Envío de respuesta
        await page.locator(".q-px-lg.q-mb-xl.col-md-3.col-sm-5.col-xs-12.q-mb-lg.field-cell", has_text="Envio de respuesta").click()
        await page.get_by_role("option", name="Automático").click()
        await asyncio.sleep(1)

        # Botón finalizar
        await page.get_by_role("button", name="Finalizar tarea").click()
        await asyncio.sleep(2)
        
        return "Completado"
    
    except Exception as e:
        _log(f"Error en wizard_finalizacion (folio={folio_wizard}): {e}", error=True)
        return "Error"


# =========================================
# Orchestrator
# =========================================

# ── Registro declarativo de tareas ────────────────────────────────────────────
# Para agregar una nueva tarea a futuro, añade una entrada aquí con:
#   col_status   → columna del Excel/CSV donde se escribe el resultado por folio
#   pendiente_fn → función(df, col) → lista de índices aún sin procesar
#   requiere_sugo → True si el proceso necesita credenciales de Intranet
#
# El handler real se resuelve en el match/case dentro de orchestrator para que
# cada caso pueda recibir parámetros propios (p.ej. informes_dir).
# ─────────────────────────────────────────────────────────────────────────────
TASK_REGISTRY: dict = {
    "sugo-asignacion": {
        "col_status": "Status SUGO Asignacion",
        "pendiente_fn": lambda df, col: df[
            df[col].isin(["Pendiente", "Error"])
        ].index.tolist(),
        "requiere_sugo": False,
    },
    "wizard-finalizacion": {
        "col_status": "Status WIZARD Finalizacion",
        "pendiente_fn": lambda df, col: df[
            ~df[col].isin(["Completado", "Omitido INE"])
        ].index.tolist(),
        "requiere_sugo": False,
    },
    "sugo-informe": {
        "col_status": "Status SUGO Informe",
        "pendiente_fn": lambda df, col: df[
            ~df[col].isin(["OK", "Completado"])
        ].index.tolist(),
        "requiere_sugo": True,
    },
    # ── Punto de extensión: agrega nuevas tareas aquí ─────────────────────────
    # "nueva_tarea": {
    #     "col_status": "Status Nueva Tarea",
    #     "pendiente_fn": lambda df, col: df[df[col] == "Pendiente"].index.tolist(),
    #     "requiere_sugo": False,
    # },
}


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
    Orquestador único para todas las tareas RPA.

    El tipo de tarea se resuelve mediante TASK_REGISTRY (datos) +
    match/case (lógica de navegador y handler). Para añadir una nueva
    tarea basta con:
      1. Registrarla en TASK_REGISTRY.
      2. Añadir un case en el bloque de inicialización del navegador.
      3. Añadir un case en el bloque de despacho del handler.

    Args:
        tipo_tarea:      clave en TASK_REGISTRY ('wizard' | 'sugo' | 'asignacion' | ...)
        modo_oculto:     True = headless (sin ventana de navegador)
        log_callback:    función(msg, *, success, error, warning) para enviar logs a la UI
        done_callback:   función() llamada al finalizar (exitoso o con error)
        user:            usuario de Intranet (solo si requiere_sugo=True)
        password:        contraseña de Intranet (solo si requiere_sugo=True)
        excel_path:      ruta del archivo Excel de entrada
        informes_dir:    ruta del directorio de informes a cargar (tarea 'sugo')
        status_callback: función(row_index, status) para actualizar el estado visual por fila
    """
    def _log(msg, **kw):
        if log_callback:
            log_callback(msg, **kw)
        else:
            print(msg)

    try:
        preparar_entorno()

        # ── Validar que el tipo de tarea sea conocido ─────────────────────────
        if tipo_tarea not in TASK_REGISTRY:
            _log(
                f"Tipo de tarea desconocido: '{tipo_tarea}'. "
                f"Tareas disponibles: {list(TASK_REGISTRY)}",
                error=True,
            )
            return

        tarea_cfg = TASK_REGISTRY[tipo_tarea]
        col_status = tarea_cfg["col_status"]

        # Columnas mínimas requeridas en el Excel de entrada
        cols_necesarias = [
            "Folio Sugo", "Folio Wizard", "Tipo Respuesta",
            "Selfservice", "Dictamen Wizard", "Informe", "Fecha Cierre"
        ]

        ruta_excel = excel_path if excel_path else settings.INPUT_FILE
        excel_name = Path(ruta_excel).stem if ruta_excel else "Oficios"
        progreso_file = Path(ruta_excel).parent / f"{excel_name}_resultados.csv" if ruta_excel else settings.FILE_EXITOS

        # Bug fix: cargar_datos ahora recibe un solo col_status en lugar de dos
        df = cargar_datos(
            cols_necesarias,
            col_status,
            excel_path,
            progreso_file,
            log_callback,
        )
        if df is None:
            _log("No se pudo cargar el archivo de datos. Proceso cancelado.", error=True)
            return

        pendientes = tarea_cfg["pendiente_fn"](df, col_status)
        total = len(pendientes)
        _log(f"Folios pendientes a procesar: {total}")

        if total == 0:
            _log("No hay folios pendientes. El proceso ha finalizado.", success=True)
            return

        # ── Validar credenciales si la tarea las necesita ─────────────────────
        if tarea_cfg["requiere_sugo"] and (not user or not password):
            _log("Se requieren credenciales para ejecutar este proceso.", error=True)
            return

        async with async_playwright() as p:

            # ── Inicialización del navegador (switch por tipo_tarea) ───────────
            # Bug fix: las claves deben coincidir exactamente con TASK_REGISTRY
            match tipo_tarea:

                case "wizard-finalizacion" | "sugo-asignacion":
                    _log(f"Iniciando navegador con perfil persistente (modo_oculto={modo_oculto})...")
                    context = await p.chromium.launch_persistent_context(
                        user_data_dir=settings.USER_DATA_DIR,
                        channel="chrome",
                        headless=modo_oculto,
                        accept_downloads=True,
                        args=obtener_argumentos_navegador(),
                    )
                    browser = None

                case "sugo-informe":
                    _log(f"Iniciando navegador para SUGO Informe (modo_oculto={modo_oculto})...")
                    browser = await p.chromium.launch(
                        headless=modo_oculto,
                        channel="chrome",
                        args=["--disable-gpu", "--no-sandbox", "--window-size=1920,1080"],
                    )
                    storage = await sugo_login(browser, user, password, log_callback)
                    if not storage:
                        _log("Error de autenticación. No se puede continuar.", error=True)
                        await browser.close()
                        return
                    context = await browser.new_context(
                        storage_state=storage, ignore_https_errors=True
                    )

                case _:
                    # Rama de seguridad (no debería alcanzarse tras la validación anterior)
                    _log(f"Tipo de tarea sin configuración de navegador: '{tipo_tarea}'", error=True)
                    return

            try:
                page = context.pages[0] if context.pages else await context.new_page()

                for i, idx in enumerate(pendientes):
                    datos = df.loc[idx].to_dict()
                    folio = str(datos.get("Folio Sugo", datos.get("Folio Wizard", idx))).strip()
                    _log(f"[{i+1}/{total}] Procesando folio: {folio}")

                    # Marcar "Procesando" en el Excel y notificar a la UI
                    df.at[idx, col_status] = "Procesando"
                    if status_callback:
                        status_callback(idx, "Procesando")

                    # ── Despacho del handler (switch por tipo_tarea) ──────────
                    match tipo_tarea:

                        case "wizard-finalizacion":
                            resultado = await wizard_finalizacion(
                                datos, page, log_callback=log_callback
                            )

                        case "sugo-asignacion":
                            folio_sugo = str(datos.get("Folio Sugo", "")).strip()
                            resultado = await sugo_asignacion(folio_sugo, page, log_callback=log_callback)

                        case "sugo-informe":
                            resultado = await sugo_cierre_operaciones_asig_juridico(
                                datos, page, informes_dir=informes_dir, log_callback=log_callback
                            )

                        case _:
                            resultado = "Error"
                            _log(f"  → Tipo de tarea sin handler: '{tipo_tarea}'", error=True)

                    # ── Persistir resultado en la columna de status de esta tarea ─
                    df.at[idx, col_status] = resultado
                    if status_callback:
                        status_callback(idx, resultado)

                    # ── Log de resultado ──────────────────────────────────────
                    if resultado in ("Completado", "OK", "Asignado"):
                        _log(f"  → Folio {folio}: {resultado}", success=True)
                    elif resultado in ("Omitido INE", "No encontrado"):
                        _log(f"  → Folio {folio}: {resultado}", warning=True)
                    elif resultado in ("Error", "ERROR"):
                        _log(f"  → Folio {folio}: Error inesperado", error=True)
                    else:
                        _log(f"  → Folio {folio}: {resultado}")

                    # ── Guardado incremental al CSV de progreso ───────────────
                    if (i + 1) % settings.BATCH_GUARDADO == 0:
                        df.to_csv(progreso_file, index=False)
                        _log(f"  Progreso guardado ({i+1}/{total} procesados)")

                # Guardado final
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


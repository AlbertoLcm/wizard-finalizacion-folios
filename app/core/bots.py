import asyncio
from app.config import settings
import os
from pathlib import Path
import pandas as pd
from typing import Tuple, Callable, Optional
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright, TimeoutError as PlaywrightTimeoutError
from datetime import datetime
import re
from pathlib import Path
import sys
import json
import shutil

# ================================================
#           Utils
# ================================================

def estandarizar_fechas(fecha):
    meses_es = {
        "ene": "01",
        "feb": "02",
        "mar": "03",
        "abr": "04",
        "may": "05",
        "jun": "06",
        "jul": "07",
        "ago": "08",
        "sep": "09",
        "oct": "10",
        "nov": "11",
        "dic": "12",
    }
    fecha = str(fecha).strip().lower()
    if pd.isnull(fecha) or fecha == "nat" or fecha == "":
        return ""
    for mes, num in meses_es.items():
        if mes in fecha:
            fecha = fecha.replace(mes, num)
            break
    formatos = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d-%m-%y",
        "%d-%m-%Y",
        "%d %m %Y",
        "%m/%d/%Y",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%y %H:%M:%S",
        "%d-%m-%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d-%m-%y %H:%M:%S",
    ]
    for formato in formatos:
        try:
            fecha_obj = datetime.strptime(fecha, formato)
            return fecha_obj.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return ""


def preparar_entorno():
    """Borra la carpeta dist/ y sus subcarpetas si existen, y las vuelve a crear."""
    carpetas = [
        settings.DIST_DIR,
        settings.USER_DATA_DIR,
    ]
    
    for carpeta in carpetas:
        path_obj = Path(carpeta)
        
        if path_obj.exists():
            shutil.rmtree(path_obj)
            
        path_obj.mkdir(parents=True, exist_ok=True)

def cargar_credenciales_sugo(log_callback) -> Tuple[str, str]:
    def _log(msg, **kw):
        if log_callback:
            log_callback(msg, **kw)
        else:
            print(msg)

    """Carga usuario y contraseña del archivo JSON."""
    try:
        with open(settings.ARCHIVO_CREDENCIALES, "r", encoding="utf-8") as f:
            creds = json.load(f)
        return creds["user"], creds["password"]
    except FileNotFoundError:
        _log(f"No se encontró el archivo '{settings.ARCHIVO_CREDENCIALES}'.", error=True)
        sys.exit(1)
    except KeyError as exc:
        _log(f"Formato de credenciales inválido. Falta la clave {exc}.", error=True)
        sys.exit(1)
    except Exception as exc:
        _log(f"Error inesperado al cargar credenciales: {exc}", error=True)
        sys.exit(1)


def cargar_datos(log_callback):
    def _log(msg, **kw):
        if log_callback:
            log_callback(msg, **kw)
        else:
            print(msg)

    if Path(settings.TEMP_FILE).exists():
        df = pd.read_csv(settings.TEMP_FILE)
        
    else:
        df = pd.read_excel(settings.INPUT_FILE)

        if not set(settings.COLUMNS_REQUIRED).issubset(df.columns):
            _log(f"El Excel debe contener las columnas: {', '.join(settings.COLUMNS_REQUIRED)}", error=True)
            return None

        # Estandarización IMPORTANTE de FECHA CIERRE
        df["Fecha Cierre"] = (
            pd.to_datetime(df["Fecha Cierre"].apply(estandarizar_fechas))
            .fillna(pd.Timestamp.today().normalize())
            .dt.strftime("%d/%m/%Y")
        )

        nuevas_columnas = ["Estatus Asignacion", "Estatus Wizard", "Estatus Informe"]
        df[nuevas_columnas] = "pendiente"

# =========================================
# Funciones de ejecución de procesos
# =========================================

async def sugo_asignacion(folio_sugo, page: Page):
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

        await page.evaluate("preAutoasignar();")

        intentos = 0
        while intentos < 30:  # Espera máxima de 15 segundos (30 * 0.5)
            if estado["finalizado"]:
                return {
                    "status": "ok",
                    "message": "Asignación realizada correctamente"
                }

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
            await page.goto(settings.URL_ASIGNACION_SUGO, wait_until="domcontentloaded")

        return {
            "status": "error",
            "message": texto_error_sistema
        }

    except Exception:
        await page.goto(settings.URL_ASIGNACION_SUGO, wait_until="domcontentloaded")
        return {
            "status": "error",
            "message": "Ocurrio un error inesperado"
        }

    finally:
        try:
            page.remove_listener("dialog", manejar_dialogos)
        except Exception:
            pass


async def wizard_finalizacion(datos: dict, page: Page):
    
    folio_wizard = str(datos.get("Folio Wizard")).strip()
    tipo_respuesta = str(datos.get("Tipo Respuesta")).strip().lower()
    selfservice = str(datos.get("Selfservice", "")).strip().lower()
    dictamen_wizard = str(datos.get("Dictamen Wizard")).strip().lower()

    if not folio_wizard or not tipo_respuesta or not dictamen_wizard:
        return {
            "status": "error",
            "message": "Faltan parámetros requeridos: folio_wizard, tipo_respuesta o dictamen_wizard."
        }

    if 'ine' in selfservice:
        #TODO: Implementar logica para los INE
        return {
            "status": "ok",
            "message": "Folio INE fue omitido."
        }

    try:
        for intento in range(2):
            await page.goto(settings.URL_WIZARD_MIS_TAREAS, timeout=80_000)
            await asyncio.sleep(3)
            await page.get_by_role("button", name="Filtros").click()
            await asyncio.sleep(3)
            await page.fill("textarea[aria-label='Id solicitud']", folio_wizard)
            await asyncio.sleep(3)
            await page.get_by_role("button", name="Buscar").click()
            await asyncio.sleep(3)

            try:
                await page.locator(".q-tab-panel").get_by_text(folio_wizard).wait_for(timeout=5_000)
                break
            except Exception:
                if intento == 1:
                  return {
                      "status": "error",
                      "message": "No se encontro el Folio."
                  }
            
        await asyncio.sleep(2)
        
        await page.locator(".q-tab-panel").get_by_text(folio_wizard).click()
        await page.get_by_text("Detalle del caso").wait_for(timeout=80_000)
        await page.get_by_text("Detalle del caso").click()
        await asyncio.sleep(2)

        if 'negativa' in tipo_respuesta:
            await page.locator(".q-px-lg.q-mb-xl.col-md-3.col-sm-5.col-xs-12.q-mb-lg.field-cell", has_text="Respuesta del oficio").click()
            await page.get_by_role("option", name="Negativa SITI").click()
            await asyncio.sleep(1)

            if 'cargar la respuesta negativa' in dictamen_wizard:
                chekbox_validacion = page.locator("div[aria-label='¿Has validado la  carta de respuesta?']")
                await chekbox_validacion.wait_for(state="visible")
                await chekbox_validacion.click()
                await asyncio.sleep(1)

            if 'positivas insumos' in dictamen_wizard:
                await page.locator(".q-px-lg.q-mb-xl.col-md-3.col-sm-5.col-xs-12.q-mb-lg.field-cell", has_text="Acciones de cierre - Insumos").click()
                await page.get_by_role("option", name="Cierre Operaciones").click()
                await asyncio.sleep(1)
        
        else:
            await page.locator(".q-px-lg.q-mb-xl.col-md-3.col-sm-5.col-xs-12.q-mb-lg.field-cell", has_text="Acciones de cierre - Insumos").click()
            await page.get_by_role("option", name="Adjuntar Informe y Cierre Jurídico").click()
            await asyncio.sleep(1)

        await page.locator(".q-px-lg.q-mb-xl.col-md-3.col-sm-5.col-xs-12.q-mb-lg.field-cell", has_text="Envio de respuesta").click()
        await page.get_by_role("option", name="Automático").click()
        await asyncio.sleep(1)

        await page.get_by_role("button", name="Finalizar tarea").click()
        await asyncio.sleep(2)
        
        return {
            "status": "ok",
            "message": "Finalización correcta."
        }
    
    except Exception:
        return {
            "status": "error",
            "message": "Ocurrio un error inesperado en el portal de WIZARD."
        }


async def sugo_cierre_operaciones_asig_juridico(datos: dict, page: Page, informes_dir: str):

    folio_sugo = str(datos.get("Folio Sugo", "")).strip()
    fecha_cierre = str(datos.get("Fecha Cierre", "")).strip()
    informes_dir = Path(informes_dir)

    if not folio_sugo:
        return {
            "status": "error",
            "message": "Falta el Folio Sugo."
        }
    
    file_informe = next(informes_dir.glob(f"*{folio_sugo}*"), None)

    if not file_informe:
        return {
            "status": "error",
            "message": "No se encontro el informe en la carpeta seleccionada."
        }

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

        if fecha_cierre:
            await page.evaluate(
                f"document.getElementById('fechaFin2').value = '{fecha_cierre}'"
            )

        try:
            filtro_url = lambda p: "image-viewer.jsp" in p.url
            async with page.context.expect_page(
                predicate=filtro_url, timeout=5000
            ) as new_page_visor:
                await page.locator("#btnAdjJuriC1").click()

            page_visor = await new_page_visor.value
            await page_visor.wait_for_load_state()

        except Exception as e:
            return {
                "status": "error",
                "message": "No se abrio el VISOR, revisa la VPN."
            }

        frame_visor = page_visor.frame_locator('frame[name="viewerFrame"]')
        link_upload = frame_visor.locator('a[href*="imageManager(2)"]')

        async with page_visor.context.expect_page() as upload_popup_info:
            await link_upload.click()

        pagina_upload = await upload_popup_info.value
        await pagina_upload.wait_for_load_state("domcontentloaded")

        input_file0 = pagina_upload.locator("#file0")
        await input_file0.set_input_files(file_informe)

        # Submit
        await pagina_upload.click("//input[@type='submit']")

        try:
            await pagina_upload.wait_for_event("close", timeout=10_000)
        except Exception:
            if not pagina_upload.is_closed():
                await pagina_upload.close()

        return {
            "status": "ok",
            "message": "Se cargo exitosamente el informe en SUGO."
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
            await page.goto(settings.URL_CIERRE_OPERACIONES, wait_until="domcontentloaded")

        return {
            "status": "error",
            "message": texto_error_sistema
        }

    except Exception as e:
        await page.goto(settings.URL_CIERRE_OPERACIONES, wait_until="domcontentloaded")
        return {
            "status": "error",
            "message": "Ocurrio un error inesperado en el portal de SUGO."
        }

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

        await page.bring_to_front()


# ================================================
#           Browser
# ================================================

async def load_page_wizard(context: BrowserContext, p: Playwright, headless: bool):
    page_wizard = await context.new_page()

    await page_wizard.goto(settings.URL_WIZARD, timeout=10_000)
    await page_wizard.wait_for_load_state(state="domcontentloaded")

    if 'idp/profile' in page_wizard.url or 'accounts.google' in page_wizard.url:
        await context.close()

        context = await p.chromium.launch_persistent_context(
            user_data_dir="dist/perfil_prueba",
            headless=False,
            channel="chrome",
            args=settings.ARGUMENTOS_CHROME
        )
        page_login = context.pages[0] if context.pages else await context.new_page()

        await page_login.goto(settings.URL_LOGIN_GOOGLE, timeout=10_000)
        await page_login.wait_for_load_state(state="domcontentloaded")

        await page_login.wait_for_url(re.compile(r"myaccount"), timeout=0)
        
        await context.close()

        context = await p.chromium.launch_persistent_context(
            user_data_dir="dist/perfil_prueba",
            headless=headless,
            channel="chrome",
            args=settings.ARGUMENTOS_CHROME
        )
        page_wizard = context.pages[0] if context.pages else await context.new_page()
        
        await page_wizard.goto(settings.URL_WIZARD, timeout=10_000)
        await page_wizard.wait_for_load_state(state="domcontentloaded")

    if not 'welcome-page' in page_wizard.url:
        return context, None

    return context, page_wizard


async def load_page_sugo(context: BrowserContext, user: str, password: str) -> Optional[Page]:
    page_sugo = await context.new_page()

    try:
        async with context.expect_page(timeout=3_000) as page_info:
            await page_sugo.goto(settings.URL_SUGO_LOGIN, timeout=10_000)

        popup = await page_info.value
        await popup.wait_for_load_state()
        await popup.close()

        await page_sugo.bring_to_front()
        await page_sugo.goto(settings.URL_SUGO, timeout=5_000)
        await page_sugo.wait_for_load_state("domcontentloaded")

    except Exception:

        await asyncio.sleep(2)
        await page_sugo.fill(".name", user)
        await page_sugo.fill(".pass", password)
        await asyncio.sleep(1)

        try:
            async with context.expect_page(timeout=20_000) as page_info:
                if await page_sugo.locator("//p[@onclick='validaCampos()']").is_visible():
                    await page_sugo.evaluate("validaCampos()")

            popup = await page_info.value
            await popup.wait_for_load_state()
            await popup.close()

            await page_sugo.bring_to_front()
            await page_sugo.goto(settings.URL_SUGO, timeout=5_000)
            await page_sugo.wait_for_load_state("domcontentloaded")

        except Exception as e:
            return None

    return page_sugo


# =========================================
# Orchestrator
# =========================================

async def orchestrator(
    df: pd.DataFrame,
    tipo_tarea: str,
    modo_oculto: bool,
    informes_dir: str,
    log_callback: Optional[Callable] = None,
    done_callback: Optional[Callable] = None,
    status_callback: Optional[Callable[[int, str], None]] = None,
):
    def _log(msg, **kw):
        if log_callback:
            log_callback(msg, **kw)
        else:
            print(msg)

    try:
        user, password = cargar_credenciales_sugo(log_callback)

        TASK_REGISTRY = ["asignacion", "cierre_oficio"]

        # ── Validar que el tipo de tarea sea conocido ─────────────────────────
        if tipo_tarea not in TASK_REGISTRY:
            _log(
                f"Tipo de tarea desconocido: '{tipo_tarea}'. "
                f"Tareas disponibles: {list(TASK_REGISTRY)}",
                error=True,
            )
            return
        
        async with async_playwright() as p:

            context = await p.chromium.launch_persistent_context(
                user_data_dir=settings.USER_DATA_DIR,
                headless=modo_oculto,
                channel="chrome",
                args=settings.ARGUMENTOS_CHROME
            )

            for page in context.pages:
                await page.close()


            match tipo_tarea:

                case "cierre_oficio":
                    _log(f"Iniciando proceso Cierre Oficio (modo_oculto={modo_oculto})...")
                    pending_folios = df[(df['Estatus Wizard'] != "ok") | (df['Estatus Informe'] != "ok")]
                    total_pending = len(pending_folios)

                    # Abrimos la pestaña WIZARD y la pestaña SUGO
                    context, page_wizard = await load_page_wizard(context, p, modo_oculto)
                    page_sugo = await load_page_sugo(context, user, password)

                    if not page_wizard or not page_sugo:
                        _log("No se pudo abrir WIZARD o SUGO, Revisar credenciales...", error=True)
                        return

                case "asignacion":
                    _log(f"Iniciando proceso Asignación (modo_oculto={modo_oculto})...")
                    pending_folios = df[df['Estatus Asignacion'] != "ok"]
                    total_pending = len(pending_folios)

                    # Abrimos solo la pestaña
                    page_sugo = await load_page_sugo(context, user, password)

                    if not page_sugo:
                        _log("No se pudo abrir SUGO, Revisar credenciales...", error=True)

                case _:
                    _log(f"No se encontro el tipo de actividad a realizar: '{tipo_tarea}'", error=True)
                    return

            try:
                for i, (idx, row) in enumerate(pending_folios.iterrows(), start=1):
                    data_folio = row.to_dict()

                    folio_sugo = data_folio.get("Folio Sugo", "")

                    _log(f"\n[{i}/{total_pending}] => {folio_sugo}:")

                    # ── Despacho del handler (switch por tipo_tarea) ──────────
                    match tipo_tarea:

                        case "wizard-finalizacion":
                            status_wizard = data_folio.get("Estatus Wizard")
                            status_sugo = data_folio.get("Estatus Informe")

                            # Proceso WIZARD
                            df.at[idx, "Estatus Wizard"] = "Procesando"
                            if status_callback:
                                status_callback(idx, "Procesando")

                            if status_wizard != "ok":
                                await page_wizard.bring_to_front()
                                resultados_wizard = await wizard_finalizacion(data_folio, page_wizard)
                                _log(f"     → WIZARD: {resultados_wizard['status']} - {resultados_wizard['message']}")
                                df.loc[idx, "Estatus Wizard"] = resultados_wizard["status"]
                                if status_callback:
                                    status_callback(idx, resultados_wizard['status'])

                                if resultados_wizard['status'] != "ok":
                                    continue

                            # Proceso SUGO INFORME
                            df.at[idx, "Estatus Informe"] = "Procesando"
                            if status_callback:
                                status_callback(idx, "Procesando")

                            if status_sugo != "ok":
                                await page_sugo.bring_to_front()
                                resultados_informe = await sugo_cierre_operaciones_asig_juridico(data_folio, page_sugo, informes_dir)
                                _log(f"     → INFORME: {resultados_informe['status']} - {resultados_informe['message']}")
                                df.loc[idx, "Estatus Informe"] = resultados_informe["status"]
                                if status_callback:
                                    status_callback(idx, resultados_informe["status"])


                        case "sugo-asignacion":
                            df.at[idx, "Estatus Asignacion"] = "Procesando"
                            if status_callback:
                                status_callback(idx, "Procesando")

                            await page_sugo.bring_to_front()
                            resultados_asignacion = await sugo_asignacion(folio_sugo, page_sugo)
                            _log(f"     → ASIGNACION: {resultados_asignacion['status']} - {resultados_asignacion['message']}")
                            df.loc[idx, "Estatus Asignacion"] = resultados_asignacion["status"]
                            if status_callback:
                                status_callback(idx, resultados_asignacion["status"])

                        case _:
                            _log(f"     → Tipo de tarea sin handler: '{tipo_tarea}'", error=True)


                    # ── Guardado incremental al CSV de progreso ───────────────
                    if (i) % settings.BATCH_GUARDADO == 0:
                        df.to_csv(settings.TEMP_FILE, index=False)

            except Exception as e:
                _log(f"El proceso se interrumpió por un errror en la iteración {i}: {e}", error=True)

            finally:
                # Guardado final
                df.to_csv(settings.TEMP_FILE, index=False)
                _log(f"Proceso finalizado. Resultados guardados en: {settings.TEMP_FILE}", success=True)
                await context.close()

    except Exception as e:
        _log(f"Error crítico en el proceso: {e}", error=True)
    finally:
        if done_callback:
            done_callback()


import asyncio
import threading

from PIL import Image
import customtkinter as ctk

from app.config import settings
from app.core.bots import autenticar_google, orchestrator

from app.ui.panel_logs import PanelLogs
from app.ui.panel_controls import PanelControls
from app.ui.panel_grid import PanelGrid
from app.ui.dialog_login import DialogLogin
from app.ui.dialog_resume import DialogResume


class BotWizardApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.img_bbva = ctk.CTkImage(
            Image.open(settings.ASSETS_DIR / "bbva-blue.png"),
            size=(85, 26)
        )

        self.img_bbva_white = ctk.CTkImage(
            Image.open(settings.ASSETS_DIR / "bbva-white.png"),
            size=(53, 16)
        )

        self.icon_security = ctk.CTkImage(
            Image.open(settings.ASSETS_DIR / "security-token-white.png"),
            size=(18, 18)
        )

        self.icon_trash = ctk.CTkImage(
            Image.open(settings.ASSETS_DIR / "trash-white.png"),
            size=(18, 18)
        )

        self.icon_off = ctk.CTkImage(
            Image.open(settings.ASSETS_DIR / "on-off.png"),
            size=(18, 18)
        )

        self.title(settings.APP_TITLE)
        self.geometry("1200x800")
        self.resizable(True, True)
        self.configure(fg_color=settings.COLOR_SAND)

        # Variables de estado
        self.excel_path = None
        self.informes_path = None

        # ==========================================
        # --- INTERFAZ ---
        # ==========================================

        self.grid_columnconfigure(0, weight=3, minsize=350)
        self.grid_columnconfigure(1, weight=7, minsize=800)
        self.grid_rowconfigure(0, weight=5, minsize=350) # Grid
        self.grid_rowconfigure(1, weight=5, minsize=350) # Logs
        self.grid_rowconfigure(2, weight=0)              # Bottom bar

        # ==========================================
        # --- PANEL IZQUIERDO (CONTROLES) ---
        # ==========================================
        
        self.panel_izq = PanelControls(
            self,
            image_logo=self.img_bbva,
            icon_off=self.icon_off,
            cmd_login=self.cmd_login,
            cmd_exit=self.destroy,
            cmd_sugo=self.cmd_sugo,
            cmd_wizard=self.cmd_wizard,
            cmd_excel_selected=self.on_excel_selected,
            cmd_folder_selected=self.on_folder_selected,
        )
        self.panel_izq.grid(row=0, column=0, rowspan=2, padx=(20, 10), pady=(20, 10), sticky="nsew")

        # ==========================================
        # --- PANEL DERECHO SUPERIOR (GRID) ---
        # ==========================================
        self.panel_grid = PanelGrid(self)
        self.panel_grid.grid(row=0, column=1, padx=(10, 20), pady=(20, 10), sticky="nsew")

        # ==========================================
        # --- PANEL DERECHO INFERIOR (LOGS) ---
        # ==========================================
        self.panel_logs = PanelLogs(self, icon_trash=self.icon_trash)
        self.panel_logs.grid(row=1, column=1, padx=(10, 20), pady=(10, 10), sticky="nsew")

        # ==========================================
        # --- BARRA INFERIOR (BRANDING) ---
        # ==========================================
        self.panel_bottom = ctk.CTkFrame(self, fg_color=settings.COLOR_DARK_BLUE, height=35, corner_radius=0)
        self.panel_bottom.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self.panel_bottom.pack_propagate(False)

        self.lbl_brand_left = ctk.CTkLabel(
            self.panel_bottom, text="  Seguridad  ·  Confianza  ·  Innovación",
            image=self.icon_security, compound="left",
            font=ctk.CTkFont(size=12), text_color="#8997B5"
        )
        self.lbl_brand_left.pack(side="left", padx=20)

        self.lbl_brand_right = ctk.CTkLabel(
            self.panel_bottom, text="  Atención Autoridades  ", 
            image=self.img_bbva_white, compound="left",
            font=ctk.CTkFont(size=12), text_color="white"
        )
        self.lbl_brand_right.pack(side="right", padx=20)

        # Cargar valores por defecto si existen
        import os
        if os.path.exists(settings.INPUT_FILE):
            self.excel_path = str(settings.INPUT_FILE)
            self.panel_izq.set_excel_path(self.excel_path)
            self.cargar_datos_excel()

        if os.path.exists(settings.DOCUMENTS_UPLOAD):
            self.informes_path = str(settings.DOCUMENTS_UPLOAD)
            self.panel_izq.set_folder_path(self.informes_path)

        self.panel_logs.agregar_log("Sistema Bot Wizard iniciado correctamente.", success=True)

    # ==========================================
    # HELPERS INTERNOS
    # ==========================================

    def _log(self, msg, **kwargs):
        """Envía un mensaje al panel de logs de forma thread-safe."""
        self.after(0, lambda: self.panel_logs.agregar_log(msg, **kwargs))

    def _set_ui_bloqueada(self, bloqueada: bool):
        """Bloquea o desbloquea la UI (thread-safe)."""
        self.after(0, lambda: self.panel_izq.bloquear_ui(bloqueada))

    def _set_estado(self, msg, color=settings.COLOR_GREEN, is_processing=False):
        """Actualiza el estado inferior (thread-safe)."""
        self.after(0, lambda: self.panel_izq.cambiar_estado(msg, color=color, is_processing=is_processing))

    def _on_proceso_terminado(self):
        """Callback llamado desde el hilo del bot cuando termina (éxito o error)."""
        self._set_ui_bloqueada(False)
        self._set_estado("Listo", color=settings.COLOR_GREEN, is_processing=False)

    def _ejecutar_en_hilo(self, coro):
        """Lanza una coroutine asyncio en un hilo de fondo sin bloquear la UI."""
        def _runner():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(coro)
            finally:
                loop.close()

        hilo = threading.Thread(target=_runner, daemon=True)
        hilo.start()

    # ==========================================
    # EVENTOS DE LOS BOTONES
    # ==========================================

    def cmd_login(self):
        """Botón 1 — Iniciar Sesión Google Drive (persistente)."""
        self._log("Iniciando proceso de autenticación Google Drive...")
        self._set_estado("Autenticando Google...", color=settings.COLOR_CYAN, is_processing=True)
        self._set_ui_bloqueada(True)

        async def _tarea():
            try:
                await autenticar_google(log_callback=self._log)
                self._log("Sesión de Google Drive guardada correctamente.", success=True)
            except Exception as e:
                self._log(f"Error durante la autenticación: {e}", error=True)
            finally:
                self._on_proceso_terminado()

        self._ejecutar_en_hilo(_tarea())

    def _verificar_progreso_y_ejecutar(self, ejecutar_callback):
        if not self.excel_path:
            self._log("Por favor, seleccione un archivo Excel de entrada antes de iniciar.", error=True)
            return

        from pathlib import Path
        import os
        excel_path_obj = Path(self.excel_path)
        excel_name = excel_path_obj.stem
        progreso_file = excel_path_obj.parent / f"{excel_name}_resultados.csv"

        if os.path.exists(progreso_file):
            def on_resume():
                self._log("Retomando el progreso anterior...", success=True)
                ejecutar_callback()

            def on_fresh():
                try:
                    os.remove(progreso_file)
                    self._log("Progreso anterior eliminado. Iniciando desde cero...", success=True)
                except Exception as e:
                    self._log(f"No se pudo limpiar el progreso anterior: {e}", error=True)
                self.cargar_datos_excel()
                ejecutar_callback()

            def on_cancel():
                self._log("Operación cancelada por el usuario.", warning=True)

            DialogResume(self, callback_resume=on_resume, callback_fresh=on_fresh, callback_cancel=on_cancel)
        else:
            ejecutar_callback()

    def cmd_wizard(self):
        """Botón 2 — Cierre Folio Wizard."""
        def _iniciar_wizard():
            modo_oculto = self.panel_izq.get_modo_oculto()
            modo_txt = "oculto (headless)" if modo_oculto else "visible"
            self._log(f"Iniciando Cierre Folio Wizard en modo {modo_txt}...")
            self._set_estado("Ejecutando Wizard...", color=settings.COLOR_CYAN, is_processing=True)
            self._set_ui_bloqueada(True)

            coro = orchestrator(
                tipo_tarea="wizard",
                modo_oculto=modo_oculto,
                log_callback=self._log,
                done_callback=self._on_proceso_terminado,
                excel_path=self.excel_path,
                informes_dir=self.informes_path,
                status_callback=self._update_row_status,
            )
            self._ejecutar_en_hilo(coro)

        self._verificar_progreso_y_ejecutar(_iniciar_wizard)

    def cmd_sugo(self):
        """Botón 3 — Adjuntar Informe SUGO (pide credenciales primero)."""
        def _iniciar_sugo():
            self._log("Preparando proceso SUGO. Solicitando credenciales...")
            self._set_estado("Esperando credenciales...", color=settings.COLOR_CYAN, is_processing=True)
            self._set_ui_bloqueada(True)

            def _on_credenciales_ok(user: str, password: str):
                modo_oculto = self.panel_izq.get_modo_oculto()
                modo_txt = "oculto (headless)" if modo_oculto else "visible"
                self._log(f"Credenciales recibidas. Iniciando SUGO en modo {modo_txt}...")
                self._set_estado("Adjuntando informe SUGO...", color=settings.COLOR_CYAN, is_processing=True)

                coro = orchestrator(
                    tipo_tarea="sugo",
                    modo_oculto=modo_oculto,
                    log_callback=self._log,
                    done_callback=self._on_proceso_terminado,
                    user=user,
                    password=password,
                    excel_path=self.excel_path,
                    informes_dir=self.informes_path,
                    status_callback=self._update_row_status,
                )
                self._ejecutar_en_hilo(coro)

            def _on_cancelado():
                self._log("Proceso SUGO cancelado por el usuario.", warning=True)
                self._on_proceso_terminado()

            DialogLogin(self, callback_ok=_on_credenciales_ok, callback_cancel=_on_cancelado)

        self._verificar_progreso_y_ejecutar(_iniciar_sugo)

    # ==========================================
    # CALLBACKS DE SELECCIÓN DE ENTRADAS
    # ==========================================

    def on_excel_selected(self, path):
        self.excel_path = path
        self._log(f"Archivo Excel seleccionado: {path}")
        self.cargar_datos_excel()

    def on_folder_selected(self, path):
        self.informes_path = path
        self._log(f"Carpeta de informes seleccionada: {path}")

    def cargar_datos_excel(self):
        """Carga el Excel y lo muestra en el panel de grid."""
        if not self.excel_path:
            return
        
        try:
            col_status = "Status Asignacion"
            col_informe = "Status Informe"
            cols_necesarias = ["Folio Sugo", "Folio Wizard", "Tipo Respuesta", "Selfservice", "Dictamen Wizard", "Informe"]
            
            from pathlib import Path
            excel_path_obj = Path(self.excel_path)
            excel_name = excel_path_obj.stem
            progreso_file = excel_path_obj.parent / f"{excel_name}_resultados.csv"
            
            from app.core.bots import cargar_datos
            df = cargar_datos(
                columnas_requeridas=cols_necesarias,
                columna_status_asignacion=col_status,
                columna_status_informe=col_informe,
                excel_path=self.excel_path,
                progreso_file=str(progreso_file),
                log_callback=self._log
            )
            if df is not None:
                self.panel_grid.cargar_datos(df)
                self._log(f"Se cargaron {len(df)} registros en la tabla.", success=True)
            else:
                self.panel_grid.limpiar_tabla()
        except Exception as e:
            self._log(f"Error al cargar datos del Excel: {e}", error=True)
            self.panel_grid.limpiar_tabla()

    def _update_row_status(self, idx, status):
        """Actualiza el estatus de la fila en la tabla de forma segura en el hilo principal."""
        self.after(0, lambda: self.panel_grid.actualizar_estatus(idx, status))
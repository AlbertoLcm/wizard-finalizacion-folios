import customtkinter as ctk
from app.config import settings


class PanelControls(ctk.CTkFrame):
    def __init__(self, master, image_logo, icon_off, cmd_login, cmd_wizard, cmd_sugo, cmd_exit, cmd_excel_selected, cmd_folder_selected):
        super().__init__(master, fg_color=settings.COLOR_WHITE, corner_radius=15, border_width=0)

        self.cmd_excel_selected = cmd_excel_selected
        self.cmd_folder_selected = cmd_folder_selected

        self.lbl_imagen_robot = ctk.CTkLabel(
            self, 
            text="", 
            image=image_logo,
        )
        self.lbl_imagen_robot.pack(pady=(20, 5), padx=35, anchor="w")

        self.lbl_title = ctk.CTkLabel(
            self, text="Bot Wizard", 
            font=ctk.CTkFont(family="Roboto", size=30, weight="bold"),
            text_color=settings.COLOR_ELECTRIC
        )
        self.lbl_title.pack(pady=(5, 0), padx=35, anchor="w")

        self.lbl_sub = ctk.CTkLabel(
            self, text='Operaciones "Especiales"', 
            font=ctk.CTkFont(family="Roboto", size=14),
            text_color=settings.COLOR_TEXT_MUTED
        )
        self.lbl_sub.pack(pady=(0, 2), padx=35, anchor="w")

        self.linea_cian_izq = ctk.CTkFrame(self, width=35, height=3, fg_color=settings.COLOR_CYAN, corner_radius=2)
        self.linea_cian_izq.pack(pady=(2, 10), padx=35, anchor="w")

        # ==========================================
        # --- SECCIÓN CONFIGURACIÓN DE ENTRADAS ---
        # ==========================================
        self.lbl_config_title = ctk.CTkLabel(
            self, text="Configuración de Entrada",
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=settings.COLOR_ELECTRIC
        )
        self.lbl_config_title.pack(pady=(5, 2), padx=35, anchor="w")
        
        # --- Selector de Excel ---
        self.frame_excel = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_excel.pack(fill="x", padx=35, pady=2)
        
        self.lbl_excel_title = ctk.CTkLabel(
            self.frame_excel, text="Archivo Excel (.xlsx):",
            font=ctk.CTkFont(size=11), text_color=settings.COLOR_TEXT_MUTED
        )
        self.lbl_excel_title.pack(anchor="w")
        
        self.frame_excel_input = ctk.CTkFrame(self.frame_excel, fg_color="transparent")
        self.frame_excel_input.pack(fill="x")
        
        self.entry_excel = ctk.CTkEntry(
            self.frame_excel_input, placeholder_text="Seleccione un archivo...",
            height=30, corner_radius=6, border_color="#CBD5E1", fg_color="#F8FAFC",
            font=ctk.CTkFont(size=11)
        )
        self.entry_excel.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.entry_excel.configure(state="readonly")
        
        self.btn_browse_excel = ctk.CTkButton(
            self.frame_excel_input, text="Examinar", width=70, height=30, corner_radius=6,
            fg_color="#F1F5F9", hover_color="#E2E8F0", text_color="#0F172A",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._on_browse_excel
        )
        self.btn_browse_excel.pack(side="right")
        
        # --- Selector de Carpeta de Informes ---
        self.frame_folder = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_folder.pack(fill="x", padx=35, pady=2)
        
        self.lbl_folder_title = ctk.CTkLabel(
            self.frame_folder, text="Carpeta de Informes (Opcional):",
            font=ctk.CTkFont(size=11), text_color=settings.COLOR_TEXT_MUTED
        )
        self.lbl_folder_title.pack(anchor="w")
        
        self.frame_folder_input = ctk.CTkFrame(self.frame_folder, fg_color="transparent")
        self.frame_folder_input.pack(fill="x")
        
        self.entry_folder = ctk.CTkEntry(
            self.frame_folder_input, placeholder_text="Seleccione una carpeta...",
            height=30, corner_radius=6, border_color="#CBD5E1", fg_color="#F8FAFC",
            font=ctk.CTkFont(size=11)
        )
        self.entry_folder.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.entry_folder.configure(state="readonly")
        
        self.btn_browse_folder = ctk.CTkButton(
            self.frame_folder_input, text="Examinar", width=70, height=30, corner_radius=6,
            fg_color="#F1F5F9", hover_color="#E2E8F0", text_color="#0F172A",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._on_browse_folder
        )
        self.btn_browse_folder.pack(side="right")
        
        self.linea_separadora = ctk.CTkFrame(self, height=1, fg_color="#E2E8F0")
        self.linea_separadora.pack(fill="x", padx=35, pady=(10, 8))

        # Botones de Acción usando los Callbacks recibidos por parámetro
        self.btn_1 = self.crear_boton("    1. Iniciar Sesión", cmd_login)
        self.btn_1.pack(pady=5, padx=35, fill="x")

        self.btn_2 = self.crear_boton("    2. Cierre Folio Wizard", cmd_wizard)
        self.btn_2.pack(pady=5, padx=35, fill="x")

        self.btn_3 = self.crear_boton("    3. Adjuntar Informe SUGO", cmd_sugo)
        self.btn_3.pack(pady=5, padx=35, fill="x")

        self.btn_exit = self.crear_boton_con_imagen("4. Salir", icon_off, cmd_exit, white=True)
        self.btn_exit.pack(pady=(8, 5), padx=35, fill="x")

        # ==========================================
        # --- OPCIÓN MODO OCULTO (HEADLESS RPA) ---
        # ==========================================
        self.frame_headless = ctk.CTkFrame(
            self,
            fg_color="#F0F4FF",
            corner_radius=10,
            border_width=1,
            border_color="#C5CCE8"
        )
        self.frame_headless.pack(fill="x", padx=35, pady=(4, 5))

        ctk.CTkLabel(
            self.frame_headless,
            text=" 🖥️  Modo Oculto (RPA)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=settings.COLOR_ELECTRIC
        ).pack(side="left", padx=(10, 4), pady=8)

        self._var_headless = ctk.BooleanVar(value=False)
        self.switch_headless = ctk.CTkSwitch(
            self.frame_headless,
            text="",
            variable=self._var_headless,
            onvalue=True,
            offvalue=False,
            width=40,
            progress_color=settings.COLOR_CYAN,
            button_color=settings.COLOR_ELECTRIC,
            button_hover_color=settings.COLOR_MIDNIGHT,
            command=self._on_headless_toggle
        )
        self.switch_headless.pack(side="right", padx=(4, 10), pady=8)

        self.lbl_headless_state = ctk.CTkLabel(
            self.frame_headless,
            text="Desactivado",
            font=ctk.CTkFont(size=10),
            text_color=settings.COLOR_TEXT_MUTED
        )
        self.lbl_headless_state.pack(side="right", padx=(0, 2), pady=8)

        # Espaciador para empujar el estado al fondo
        ctk.CTkFrame(self, fg_color="transparent").pack(expand=True, fill="both")

        # Estado (Caja verde claro)
        self.frame_status = ctk.CTkFrame(self, fg_color=settings.COLOR_STATUS_BG, corner_radius=10, height=40)
        self.frame_status.pack(side="bottom", fill="x", padx=35, pady=15)
        self.frame_status.pack_propagate(False)

        # Ícono Check
        self.lbl_check = ctk.CTkLabel(
            self.frame_status, text="✓", text_color="white", fg_color=settings.COLOR_GREEN,
            width=20, height=20, corner_radius=10, font=ctk.CTkFont(size=11, weight="bold")
        )
        self.lbl_check.pack(side="left", padx=(12, 8), pady=8)

        self.lbl_status = ctk.CTkLabel(
            self.frame_status, text="Estado: Listo", 
            text_color=settings.COLOR_GREEN, font=ctk.CTkFont(size=13, weight="bold")
        )
        self.lbl_status.pack(side="left", pady=8)

    # ==========================================
    # FILE DIALOG CALLBACKS
    # ==========================================
    def _on_browse_excel(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Seleccionar archivo Excel",
            filetypes=[("Archivos de Excel", ("*.xlsx", "*.xls", "*.csv"))] 
        )
        if path:
            self.set_excel_path(path)
            if self.cmd_excel_selected:
                self.cmd_excel_selected(path)

    def _on_browse_folder(self):
        from tkinter import filedialog
        path = filedialog.askdirectory(
            title="Seleccionar carpeta de Informes"
        )
        if path:
            self.set_folder_path(path)
            if self.cmd_folder_selected:
                self.cmd_folder_selected(path)

    def set_excel_path(self, path):
        self.entry_excel.configure(state="normal")
        self.entry_excel.delete(0, "end")
        self.entry_excel.insert(0, path)
        self.entry_excel.configure(state="readonly")

    def set_folder_path(self, path):
        self.entry_folder.configure(state="normal")
        self.entry_folder.delete(0, "end")
        self.entry_folder.insert(0, path)
        self.entry_folder.configure(state="readonly")

    # ==========================================
    # TOGGLE HEADLESS
    # ==========================================
    def _on_headless_toggle(self):
        activo = self._var_headless.get()
        if activo:
            self.lbl_headless_state.configure(
                text="Activado", text_color=settings.COLOR_ELECTRIC
            )
            self.frame_headless.configure(
                fg_color="#DDE6FF", border_color=settings.COLOR_ELECTRIC
            )
        else:
            self.lbl_headless_state.configure(
                text="Desactivado", text_color=settings.COLOR_TEXT_MUTED
            )
            self.frame_headless.configure(
                fg_color="#F0F4FF", border_color="#C5CCE8"
            )

    def get_modo_oculto(self) -> bool:
        """Devuelve True si el RPA debe ejecutarse en modo headless (sin ventana)."""
        return self._var_headless.get()

    # ==========================================
    # UTILIDADES TRASLADADAS A ESTA CLASE
    # ==========================================
    def crear_boton(self, texto, comando):
        return ctk.CTkButton(
            self, text=texto, command=comando, 
            height=40, corner_radius=10,
            fg_color=settings.COLOR_ELECTRIC, text_color="white",
            font=ctk.CTkFont(size=13, weight="bold"),
            hover_color=settings.COLOR_MIDNIGHT,
            anchor="w"
        )
    
    def crear_boton_con_imagen(self, texto, imagen, comando, white=False):
        return ctk.CTkButton(
            self, 
            text=f"  {texto}",
            image=imagen,
            compound="left",
            command=comando, 
            height=40, 
            corner_radius=10,
            border_color="#334070" if not white else "#CCCCCC",
            border_width=1 if white else 0,
            fg_color=settings.COLOR_ELECTRIC if not white else "white",
            text_color="white" if not white else "black",
            font=ctk.CTkFont(size=13, weight="bold"),
            hover_color="#15337A" if not white else "#E0E0E0",
            anchor="w"
        )

    def cambiar_estado(self, msg, color=settings.COLOR_GREEN, is_processing=False):
        self.lbl_status.configure(text=f"Estado: {msg}", text_color=color)
        if is_processing:
            self.lbl_check.configure(text="●", fg_color="transparent", text_color=color)
        else:
            self.lbl_check.configure(text="✓", fg_color=color, text_color="white")

    def bloquear_ui(self, bloquear):
        estado = "disabled" if bloquear else "normal"
        self.btn_1.configure(state=estado)
        self.btn_2.configure(state=estado)
        self.btn_3.configure(state=estado)
        self.btn_exit.configure(state=estado)
        self.switch_headless.configure(state=estado)
        self.btn_browse_excel.configure(state=estado)
        self.btn_browse_folder.configure(state=estado)
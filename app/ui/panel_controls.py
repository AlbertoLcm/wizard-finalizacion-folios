import customtkinter as ctk
from app.config import settings


class PanelControls(ctk.CTkFrame):
    def __init__(self, master, image_logo, icon_off, cmd_login, cmd_wizard, cmd_sugo, cmd_exit):
        super().__init__(master, fg_color=settings.COLOR_WHITE, corner_radius=15, border_width=0)

        self.lbl_imagen_robot = ctk.CTkLabel(
            self, 
            text="", 
            image=image_logo,
        )
        self.lbl_imagen_robot.pack(pady=(25, 10), padx=35, anchor="w")

        self.lbl_title = ctk.CTkLabel(
            self, text="Bot Wizard", 
            font=ctk.CTkFont(family="Roboto", size=34, weight="bold"),
            text_color=settings.COLOR_ELECTRIC
        )
        self.lbl_title.pack(pady=(10, 0), padx=35, anchor="w")

        self.lbl_sub = ctk.CTkLabel(
            self, text='Operaciones "Especiales"', 
            font=ctk.CTkFont(family="Roboto", size=16),
            text_color=settings.COLOR_TEXT_MUTED
        )
        self.lbl_sub.pack(pady=(0, 5), padx=35, anchor="w")

        self.linea_cian_izq = ctk.CTkFrame(self, width=35, height=3, fg_color=settings.COLOR_CYAN, corner_radius=2)
        self.linea_cian_izq.pack(pady=(5, 20), padx=35, anchor="w")

        # Botones de Acción usando los Callbacks recibidos por parámetro
        self.btn_1 = self.crear_boton("    1. Iniciar Sesión                                    >", cmd_login)
        self.btn_1.pack(pady=8, padx=35, fill="x")

        self.btn_2 = self.crear_boton("    2. Cierre Folio Wizard                        >", cmd_wizard)
        self.btn_2.pack(pady=8, padx=35, fill="x")

        self.btn_3 = self.crear_boton("    3. Adjuntar Informe SUGO                >", cmd_sugo)
        self.btn_3.pack(pady=8, padx=35, fill="x")

        self.btn_exit = self.crear_boton_con_imagen("4. Salir", icon_off, cmd_exit, white=True)
        self.btn_exit.pack(pady=(12, 8), padx=35, fill="x")

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
        self.frame_headless.pack(fill="x", padx=35, pady=(4, 8))

        ctk.CTkLabel(
            self.frame_headless,
            text="🖥️  Modo Oculto (RPA)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=settings.COLOR_ELECTRIC
        ).pack(side="left", padx=(14, 6), pady=10)

        self._var_headless = ctk.BooleanVar(value=False)
        self.switch_headless = ctk.CTkSwitch(
            self.frame_headless,
            text="",
            variable=self._var_headless,
            onvalue=True,
            offvalue=False,
            width=44,
            progress_color=settings.COLOR_CYAN,
            button_color=settings.COLOR_ELECTRIC,
            button_hover_color=settings.COLOR_MIDNIGHT,
            command=self._on_headless_toggle
        )
        self.switch_headless.pack(side="right", padx=(6, 14), pady=10)

        self.lbl_headless_state = ctk.CTkLabel(
            self.frame_headless,
            text="Desactivado",
            font=ctk.CTkFont(size=11),
            text_color=settings.COLOR_TEXT_MUTED
        )
        self.lbl_headless_state.pack(side="right", padx=(0, 4), pady=10)

        # Espaciador para empujar el estado al fondo
        ctk.CTkFrame(self, fg_color="transparent").pack(expand=True, fill="both")

        # Estado (Caja verde claro)
        self.frame_status = ctk.CTkFrame(self, fg_color=settings.COLOR_STATUS_BG, corner_radius=10, height=45)
        self.frame_status.pack(side="bottom", fill="x", padx=35, pady=25)
        self.frame_status.pack_propagate(False)

        # Ícono Check
        self.lbl_check = ctk.CTkLabel(
            self.frame_status, text="✓", text_color="white", fg_color=settings.COLOR_GREEN,
            width=22, height=22, corner_radius=11, font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_check.pack(side="left", padx=(15, 10), pady=10)

        self.lbl_status = ctk.CTkLabel(
            self.frame_status, text="Estado: Listo", 
            text_color=settings.COLOR_GREEN, font=ctk.CTkFont(size=14, weight="bold")
        )
        self.lbl_status.pack(side="left", pady=10)

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
            height=45, corner_radius=10,
            fg_color=settings.COLOR_ELECTRIC, text_color="white",
            font=ctk.CTkFont(size=14, weight="bold"),
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
            height=45, 
            corner_radius=10,
            border_color="#334070" if not white else "#CCCCCC",
            border_width=1 if white else 0,
            fg_color=settings.COLOR_ELECTRIC if not white else "white",
            text_color="white" if not white else "black",
            font=ctk.CTkFont(size=14, weight="bold"),
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
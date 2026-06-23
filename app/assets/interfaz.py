import asyncio
import datetime
import threading
from PIL import Image
import customtkinter as ctk

# ==========================================
# CONFIGURACIÓN DE COLORES (Ajustados a la imagen)
# ==========================================
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

# ==========================================
# LÓGICA DE LOS BOTS (Simulación)
# ==========================================
async def autenticar_google(log_func):
    log_func("Iniciando conexión con Google API...")
    await asyncio.sleep(2)
    log_func("Autenticación exitosa. Token guardado.", success=True)

async def orchestrator(tipo, log_func):
    log_func(f"Iniciando proceso de {tipo}...")
    await asyncio.sleep(3)
    log_func(f"Proceso {tipo.upper()} completado con éxito.", success=True)

# ==========================================
# INTERFAZ GRÁFICA PROFESIONAL
# ==========================================
class BotWizardApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        img_bbva = ctk.CTkImage(Image.open("assets/bbva-blue.png"), size=(85, 26))
        img_bbva_white = ctk.CTkImage(Image.open("assets/bbva-white.png"), size=(53, 16))
        icon_security = ctk.CTkImage(Image.open("assets/security-token-white.png"), size=(18, 18))
        icon_trash = ctk.CTkImage(Image.open("assets/trash-white.png"), size=(18, 18))
        icon_off = ctk.CTkImage(Image.open("assets/on-off.png"), size=(18, 18))

        # Configuración básica
        self.title("Bot Wizard - Panel de Control")
        self.geometry("1000x650")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_SAND)

        # Layout Principal: 2 Columnas y 2 Filas (Para la barra inferior)
        self.grid_columnconfigure(0, weight=4, minsize=400)
        self.grid_columnconfigure(1, weight=6, minsize=600)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # ==========================================
        self.panel_izq = ctk.CTkFrame(self, fg_color=COLOR_WHITE, corner_radius=15, border_width=0)
        # --- PANEL IZQUIERDO (CONTROLES) ---
        # ==========================================
        self.panel_izq.grid(row=0, column=0, padx=(20, 10), pady=(20, 20), sticky="nsew")

        # Logo / Marca Superior
        self.lbl_imagen_robot = ctk.CTkLabel(
            self.panel_izq, 
            text="", 
            image=img_bbva,
          )
        self.lbl_imagen_robot.pack(pady=(25, 10), padx=35, anchor="w")

        # Títulos
        self.lbl_title = ctk.CTkLabel(
            self.panel_izq, text="Bot Wizard", 
            font=ctk.CTkFont(family="Roboto", size=34, weight="bold"),
            text_color=COLOR_ELECTRIC
        )
        self.lbl_title.pack(pady=(10, 0), padx=35, anchor="w")

        self.lbl_sub = ctk.CTkLabel(
            self.panel_izq, text="Operaciones Especiales", 
            font=ctk.CTkFont(family="Roboto", size=16),
            text_color=COLOR_TEXT_MUTED
        )
        self.lbl_sub.pack(pady=(0, 5), padx=35, anchor="w")

        # Línea decorativa cian bajo el título
        self.linea_cian_izq = ctk.CTkFrame(self.panel_izq, width=35, height=3, fg_color=COLOR_CYAN, corner_radius=2)
        self.linea_cian_izq.pack(pady=(5, 30), padx=35, anchor="w")

        # Botones de Acción (Se usan espacios para separar el ícono, el texto y la flecha)
        self.btn_1 = self.crear_boton("    1. Iniciar Sesión                                    >", self.cmd_login)
        self.btn_1.pack(pady=8, padx=35, fill="x")

        self.btn_2 = self.crear_boton("    2. Cierre Folio Wizard                        >", self.cmd_wizard)
        self.btn_2.pack(pady=8, padx=35, fill="x")

        self.btn_3 = self.crear_boton("    3. Adjuntar Informe SUGO                >", self.cmd_sugo)
        self.btn_3.pack(pady=8, padx=35, fill="x")

        self.btn_exit = self.crear_boton_con_imagen("4. Salir", icon_off, self.destroy, white=True)
        self.btn_exit.pack(pady=(20, 10), padx=35, fill="x")

        # Espaciador para empujar el estado al fondo
        ctk.CTkFrame(self.panel_izq, fg_color="transparent").pack(expand=True, fill="both")

        # Estado (Caja verde claro)
        self.frame_status = ctk.CTkFrame(self.panel_izq, fg_color=COLOR_STATUS_BG, corner_radius=10, height=45)
        self.frame_status.pack(side="bottom", fill="x", padx=35, pady=25)
        self.frame_status.pack_propagate(False)

        # Ícono Check
        self.lbl_check = ctk.CTkLabel(
            self.frame_status, text="✓", text_color="white", fg_color=COLOR_GREEN,
            width=22, height=22, corner_radius=11, font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_check.pack(side="left", padx=(15, 10), pady=10)

        self.lbl_status = ctk.CTkLabel(
            self.frame_status, text="Estado: Listo", 
            text_color=COLOR_GREEN, font=ctk.CTkFont(size=14, weight="bold")
        )
        self.lbl_status.pack(side="left", pady=10)

        # ==========================================
        # --- PANEL DERECHO (LOGS) ---
        # ==========================================
        self.panel_der = ctk.CTkFrame(self, fg_color=COLOR_MIDNIGHT, corner_radius=15)
        self.panel_der.grid(row=0, column=1, padx=(10, 20), pady=(20, 20), sticky="nsew")

        # Cabecera Panel Derecho
        self.frame_log_header = ctk.CTkFrame(self.panel_der, fg_color="transparent")
        self.frame_log_header.pack(fill="x", padx=30, pady=(30, 15))

        self.lbl_log_title = ctk.CTkLabel(
            self.frame_log_header, text="Registro de Actividad", 
            font=ctk.CTkFont(family="Roboto", size=20, weight="bold"),
            text_color="white"
        )
        self.lbl_log_title.pack(side="left")

        # Botón Limpiar y línea decorativa
        self.btn_clear = ctk.CTkButton(
            self.frame_log_header, text="Limpiar", width=80, height=28,
            image=icon_trash, compound="left",
            fg_color="transparent", border_width=1, border_color="#334070",
            hover_color="#1A2859", text_color="#A2ADC0",
            command=self.limpiar_logs
        )
        self.btn_clear.pack(side="right", padx=(15, 0))

        self.linea_cian_der = ctk.CTkFrame(self.frame_log_header, width=30, height=3, fg_color=COLOR_CYAN, corner_radius=2)
        self.linea_cian_der.pack(side="right")

        # Terminal de Logs
        self.txt_logs = ctk.CTkTextbox(
            self.panel_der, 
            font=ctk.CTkFont(family="Courier New", size=13),
            fg_color="transparent",
            text_color="#C4CDD5",
            wrap="word"
        )
        self.txt_logs.pack(padx=25, pady=(0, 25), fill="both", expand=True)
        
        # Configuración de colores en el texto (Tags)
        self.txt_logs.tag_config("cyan_dot", foreground=COLOR_CYAN)
        self.txt_logs.tag_config("success", foreground=COLOR_GREEN)
        self.txt_logs.tag_config("timestamp", foreground="#7A8599")
        self.txt_logs.configure(state="disabled")

        # ==========================================
        # --- BARRA INFERIOR (BRANDING) ---
        # ==========================================
        self.panel_bottom = ctk.CTkFrame(self, fg_color=COLOR_DARK_BLUE, height=35, corner_radius=0)
        self.panel_bottom.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.panel_bottom.pack_propagate(False)

        self.lbl_brand_left = ctk.CTkLabel(
            self.panel_bottom, text="  Seguridad  ·  Confianza  ·  Innovación",
            image=icon_security, compound="left",
            font=ctk.CTkFont(size=12), text_color="#8997B5"
        )
        self.lbl_brand_left.pack(side="left", padx=20)

        self.lbl_brand_right = ctk.CTkLabel(
            self.panel_bottom, text="  Atención Autoridades  ", 
            image=img_bbva_white, compound="left",
            font=ctk.CTkFont(size=12), text_color="white"
        )
        self.lbl_brand_right.pack(side="right", padx=20)

        # Iniciar sistema visualmente
        self.log("Sistema Bot Wizard iniciado correctamente.")

    # ==========================================
    # UTILIDADES Y MÉTODOS DE LA UI
    # ==========================================
    def crear_boton(self, texto, comando):
        return ctk.CTkButton(
            self.panel_izq, text=texto, command=comando, 
            height=45, corner_radius=10,
            fg_color=COLOR_ELECTRIC, text_color="white",
            font=ctk.CTkFont(size=14, weight="bold"),
            hover_color=COLOR_MIDNIGHT,
            anchor="w"
        )
    
    def crear_boton_con_imagen(self, texto, imagen, comando, white = False):
        return ctk.CTkButton(
            self.panel_izq, 
            text=f"  {texto}",
            image=imagen,
            compound="left",
            command=comando, 
            height=45, 
            corner_radius=10,
            border_color="#334070" if not white else "#CCCCCC",
            border_width=1 if white else 0,
            fg_color=COLOR_ELECTRIC if not white else "white",
            text_color="white" if not white else "black",
            font=ctk.CTkFont(size=14, weight="bold"),
            hover_color="#15337A" if not white else "#E0E0E0",
            anchor="w"
        )

    def log(self, texto, success=False):
        hora = datetime.datetime.now().strftime("%H:%M:%S")
        self.txt_logs.configure(state="normal")
        
        # Insertar viñeta
        if success:
            self.txt_logs.insert("end", "  ✓ ", "success")
        else:
            self.txt_logs.insert("end", "  ● ", "cyan_dot")
            
        # Insertar hora y texto
        self.txt_logs.insert("end", f"[{hora}] ", "timestamp")
        if success:
            self.txt_logs.insert("end", f"{texto}\n", "success")
        else:
            self.txt_logs.insert("end", f"{texto}\n")
            
        self.txt_logs.configure(state="disabled")
        self.txt_logs.see("end")

    def limpiar_logs(self):
        self.txt_logs.configure(state="normal")
        self.txt_logs.delete("1.0", "end")
        self.txt_logs.configure(state="disabled")
        self.log("Registro limpiado.")

    def cambiar_estado(self, msg, color=COLOR_GREEN, is_processing=False):
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

    # ==========================================
    # GESTIÓN DE PROCESOS (THREADS)
    # ==========================================
    def run_task(self, coro):
        self.cambiar_estado("Procesando...", "#F59E0B", is_processing=True)
        self.bloquear_ui(True)

        def worker():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(coro)
            finally:
                self.after(0, lambda: self.cambiar_estado("Listo", COLOR_GREEN))
                self.after(0, lambda: self.bloquear_ui(False))

        threading.Thread(target=worker, daemon=True).start()

    # --- COMANDOS ---
    def cmd_login(self):
        self.run_task(autenticar_google(self.log))

    def cmd_wizard(self):
        self.run_task(orchestrator("wizard", self.log))

    def cmd_sugo(self):
        self.run_task(orchestrator("sugo", self.log))

if __name__ == "__main__":
    app = BotWizardApp()
    app.mainloop()
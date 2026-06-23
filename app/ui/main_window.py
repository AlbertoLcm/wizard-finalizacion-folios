import asyncio
import datetime
import threading

from PIL import Image
import customtkinter as ctk

from app.config import settings
from app.core.bots import autenticar_google, orchestrator

from app.ui.panel_logs import PanelLogs
from app.ui.panel_controls import PanelControls

import time


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
        self.geometry(settings.APP_GEOMETRY)
        self.resizable(False, False)
        self.configure(fg_color=settings.COLOR_SAND)

        # ==========================================
        # --- INTERFAZ ---
        # ==========================================

        self.grid_columnconfigure(0, weight=4, minsize=400)
        self.grid_columnconfigure(1, weight=6, minsize=600)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

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
        )
        self.panel_izq.grid(row=0, column=0, padx=(20, 10), pady=(20, 20), sticky="nsew")

        # ==========================================
        # --- PANEL DERECHO (LOGS) ---
        # ==========================================
        self.panel_logs = PanelLogs(self, icon_trash=self.icon_trash)
        self.panel_logs.grid(row=0, column=1, padx=(10, 20), pady=(20, 20), sticky="nsew")

        # ==========================================
        # --- BARRA INFERIOR (BRANDING) ---
        # ==========================================
        self.panel_bottom = ctk.CTkFrame(self, fg_color=settings.COLOR_DARK_BLUE, height=35, corner_radius=0)
        self.panel_bottom.grid(row=1, column=0, columnspan=2, sticky="nsew")
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

        self.panel_logs.agregar_log("Sistema Bot Wizard iniciado correctamente.", success=True)

    # ==========================================
    # EVENTOS DE LOS BOTONES (Actualizados)
    # ==========================================
    def cmd_login(self):
        self.panel_logs.agregar_log("Iniciando Login...", success=True)
        # TODO: Agregar lógica de autenticación aquí

    def cmd_wizard(self):
        self.panel_logs.agregar_log("Ejecutando Cierre Folio Wizard...")
        self.panel_izq.cambiar_estado("Ejecutando Wizard...", is_processing=True)
        # TODO: Agregar lógica de orchestrator aquí

    def cmd_sugo(self):
        self.panel_logs.agregar_log("Adjuntando Informe SUGO...")
        self.panel_izq.cambiar_estado("Adjuntando informe...", is_processing=True)
        # TODO: Agregar lógica del informe SUGO aquí
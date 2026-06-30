import customtkinter as ctk
from app.config import settings

class PanelGrid(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=settings.COLOR_WHITE, corner_radius=15, border_width=1, border_color="#E2E8F0", **kwargs)
        
        # --- Cabecera Panel ---
        self.frame_header = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_header.pack(fill="x", padx=25, pady=(20, 10))

        self.lbl_title = ctk.CTkLabel(
            self.frame_header, text="Registros Cargados (Excel)", 
            font=ctk.CTkFont(family="Roboto", size=18, weight="bold"),
            text_color=settings.COLOR_ELECTRIC
        )
        self.lbl_title.pack(side="left")

        # Contador de filas
        self.lbl_count = ctk.CTkLabel(
            self.frame_header, text="0 registros", 
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=settings.COLOR_TEXT_MUTED,
            fg_color="#F1F5F9",
            corner_radius=8,
            padx=10,
            pady=2
        )
        self.lbl_count.pack(side="left", padx=15)

        self.linea_decorativa = ctk.CTkFrame(self, height=1, fg_color="#E2E8F0")
        self.linea_decorativa.pack(fill="x", padx=25, pady=(0, 10))

        # --- Encabezados de la Tabla ---
        self.frame_table_headers = ctk.CTkFrame(self, fg_color="#F8FAFC", height=35, corner_radius=6)
        self.frame_table_headers.pack(fill="x", padx=25, pady=(0, 5))
        self.frame_table_headers.pack_propagate(False)

        # Configurar columnas
        self.column_weights = [1.5, 1.5, 3.0, 2.0, 2.0]  # Folio Sugo, Folio Wizard, Tipo Respuesta, Informe, Estatus
        self.column_titles = ["Folio Sugo", "Folio Wizard", "Tipo Respuesta", "Informe", "Estatus"]

        for col_idx, (title, weight) in enumerate(zip(self.column_titles, self.column_weights)):
            self.frame_table_headers.grid_columnconfigure(col_idx, weight=int(weight * 10))
            
            lbl = ctk.CTkLabel(
                self.frame_table_headers, text=title,
                font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
                text_color="#475569",
                anchor="w"
            )
            lbl.grid(row=0, column=col_idx, padx=10, pady=5, sticky="ew")

        # --- Cuerpo de la Tabla (Scrollable) ---
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, 
            fg_color="transparent",
            scrollbar_button_color="#CBD5E1",
            scrollbar_button_hover_color="#94A3B8"
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        # Diccionario para guardar referencias de los widgets de status para actualización rápida
        # { index_fila: { 'status_lbl': CTkLabel, 'row_frame': CTkFrame } }
        self.row_widgets = {}

    def cargar_datos(self, df):
        """Limpia la tabla anterior y carga el DataFrame de pandas."""
        self.limpiar_tabla()

        if df is None or df.empty:
            self.lbl_count.configure(text="0 registros")
            return

        total_filas = len(df)
        self.lbl_count.configure(text=f"{total_filas} registros")

        # Determinar qué columna contiene el estatus
        col_status = "Status Asignacion" if "Status Asignacion" in df.columns else "Status SUGO"
        if col_status not in df.columns:
            # Si no está ninguno de los dos, buscar uno que contenga 'status' o 'estatus'
            status_cols = [c for c in df.columns if "status" in c.lower() or "estatus" in c.lower()]
            col_status = status_cols[0] if status_cols else None

        for idx, row in df.iterrows():
            # Color de fondo alterno para filas
            bg_color = settings.COLOR_WHITE if idx % 2 == 0 else "#F8FAFC"
            
            row_frame = ctk.CTkFrame(self.scroll_frame, fg_color=bg_color, height=40, corner_radius=6)
            row_frame.pack(fill="x", pady=2)
            row_frame.pack_propagate(False)

            # Configurar las columnas en el frame de la fila
            for col_idx, weight in enumerate(self.column_weights):
                row_frame.grid_columnconfigure(col_idx, weight=int(weight * 10))

            # Extraer valores
            val_sugo = str(row.get("Folio Sugo", "")).strip()
            val_wizard = str(row.get("Folio Wizard", "")).strip()
            val_tipo = str(row.get("Tipo Respuesta", "")).strip()
            val_informe = str(row.get("Informe", "")).strip()
            
            # Quitar .0 si pandas lo leyó como float
            if val_sugo.endswith(".0"): val_sugo = val_sugo[:-2]
            if val_wizard.endswith(".0"): val_wizard = val_wizard[:-2]

            # Estatus inicial
            val_status = str(row.get(col_status, "Pendiente")).strip() if col_status else "Pendiente"

            # Crear celdas de texto
            lbl_sugo = ctk.CTkLabel(row_frame, text=val_sugo, font=ctk.CTkFont(size=12), text_color="#1E293B", anchor="w")
            lbl_sugo.grid(row=0, column=0, padx=10, pady=8, sticky="ew")

            lbl_wizard = ctk.CTkLabel(row_frame, text=val_wizard, font=ctk.CTkFont(size=12), text_color="#1E293B", anchor="w")
            lbl_wizard.grid(row=0, column=1, padx=10, pady=8, sticky="ew")

            lbl_tipo = ctk.CTkLabel(row_frame, text=val_tipo, font=ctk.CTkFont(size=12), text_color="#1E293B", anchor="w")
            lbl_tipo.grid(row=0, column=2, padx=10, pady=8, sticky="ew")

            # Acortar nombre de informe si es muy largo
            display_informe = val_informe
            if len(display_informe) > 20:
                display_informe = display_informe[:17] + "..."
            lbl_informe = ctk.CTkLabel(row_frame, text=display_informe, font=ctk.CTkFont(size=12), text_color="#64748B", anchor="w")
            lbl_informe.grid(row=0, column=3, padx=10, pady=8, sticky="ew")

            # Celda de Estatus (Badge)
            lbl_status = ctk.CTkLabel(
                row_frame, 
                text=val_status, 
                font=ctk.CTkFont(size=11, weight="bold"),
                width=100,
                height=24,
                corner_radius=12
            )
            lbl_status.grid(row=0, column=4, padx=10, pady=8, sticky="w")
            
            # Aplicar colores de badge
            self._aplicar_estilo_badge(lbl_status, val_status)

            # Guardar referencia para actualizaciones en tiempo real
            self.row_widgets[idx] = {
                'status_lbl': lbl_status,
                'row_frame': row_frame
            }

    def actualizar_estatus(self, row_index, nuevo_estatus):
        """Actualiza el estatus de una fila específica y cambia los colores del badge en tiempo real."""
        if row_index in self.row_widgets:
            widgets = self.row_widgets[row_index]
            lbl = widgets['status_lbl']
            frame = widgets['row_frame']
            
            # Actualizar texto y color del badge
            lbl.configure(text=nuevo_estatus)
            self._aplicar_estilo_badge(lbl, nuevo_estatus)
            
            # Si está procesando, dar un fondo sutil a toda la fila
            if nuevo_estatus in ("Procesando", "Ejecutando"):
                frame.configure(fg_color="#EFF6FF") # Light blue tint
            elif nuevo_estatus in ("Completado", "OK"):
                frame.configure(fg_color="#F0FDF4") # Light green tint
            elif nuevo_estatus == "Error":
                frame.configure(fg_color="#FEF2F2") # Light red tint
            else:
                # Restaurar color normal
                bg_color = settings.COLOR_WHITE if row_index % 2 == 0 else "#F8FAFC"
                frame.configure(fg_color=bg_color)
                
            # Hacer scroll para ver la fila activa
            self.scroll_frame._parent_canvas.yview_moveto(row_index / len(self.row_widgets))

    def _aplicar_estilo_badge(self, label, status):
        """Aplica estilos CSS-like (Tailwind) al badge de estatus según su valor."""
        status_lower = status.lower()
        
        if "pendiente" in status_lower:
            label.configure(fg_color="#E2E8F0", text_color="#475569")  # Slate Gray
        elif "procesando" in status_lower or "ejecutando" in status_lower:
            label.configure(fg_color="#DBEAFE", text_color="#1D4ED8")  # Blue
        elif "completado" in status_lower or status_lower == "ok":
            label.configure(fg_color="#D1FAE5", text_color="#065F46")  # Green
        elif "error" in status_lower:
            label.configure(fg_color="#FEE2E2", text_color="#991B1B")  # Red
        elif "no encontrado" in status_lower or "omitido" in status_lower:
            label.configure(fg_color="#FEF3C7", text_color="#92400E")  # Amber / Orange
        else:
            label.configure(fg_color="#F1F5F9", text_color="#475569")  # Neutral Gray

    def limpiar_tabla(self):
        """Elimina todas las filas de la tabla."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.row_widgets.clear()

import customtkinter as ctk
from tkinter import ttk
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

        # --- Estadísticas (Stats) ---
        self.frame_stats = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_stats.pack(fill="x", padx=25, pady=(0, 15))
        
        # Configurar 4 columnas uniformes para las tarjetas
        for c in range(4):
            self.frame_stats.grid_columnconfigure(c, weight=1, uniform="stat_cols")
            
        # Crear las tarjetas de estadísticas
        self.card_total = self._crear_stat_card(self.frame_stats, 0, "Total", "0", "#64748B", "#F1F5F9")
        self.card_pendientes = self._crear_stat_card(self.frame_stats, 1, "Pendientes", "0", "#475569", "#F8FAFC")
        self.card_procesados = self._crear_stat_card(self.frame_stats, 2, "Procesados", "0", "#065F46", "#F0FDF4")
        self.card_errores = self._crear_stat_card(self.frame_stats, 3, "Con Error", "0", "#991B1B", "#FEF2F2")

        # --- Contenedor de la Tabla ---
        self.frame_table = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        self.frame_table.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        # Configuración de estilos ttk para Treeview
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Configurar colores y diseño general para mimetizar la interfaz
        self.style.configure(
            "Custom.Treeview",
            background=settings.COLOR_WHITE,
            foreground="#1E293B",
            rowheight=35,
            fieldbackground=settings.COLOR_WHITE,
            font=("Roboto", 11),
            border_width=0
        )

        self.style.configure(
            "Custom.Treeview.Heading",
            background="#F8FAFC",
            foreground="#475569",
            font=("Roboto", 11, "bold"),
            relief="flat"
        )
        
        self.style.map(
            "Custom.Treeview.Heading",
            background=[("active", "#E2E8F0")],
            foreground=[("active", "#0F172A")]
        )

        self.style.map(
            "Custom.Treeview",
            background=[("selected", "#EFF6FF")],
            foreground=[("selected", "#1D4ED8")]
        )

        # Crear Treeview
        self.column_ids = ("folio_sugo", "folio_wizard", "tipo_respuesta", "informe", "estatus")
        self.tree = ttk.Treeview(
            self.frame_table,
            columns=self.column_ids,
            show="headings",
            style="Custom.Treeview",
            selectmode="browse"
        )

        # Scrollbar responsiva (CustomTkinter)
        self.scrollbar = ctk.CTkScrollbar(self.frame_table, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y", padx=(5, 0))

        # Configuración de columnas
        column_configs = {
            "folio_sugo": {"text": "Folio Sugo", "width": 110, "anchor": "w"},
            "folio_wizard": {"text": "Folio Wizard", "width": 110, "anchor": "w"},
            "tipo_respuesta": {"text": "Tipo Respuesta", "width": 250, "anchor": "w"},
            "informe": {"text": "Informe", "width": 200, "anchor": "w"},
            "estatus": {"text": "Estatus", "width": 120, "anchor": "center"}
        }

        for col_id, config in column_configs.items():
            self.tree.heading(col_id, text=config["text"], anchor=config["anchor"])
            self.tree.column(col_id, width=config["width"], minwidth=50, anchor=config["anchor"], stretch=True)

        # Configurar tags de filas para estatus coloreados
        self.tree.tag_configure("evenrow", background=settings.COLOR_WHITE)
        self.tree.tag_configure("oddrow", background="#F8FAFC")
        self.tree.tag_configure("status_pendiente", foreground="#475569", background=settings.COLOR_WHITE)
        self.tree.tag_configure("status_procesando", foreground="#1D4ED8", background="#EFF6FF")
        self.tree.tag_configure("status_completado", foreground="#065F46", background="#F0FDF4")
        self.tree.tag_configure("status_error", foreground="#991B1B", background="#FEF2F2")
        self.tree.tag_configure("status_warning", foreground="#92400E", background="#FEF3C7")

        # Mapeo de índices de fila a ID del item del Treeview
        self.row_items = {}

    def _crear_stat_card(self, parent, column, title, val, text_color, bg_color):
        """Helper para construir una tarjeta visual de métricas sin emojis."""
        card = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=10, border_width=1, border_color="#E2E8F0")
        card.grid(row=0, column=column, padx=5, sticky="nsew")
        
        lbl_title = ctk.CTkLabel(
            card, text=title,
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            text_color="#64748B"
        )
        lbl_title.pack(anchor="w", padx=12, pady=(8, 2))
        
        lbl_val = ctk.CTkLabel(
            card, text=val,
            font=ctk.CTkFont(family="Roboto", size=20, weight="bold"),
            text_color=text_color
        )
        lbl_val.pack(anchor="w", padx=12, pady=(0, 8))
        
        return lbl_val

    def recalcular_estadisticas(self):
        """Calcula el total de filas, pendientes, procesados y errores, y actualiza las tarjetas."""
        total = 0
        pendientes = 0
        procesados = 0
        errores = 0
        
        for item in self.tree.get_children():
            total += 1
            valores = self.tree.item(item, "values")
            if len(valores) > 4:
                status = str(valores[4]).lower()
                if "pendiente" in status:
                    pendientes += 1
                elif "error" in status:
                    errores += 1
                else:
                    procesados += 1
                    
        self.card_total.configure(text=str(total))
        self.card_pendientes.configure(text=str(pendientes))
        self.card_procesados.configure(text=str(procesados))
        self.card_errores.configure(text=str(errores))

    def cargar_datos(self, df, col_status: str = None):
        """Limpia la tabla anterior y carga el DataFrame de pandas.
        
        Args:
            df:         DataFrame con los datos a mostrar.
            col_status: nombre exacto de la columna de estado a mostrar en la
                        columna "Estatus" del grid. Si se omite, se infiere
                        buscando columnas que contengan 'status' o 'estatus'.
        """
        self.limpiar_tabla()

        if df is None or df.empty:
            self.lbl_count.configure(text="0 registros")
            self.recalcular_estadisticas()
            return

        total_filas = len(df)
        self.lbl_count.configure(text=f"{total_filas} registros")

        # Resolver columna de estatus
        if col_status and col_status in df.columns:
            col_status_real = col_status
        else:
            # Fallback: buscar cualquier columna que parezca de estatus
            status_cols = [
                c for c in df.columns
                if "status" in c.lower() or "estatus" in c.lower()
            ]
            col_status_real = status_cols[0] if status_cols else None

        for idx, row in df.iterrows():
            val_sugo = str(row.get("Folio Sugo", "")).strip()
            val_wizard = str(row.get("Folio Wizard", "")).strip()
            val_tipo = str(row.get("Tipo Respuesta", "")).strip()
            val_informe = str(row.get("Informe", "")).strip()
            val_status = str(row.get(col_status_real, "Pendiente")).strip() if col_status_real else "Pendiente"

            if val_sugo.endswith(".0"): val_sugo = val_sugo[:-2]
            if val_wizard.endswith(".0"): val_wizard = val_wizard[:-2]

            # Insertar registro en el Treeview
            item_id = self.tree.insert(
                "",
                "end",
                values=(val_sugo, val_wizard, val_tipo, val_informe, val_status)
            )

            # Guardar referencia
            self.row_items[idx] = item_id

            # Aplicar estilo de fila según estatus inicial
            self._aplicar_estilo_fila(item_id, idx, val_status)
            
        self.recalcular_estadisticas()

    def actualizar_estatus(self, row_index, nuevo_estatus):
        """Actualiza el estatus de una fila específica en tiempo real."""
        if row_index in self.row_items:
            item_id = self.row_items[row_index]
            
            # Obtener valores actuales y actualizar la columna estatus (índice 4)
            valores = list(self.tree.item(item_id, "values"))
            valores[4] = nuevo_estatus
            self.tree.item(item_id, values=valores)
            
            # Re-aplicar estilo
            self._aplicar_estilo_fila(item_id, row_index, nuevo_estatus)
            
            # Auto-scroll para que el elemento sea visible
            self.tree.see(item_id)
            
            # Seleccionar la fila activa
            self.tree.selection_set(item_id)
            
            # Actualizar tarjetas de estadísticas
            self.recalcular_estadisticas()

    def _aplicar_estilo_fila(self, item_id, row_index, status):
        """Asigna los tags de estilo correspondientes según el estatus del folio."""
        status_lower = status.lower()
        
        if "pendiente" in status_lower:
            tag = "status_pendiente"
        elif "procesando" in status_lower or "ejecutando" in status_lower:
            tag = "status_procesando"
        elif "completado" in status_lower or status_lower == "ok":
            tag = "status_completado"
        elif "error" in status_lower:
            tag = "status_error"
        elif "no encontrado" in status_lower or "omitido" in status_lower:
            tag = "status_warning"
        else:
            tag = "evenrow" if row_index % 2 == 0 else "oddrow"
            
        self.tree.item(item_id, tags=(tag,))

    def limpiar_tabla(self):
        """Elimina todas las filas de la tabla."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.row_items.clear()
        self.recalcular_estadisticas()

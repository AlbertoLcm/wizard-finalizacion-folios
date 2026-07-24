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

        self.lbl_count = ctk.CTkLabel(
            self.frame_header, text="0 registros",
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=settings.COLOR_TEXT_MUTED,
            fg_color="#F1F5F9", corner_radius=8, padx=10, pady=2
        )
        self.lbl_count.pack(side="left", padx=15)

        self.linea_decorativa = ctk.CTkFrame(self, height=1, fg_color="#E2E8F0")
        self.linea_decorativa.pack(fill="x", padx=25, pady=(0, 10))

        # --- Contenedor de la Tabla ---
        self.frame_table = ctk.CTkFrame(self, fg_color="transparent", border_width=0)
        self.frame_table.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        # Estilos ttk (se definen una sola vez)
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure(
            "Custom.Treeview",
            background=settings.COLOR_WHITE, foreground="#1E293B",
            rowheight=35, fieldbackground=settings.COLOR_WHITE,
            font=("Roboto", 11), border_width=0
        )
        self.style.configure(
            "Custom.Treeview.Heading",
            background="#F8FAFC", foreground="#475569",
            font=("Roboto", 11, "bold"), relief="flat"
        )
        self.style.map("Custom.Treeview.Heading",
            background=[("active", "#E2E8F0")], foreground=[("active", "#0F172A")])
        self.style.map("Custom.Treeview",
            background=[("selected", "#EFF6FF")], foreground=[("selected", "#1D4ED8")])

        # Estado interno
        self.tree            = None
        self.scrollbar_y     = None
        self.scrollbar_x     = None
        self.row_items       = {}   # idx pandas → item_id Treeview
        self._tree_cols      = []
        self.col_status_activa = None

        # Treeview vacío de arranque
        self._rebuild_tree(["Estatus Asignacion", "Estatus Wizard", "Estatus Informe"])

    # =========================================================
    # CONSTRUCCIÓN / RECONSTRUCCIÓN DEL TREEVIEW
    # =========================================================

    def _rebuild_tree(self, cols: list):
        """Destruye el Treeview existente y crea uno nuevo con las columnas dadas."""
        if self.tree:
            self.tree.destroy()
        if self.scrollbar_y:
            self.scrollbar_y.destroy()
        if self.scrollbar_x:
            self.scrollbar_x.destroy()

        self._tree_cols = list(cols)

        self.tree = ttk.Treeview(
            self.frame_table,
            columns=self._tree_cols,
            show="headings",
            style="Custom.Treeview",
            selectmode="browse"
        )

        # Scrollbars
        self.scrollbar_y = ctk.CTkScrollbar(
            self.frame_table, orientation="vertical", command=self.tree.yview
        )
        self.scrollbar_x = ctk.CTkScrollbar(
            self.frame_table, orientation="horizontal", command=self.tree.xview
        )
        self.tree.configure(
            yscrollcommand=self.scrollbar_y.set,
            xscrollcommand=self.scrollbar_x.set
        )

        # Layout: X abajo → Y derecha → Treeview ocupa el resto
        self.scrollbar_x.pack(side="bottom", fill="x", pady=(2, 0))
        self.scrollbar_y.pack(side="right",  fill="y", padx=(5, 0))
        self.tree.pack(side="left", fill="both", expand=True)

        # Configurar columnas
        for col in self._tree_cols:
            if col.startswith("Estatus"):
                self.tree.heading(col, text=col, anchor="center")
                self.tree.column(col, width=130, minwidth=90, anchor="center", stretch=False)
            else:
                w = self._ancho_columna(col)
                self.tree.heading(col, text=col, anchor="w")
                self.tree.column(col, width=w, minwidth=80, anchor="w", stretch=False)

        # Tags de estilo
        self.tree.tag_configure("evenrow",           background=settings.COLOR_WHITE)
        self.tree.tag_configure("oddrow",            background="#F8FAFC")
        self.tree.tag_configure("status_pendiente",  foreground="#475569", background=settings.COLOR_WHITE)
        self.tree.tag_configure("status_procesando", foreground="#1D4ED8", background="#EFF6FF")
        self.tree.tag_configure("status_completado", foreground="#065F46", background="#F0FDF4")
        self.tree.tag_configure("status_error",      foreground="#991B1B", background="#FEF2F2")
        self.tree.tag_configure("status_warning",    foreground="#92400E", background="#FEF3C7")

    @staticmethod
    def _ancho_columna(col: str) -> int:
        anchos = {
            "Folio Sugo": 110, "Folio Wizard": 120, "Tipo Respuesta": 220,
            "Selfservice": 130, "Dictamen Wizard": 220,
            "Informe": 200, "Fecha Cierre": 110,
        }
        return anchos.get(col, 140)

    # =========================================================
    # HELPERS
    # =========================================================

    def _tag_para_status(self, status: str, row_index: int) -> str:
        s = status.lower()
        if "pendiente" in s or s == "":
            return "status_pendiente"
        if "procesando" in s or "ejecutando" in s:
            return "status_procesando"
        if "completado" in s or s == "ok":
            return "status_completado"
        if "error" in s:
            return "status_error"
        if "no encontrado" in s or "omitido" in s or "faltante" in s:
            return "status_warning"
        return "evenrow" if row_index % 2 == 0 else "oddrow"

    # =========================================================
    # API PÚBLICA
    # =========================================================

    def set_col_status_activa(self, col_status: str):
        """Cambia la columna de status activa (llamado por main_window al iniciar un proceso)."""
        self.col_status_activa = col_status

    def cargar_datos(self, df, col_status: str = None):
        """Reconstruye la tabla con TODAS las columnas del DataFrame.

        Las columnas de Estatus se muestran al inicio.
        
        Args:
            df:         DataFrame con los datos.
            col_status: columna del DataFrame que representa el proceso activo.
        """
        self.col_status_activa = col_status or self.col_status_activa
        self.row_items.clear()

        if df is None or df.empty:
            self.lbl_count.configure(text="0 registros")
            self._rebuild_tree(["Estatus Asignacion", "Estatus Wizard", "Estatus Informe"])
            return

        # Organizar columnas: Los tres Estatus primero, luego el resto
        status_cols = ["Estatus Asignacion", "Estatus Wizard", "Estatus Informe"]
        # Make sure they actually exist in the df, though they should be initialized
        status_cols = [c for c in status_cols if c in df.columns] 
        data_cols = [c for c in df.columns if c not in status_cols]

        self._tree_cols = status_cols + data_cols

        # Reconstruir Treeview
        self._rebuild_tree(self._tree_cols)
        self.lbl_count.configure(text=f"{len(df)} registros")

        col_stat = self.col_status_activa
        if not col_stat or col_stat not in df.columns:
            if status_cols:
                col_stat = status_cols[0]

        for idx, row in df.iterrows():
            val_status = str(row.get(col_stat, "Pendiente")).strip() if col_stat else "Pendiente"

            data_vals = []
            for col in self._tree_cols:
                v = str(row.get(col, "")).strip()
                if v.endswith(".0"):
                    v = v[:-2]
                data_vals.append(v)

            item_id = self.tree.insert(
                "", "end",
                values=tuple(data_vals)
            )
            self.row_items[idx] = item_id
            self.tree.item(item_id, tags=(self._tag_para_status(val_status, idx),))

    def actualizar_estatus(self, row_index, nuevo_estatus, col_status: str = None):
        """Actualiza la columna de Estatus específica de una fila en tiempo real."""
        if row_index not in self.row_items:
            return

        item_id = self.row_items[row_index]
        valores = list(self.tree.item(item_id, "values"))

        col = col_status or self.col_status_activa
        if col in self._tree_cols:
            col_idx = self._tree_cols.index(col)
            # Asegurar que la lista de valores tiene la longitud suficiente
            while len(valores) <= col_idx:
                valores.append("")
                
            valores[col_idx] = nuevo_estatus
            self.tree.item(item_id, values=valores)
            
            # Solo cambiar el color si estamos actualizando la columna activa
            if col == self.col_status_activa:
                self.tree.item(item_id, tags=(self._tag_para_status(nuevo_estatus, row_index),))
                
            self.tree.see(item_id)
            self.tree.selection_set(item_id)

    def limpiar_tabla(self):
        """Elimina todas las filas de la tabla."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.row_items.clear()

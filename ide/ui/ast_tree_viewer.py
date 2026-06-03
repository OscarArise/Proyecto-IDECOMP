"""
ast_tree_viewer.py
------------------
Widget de Tkinter para visualizar el Árbol Sintáctico de forma colapsable.
"""

import tkinter as tk
from tkinter import ttk
import json
from typing import Optional, Dict, Any


class ASTTreeViewer:
    """
    Widget para visualizar un AST en forma de árbol colapsable.
    
    Utiliza Tkinter Treeview para permitir expandir/contraer nodos.
    """
    
    def __init__(self, parent: tk.Widget):
        """
        Inicializa el visualizador de árbol AST.
        
        parent: Widget padre (marco o ventana)
        """
        self.parent = parent
        self.tree = None
        self.item_count = 0
        self.current_ast_json = ""
        self._style_name = "AST.Treeview"
        self._create_widgets()
    
    def _create_widgets(self):
        """Crea los widgets de la interfaz."""
        # Crear un marco para el árbol
        self._configure_styles()
        try:
            self.parent.configure(bg="#15171c")
        except tk.TclError:
            pass

        header = tk.Frame(self.parent, bg="#15171c")
        header.pack(fill=tk.X, padx=10, pady=(10, 4))
        tk.Label(header, text="Árbol Sintáctico", bg="#15171c", fg="#f5f7fb",
                 font=("Segoe UI", 12, "bold"), anchor="w").pack(side=tk.LEFT)
        tk.Label(header, text="producciones y tokens", bg="#15171c", fg="#8f98aa",
                 font=("Segoe UI", 9), anchor="w", padx=10).pack(side=tk.LEFT)

        toolbar = tk.Frame(self.parent, bg="#15171c")
        toolbar.pack(fill=tk.X, padx=10, pady=(0, 8))
        self._make_button(toolbar, "Abrir en ventana", self.open_in_window).pack(side=tk.LEFT)
        self._make_button(toolbar, "Expandir", self.expand_all).pack(side=tk.LEFT, padx=(6, 0))
        self._make_button(toolbar, "Colapsar", self.collapse_all).pack(side=tk.LEFT, padx=(6, 0))

        legend = tk.Frame(toolbar, bg="#15171c")
        legend.pack(side=tk.RIGHT)
        self._make_legend(legend, "Producción", "#8ab4f8")
        self._make_legend(legend, "Token", "#c8d0df")
        self._make_legend(legend, "Control", "#f7c873")

        tree_frame = tk.Frame(self.parent, bg="#2b303a", bd=1, relief=tk.SOLID)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Crear scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        # Crear Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            height=25,
            style=self._style_name
        )
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configurar columnas
        self.tree.column("#0", width=620, minwidth=320, stretch=True)
        self.tree.heading("#0", text="Árbol Sintáctico")
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Vincular evento de doble clic para expandir/contraer
        self.tree.bind("<Double-1>", self._on_double_click)
        self._configure_tree_tags()

    def _make_button(self, parent: tk.Widget, text: str, command):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg="#232833",
            fg="#f5f7fb",
            activebackground="#303848",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=5,
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
        )

    def _make_legend(self, parent: tk.Widget, text: str, color: str):
        item = tk.Frame(parent, bg="#15171c")
        item.pack(side=tk.LEFT, padx=(10, 0))
        tk.Label(item, text="■", bg="#15171c", fg=color, font=("Segoe UI", 8)).pack(side=tk.LEFT)
        tk.Label(item, text=text, bg="#15171c", fg="#9aa3b5", font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=(3, 0))

    def _configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            self._style_name,
            background="#1b1f27",
            foreground="#d8dee9",
            fieldbackground="#1b1f27",
            borderwidth=0,
            rowheight=26,
            font=("Consolas", 10),
        )
        style.configure(
            f"{self._style_name}.Heading",
            background="#252b36",
            foreground="#f5f7fb",
            relief=tk.FLAT,
            font=("Segoe UI", 9, "bold"),
        )
        style.map(
            self._style_name,
            background=[("selected", "#315f9f")],
            foreground=[("selected", "#ffffff")],
        )

    def _configure_tree_tags(self):
        self.tree.tag_configure("root", foreground="#9cdcfe", font=("Consolas", 10, "bold"))
        self.tree.tag_configure("nonterminal", foreground="#8ab4f8", font=("Consolas", 10, "bold"))
        self.tree.tag_configure("terminal", foreground="#c8d0df")
        self.tree.tag_configure("declaracion", foreground="#b7e4a8")
        self.tree.tag_configure("control", foreground="#f7c873", font=("Consolas", 10, "bold"))
        self.tree.tag_configure("io", foreground="#7dd3fc")
        self.tree.tag_configure("expresion", foreground="#c9a7ff")
        self.tree.tag_configure("error", foreground="#ff8a8a", font=("Consolas", 10, "bold"))
    
    def load_ast_json(self, json_str: str):
        """
        Carga el AST desde una representación JSON.
        
        json_str: String JSON del AST
        """
        try:
            self.current_ast_json = json_str
            ast_dict = json.loads(json_str)
            self.clear()
            self.current_ast_json = json_str
            self.item_count = 0
            
            # Insertar el nodo raíz
            root_id = self._insert_node(ast_dict, "")
            
            # Expandir automáticamente
            self.expand_all()
            
            # Asegurar actualización visual
            self.tree.update()
            
        except json.JSONDecodeError as e:
            self.tree.insert("", "end", text=f"Error JSON: {str(e)[:80]}")
        except Exception as e:
            self.tree.insert("", "end", text=f"Error: {str(e)[:80]}")
    
    def _insert_node(self, node_dict: Dict[str, Any], parent: str) -> str:
        """
        Inserta un nodo y sus hijos recursivamente en el árbol.
        
        node_dict: Diccionario del nodo
        parent: ID del nodo padre
        
        Retorna: ID del nodo insertado
        """
        # Obtener etiqueta del nodo
        label = node_dict.get("label", node_dict.get("type", "Nodo"))
        
        # Agregar información adicional si está disponible
        if "valor" in node_dict:
            label = f"{label} ({node_dict['valor']})"
        elif "nombre" in node_dict:
            label = f"{label} ({node_dict['nombre']})"
        
        # Insertar nodo
        item_id = f"item_{self.item_count}"
        self.item_count += 1
        
        node_type = node_dict.get("type", "")
        tags = ()
        
        # Aplicar tags para estilo
        if "ERROR" in node_type:
            tags = ("error",)
        elif label == "PROGRAMA":
            tags = ("root",)
        elif node_type == "Token" or ":" in label:
            tags = ("terminal",)
        elif node_type in ("DeclaracionVariable", "Asignacion"):
            tags = ("declaracion",)
        elif node_type in ("Seleccion", "Iteracion", "Repeticion"):
            tags = ("control",)
        elif node_type in ("EntradaEstandar", "SalidaEstandar"):
            tags = ("io",)
        elif node_type.startswith("Expresion"):
            tags = ("expresion",)
        elif label.isupper():
            tags = ("nonterminal",)
        
        self.tree.insert(parent, "end", item_id, text=label, open=True, tags=tags)
        
        # Insertar hijos recursivamente
        children = node_dict.get("children", [])
        for child_dict in children:
            if child_dict is not None:
                self._insert_node(child_dict, item_id)
        
        return item_id
    
    def clear(self):
        """Limpia el árbol."""
        if self.tree:
            self.tree.delete(*self.tree.get_children())
        self.current_ast_json = ""
    
    def open_in_window(self):
        """Abre el árbol actual en una ventana grande para revisión."""
        top = tk.Toplevel(self.parent.winfo_toplevel())
        top.title("Árbol Sintáctico")
        top.geometry("1000x700")
        top.minsize(800, 500)
        viewer = ASTTreeViewer(top)
        if self.current_ast_json:
            viewer.load_ast_json(self.current_ast_json)
        else:
            viewer.tree.insert("", "end", text="Ejecuta el análisis sintáctico para cargar el árbol")
    
    def _on_double_click(self, event):
        """Maneja el doble clic para expandir/contraer nodos."""
        item = self.tree.selection()
        if item:
            item_id = item[0]
            is_open = self.tree.item(item_id, "open")
            self.tree.item(item_id, open=not is_open)
    
    def expand_all(self):
        """Expande todos los nodos."""
        # Obtener todos los nodos raíz
        root_items = self.tree.get_children("")
        self._expand_recursive(root_items)
    
    def collapse_all(self):
        """Colapsa todos los nodos."""
        self._collapse_recursive(self.tree.get_children())
    
    def _expand_recursive(self, items):
        """Expande recursivamente los nodos."""
        if not items:
            return
        for item in items:
            try:
                self.tree.item(item, open=True)
                children = self.tree.get_children(item)
                if children:
                    self._expand_recursive(children)
            except Exception:
                pass  # Ignorar errores en nodos específicos
    
    def _collapse_recursive(self, items):
        """Colapsa recursivamente los nodos."""
        for item in items:
            self.tree.item(item, open=False)
            children = self.tree.get_children(item)
            if children:
                self._collapse_recursive(children)
    
    def configure_styles(self):
        """Configura estilos para los tags."""
        style = ttk.Style()
        
        # Estilos para diferentes tipos de nodos
        style.configure("Treeview", font=("Courier", 9))
        
        # Colores personalizados (si es posible con el tema)
        try:
            # Para Tkinter en Windows, el soporte para colores es limitado
            # Estos estilos pueden no aplicarse según el tema
            style.configure("Treeview", foreground="black")
        except:
            pass

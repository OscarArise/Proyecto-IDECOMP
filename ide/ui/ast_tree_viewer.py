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
        self._create_widgets()
    
    def _create_widgets(self):
        """Crea los widgets de la interfaz."""
        # Crear un marco para el árbol
        tree_frame = ttk.Frame(self.parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Crear scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        # Crear Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            height=25
        )
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configurar columnas
        self.tree.column("#0", width=400)
        self.tree.heading("#0", text="Árbol Sintáctico")
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Vincular evento de doble clic para expandir/contraer
        self.tree.bind("<Double-1>", self._on_double_click)
    
    def load_ast_json(self, json_str: str):
        """
        Carga el AST desde una representación JSON.
        
        json_str: String JSON del AST
        """
        try:
            ast_dict = json.loads(json_str)
            self.clear()
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
        elif node_type in ("DeclaracionVariable", "Asignacion"):
            tags = ("declaracion",)
        elif node_type in ("Seleccion", "Iteracion", "Repeticion"):
            tags = ("control",)
        elif node_type in ("EntradaEstandar", "SalidaEstandar"):
            tags = ("io",)
        elif node_type.startswith("Expresion"):
            tags = ("expresion",)
        
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

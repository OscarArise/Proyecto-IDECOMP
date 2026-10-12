import tkinter as tk
from tkinter import ttk
from .ast_tree_viewer import ASTTreeViewer

class Panels:
    #Organizacion de paneles del ide
    def __init__(self, root):
        self.root = root
        self._build_layout()

    def _build_layout(self):
        #Mapa text_widget -> frame para navegación robusta de pestañas
        self._tab_frames: dict = {}

        #Contenedor principal para la division del editor y resultados
        self.outer_pane = tk.PanedWindow(self.root, orient=tk.VERTICAL, sashrelief=tk.RAISED)
        self.outer_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5,0))

        #Contenedor superior editor izquierda /resultados derecha
        self.main_pane = tk.PanedWindow(self.outer_pane, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.outer_pane.add(self.main_pane, minsize = 200)

        #Panel del editor
        self.editor_frame = tk.Frame(self.main_pane, bg="white")
        self.main_pane.add(self.editor_frame, minsize = 200)

        #Panel de resultados
        self.right_frame = tk.Frame(self.main_pane, bg="#1e1e1e")
        self.main_pane.add(self.right_frame, minsize = 100)
        self._build_results_panel()

        #Panel Inferior Errores y ejecucion
        self.bottom_frame = tk.Frame(self.outer_pane, bg="#1e1e1e")
        self.outer_pane.add(self.bottom_frame, minsize = 80)
        self._build_bottom_panel()

        #Ajuste de proporciones
        self.root.after(100, self._adjust_proportions)

        #Calcular las redimensiones
        self.root.bind("<Configure>", self._on_resize)

    def _on_resize(self, event=None):
        if event and event.widget == self.root:
            self._adjust_proportions()

    def _adjust_proportions(self):
        self.root.update_idletasks()

        #Proporciones Verticales
        total_height = self.outer_pane.winfo_height()
        self.outer_pane.sash_place(0, 0, int(total_height * 0.70))
        #Proporciones horizontales
        total_width = self.main_pane.winfo_width()
        self.main_pane.sash_place(0, int(total_width * 0.60), 0)

    #Panel derecho "Resultados"
    def _build_results_panel(self):
        label = tk.Label(self.right_frame, text="Resultados", bg="#2d2d2d", fg="white", font=("Segoe UI", 9, "bold"), anchor="w", padx=5)
        label.pack(fill=tk.X)

        self.results_notebook = ttk.Notebook(self.right_frame)
        self.results_notebook.pack(fill=tk.BOTH, expand=True)

        #Pestañas de resultados
        self.tab_lexico = self._make_result_tab("Lexico")
        
        # Pestaña de árbol sintáctico (con visualizador colapsable)
        self.tab_sintactico_frame = tk.Frame(self.results_notebook, bg="#1e1e1e")
        self.results_notebook.add(self.tab_sintactico_frame, text="Sintactico")
        self.ast_tree_viewer = ASTTreeViewer(self.tab_sintactico_frame)
        self.tab_sintactico = None  # No se usa Text widget para esta pestaña
        
        self.tab_sintactico_conectado = self._make_result_tab("Arbol Conectado")
        self.tab_sintactico_analisis = self._make_result_tab("Analisis Sintactico")
        self.tab_semantico = self._make_result_tab("Semantico", wrap="none")

        # Fase 3: árbol con anotaciones semánticas
        self.tab_anotado_frame = tk.Frame(self.results_notebook, bg="#1e1e1e")
        self.results_notebook.add(self.tab_anotado_frame, text="Arbol Anotado")
        self.annotated_tree_viewer = ASTTreeViewer(
            self.tab_anotado_frame,
            title="Árbol con anotaciones semánticas",
            subtitle="tipos, valores y conversiones",
            semantic=True,
        )

        # Fase 3: AST original frente al AST anotado
        self.tab_comparacion_frame = tk.Frame(self.results_notebook, bg="#1e1e1e")
        self.results_notebook.add(self.tab_comparacion_frame, text="Comparacion")
        self._build_comparison_tab()

        self.tab_intermedio = self._make_result_tab("Intermedio")
        self.tab_simbolos = self._make_result_tab("Simbolos", wrap="none")

    #Pestaña "Comparacion": AST original (izquierda) y AST anotado (derecha)
    def _build_comparison_tab(self):
        bar = tk.Frame(self.tab_comparacion_frame, bg="#15171c")
        bar.pack(fill=tk.X)
        tk.Button(
            bar, text="Comparar en ventana grande", command=self.open_comparison_window,
            bg="#232833", fg="#f5f7fb", activebackground="#303848",
            activeforeground="#ffffff", relief=tk.FLAT, bd=0, padx=12, pady=5,
            cursor="hand2", font=("Segoe UI", 9, "bold"),
        ).pack(side=tk.LEFT, padx=10, pady=(8, 0))
        tk.Label(
            bar, text="AST original  →  AST con anotaciones semánticas",
            bg="#15171c", fg="#8f98aa", font=("Segoe UI", 9),
        ).pack(side=tk.LEFT, padx=10, pady=(8, 0))

        self.compare_original_viewer, self.compare_annotated_viewer = (
            self._build_comparison_viewers(self.tab_comparacion_frame)
        )

    def _build_comparison_viewers(self, parent):
        #Dos visores lado a lado: AST original (izq.) y AST anotado (der.)
        pane = tk.PanedWindow(parent, orient=tk.HORIZONTAL,
                              sashrelief=tk.RAISED, bg="#1e1e1e")
        pane.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(pane, bg="#15171c")
        right = tk.Frame(pane, bg="#15171c")
        pane.add(left, minsize=150)
        pane.add(right, minsize=150)

        original = ASTTreeViewer(
            left, title="AST original", semantic=False, compact=True
        )
        anotado = ASTTreeViewer(
            right, title="AST con anotaciones", semantic=True, compact=True
        )
        return original, anotado

    def open_comparison_window(self):
        #Abre la comparación en una ventana grande (más espacio para ver las anotaciones)
        top = tk.Toplevel(self.root.winfo_toplevel())
        top.title("Comparación: AST original  →  AST con anotaciones semánticas")
        top.geometry("1400x800")
        original, anotado = self._build_comparison_viewers(top)
        if self.compare_original_viewer.current_ast_json:
            original.load_ast_json(self.compare_original_viewer.current_ast_json)
        if self.compare_annotated_viewer.current_ast_json:
            anotado.load_ast_json(self.compare_annotated_viewer.current_ast_json)

    #Panel inferior "Errores y ejecucion"
    def _build_bottom_panel(self):
        label = tk.Label(self.bottom_frame, text="Errores y Ejecucion", bg="#2d2d2d", fg="white", font=("Segoe UI", 9, "bold"), anchor="w", padx=5)
        label.pack(fill=tk.X)

        self.bottom_notebook = ttk.Notebook(self.bottom_frame)
        self.bottom_notebook.pack(fill=tk.BOTH, expand=True)

        #Ventana de errores y ejecucion
        self.tab_err_lexico = self._make_result_tab("Errores Lexicos", notebook = self.bottom_notebook)
        self.tab_err_sintactico = self._make_result_tab("Errores Sintacticos", notebook = self.bottom_notebook)
        self.tab_err_semantico = self._make_result_tab("Errores Semanticos", notebook = self.bottom_notebook)
        self.tab_ejecucion = self._make_result_tab("Ejecucion", notebook = self.bottom_notebook)

    #Ventana de solo lectura
    def _make_result_tab(self, title, notebook = None, wrap = "char"):
        if notebook is None:
            notebook = self.results_notebook

        frame = tk.Frame(notebook, bg="#1e1e1e")
        notebook.add(frame, text=title)

        text_widget = tk.Text(frame, state="disabled", bg="#1e1e1e", fg="#d4d4d4", font=("Courier New", 10), relief=tk.FLAT, insertbackground="white", wrap=wrap)
        scrollbar = tk.Scrollbar(frame, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)

        #Sin ajuste de linea (tablas y arboles en texto): desplazamiento horizontal
        if wrap == "none":
            hscroll = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=text_widget.xview)
            text_widget.config(xscrollcommand=hscroll.set)
            hscroll.pack(side=tk.BOTTOM, fill=tk.X)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.pack(fill=tk.BOTH, expand=True)

        # Registrar la relación widget ↔ frame para get_tab_frame()
        self._tab_frames[text_widget] = frame

        return text_widget

    #escribir en un panel
    def write(self, widget, content):

        widget.config(state = "normal")
        widget.delete(1.0, tk.END)
        widget.insert(tk.END, content)
        widget.config(state = "disabled")

    #limpiar un panel
    def clear(self, widget):
        if widget is None:
            return
        widget.config(state = "normal")
        widget.delete(1.0, tk.END)
        widget.config(state = "disabled")

    #limpiar todos los paneles
    def clear_all(self):

        for widget in [
            self.tab_lexico, self.tab_sintactico_conectado,
            self.tab_sintactico_analisis, self.tab_semantico,
            self.tab_intermedio, self.tab_simbolos,
            self.tab_err_lexico, self.tab_err_sintactico,
            self.tab_err_semantico, self.tab_ejecucion
        ]:
            self.clear(widget)
        for viewer in (
            self.ast_tree_viewer,
            self.annotated_tree_viewer,
            self.compare_original_viewer,
            self.compare_annotated_viewer,
        ):
            if viewer:
                viewer.clear()

    def get_tab_frame(self, text_widget: tk.Text) -> tk.Frame | None:
        """
        Retorna el tk.Frame contenedor de la pestaña que aloja a `text_widget`.
        Usado por IDEWindow para seleccionar pestañas en el Notebook de forma
        robusta, sin depender de la jerarquía interna de widgets (.master).
        """
        return self._tab_frames.get(text_widget)

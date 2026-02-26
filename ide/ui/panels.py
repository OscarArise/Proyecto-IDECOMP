import tkinter as tk
from tkinter import ttk

class Panels:
    #Organizacion de paneles del ide
    def __init__(self, root):
        self.root = root
        self._build_layout()
    
    def _build_layout(self):
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
    
    def _on_resize(self, event = None):
        if event.widget == self.root:
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
        self.tab_sintactico = self._make_result_tab("Sintactico")
        self.tab_semantico = self._make_result_tab("Semantico")
        self.tab_intermedio = self._make_result_tab("Intermedio")
        self.tab_simbolos = self._make_result_tab("Simbolos")
        
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
    def _make_result_tab(self, title, notebook = None):
        if notebook is None:
            notebook = self.results_notebook
            
        frame = tk.Frame(notebook, bg="#1e1e1e")
        notebook.add(frame, text=title)
        
        text_widget = tk.Text(frame, state="disabled", bg="#1e1e1e", fg="#d4d4d4", font=("Courier New", 10), relief=tk.FLAT, insertbackground="white")
        scrollbar = tk.Scrollbar(frame, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        return text_widget
    
    #escribir en un panel
    def write(self, widget, content):
        
        widget.config(state = "normal")
        widget.delete(1.0, tk.END)
        widget.insert(tk.END, content)
        widget.config(state = "disabled")        
    
    #limpiar un panel
    def clear(self, widget):
        
        widget.config(state = "normal")
        widget.delete(1.0, tk.END)
        widget.config(state = "disabled")
        
    #limpiar todos los paneles
    def clear_all(self):

        for widget in [
            self.tab_lexico, self.tab_sintactico, self.tab_semantico,
            self.tab_intermedio, self.tab_simbolos,
            self.tab_err_lexico, self.tab_err_sintactico,
            self.tab_err_semantico, self.tab_ejecucion
        ]:
            self.clear(widget)
            
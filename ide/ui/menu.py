import tkinter as tk 

class Menu:
    def __init__(self, root, callbacks):
        #Callbacks diccionario de las funciones que ejecutan cada opcion
        self.root = root
        self.callbacks = callbacks
        self.menubar = tk.Menu(self.root)
        
        self._create_file_menu()
        self._create_compile_menu()
        
        self.root.config(menu = self.menubar)
        
    # Menu del archivo
    def _create_file_menu(self):
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Archivo", menu=file_menu)
        
        file_menu.add_command(label="Nuevo", command=self.callbacks.get("new_file"))
        file_menu.add_command(label="Abrir", command=self.callbacks.get("open_file"))
        file_menu.add_command(label="Cerrar", command=self.callbacks.get("close_file"))
        file_menu.add_separator()
        file_menu.add_command(label="Guardar", command=self.callbacks.get("save_file"))
        file_menu.add_command(label="Guardar como...", command=self.callbacks.get("save_as"))
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.callbacks.get("exit_app"))
        
    #Menu compilar
    def _create_compile_menu(self):
        compile_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Compilar", menu=compile_menu)
        
        compile_menu.add_command(label="Analisis lexico", command=self.callbacks.get("lexico"))
        compile_menu.add_command(label="Analisis Sintactico", command=self.callbacks.get("sintactico"))
        compile_menu.add_command(label="Analisis Semantico", command=self.callbacks.get("semantico"))
        compile_menu.add_command(label="Generacion de Codigo Intermedio", command=self.callbacks.get("intermedio"))
        compile_menu.add_separator()
        compile_menu.add_command(label="Ejecutar", command=self.callbacks.get("ejecutar"))
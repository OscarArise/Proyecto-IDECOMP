import tkinter as tk


class Menu:
    def __init__(self, root, callbacks):
        #diccionario de las funciones que ejecuta cada opción
        self.root = root
        self.callbacks = callbacks
        self.menubar = tk.Menu(self.root)

        self._create_file_menu()
        self._create_compile_menu()

        self.root.config(menu=self.menubar)

    #Menu archivo
    def _create_file_menu(self):
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Archivo", menu=file_menu)

        file_menu.add_command(
            label="Nuevo",
            accelerator="Ctrl+N",
            command=self.callbacks.get("new_file"),
        )
        file_menu.add_command(
            label="Abrir...",
            accelerator="Ctrl+O",
            command=self.callbacks.get("open_file"),
        )
        file_menu.add_command(
            label="Cerrar",
            accelerator="Ctrl+W",
            command=self.callbacks.get("close_file"),
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Guardar",
            accelerator="Ctrl+S",
            command=self.callbacks.get("save_file"),
        )
        file_menu.add_command(
            label="Guardar como...",
            accelerator="Ctrl+Shift+S",
            command=self.callbacks.get("save_as"),
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Salir",
            accelerator="Alt+F4",
            command=self.callbacks.get("exit_app"),
        )

    #Menu compilar
    def _create_compile_menu(self):
        compile_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Compilar", menu=compile_menu)

        compile_menu.add_command(
            label="Análisis Léxico",
            accelerator="F5",
            command=self.callbacks.get("lexico"),
        )
        compile_menu.add_command(
            label="Análisis Sintáctico",
            accelerator="F6",
            command=self.callbacks.get("sintactico"),
        )
        compile_menu.add_command(
            label="Análisis Semántico",
            accelerator="F7",
            command=self.callbacks.get("semantico"),
        )
        compile_menu.add_command(
            label="Generación de Código Intermedio",
            accelerator="F8",
            command=self.callbacks.get("intermedio"),
        )
        compile_menu.add_separator()
        compile_menu.add_command(
            label="Ejecutar",
            accelerator="F9",
            command=self.callbacks.get("ejecutar"),
        )
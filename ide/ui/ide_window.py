import os
import tkinter as tk
from tkinter import messagebox

from core.compiler_runner import CompilerRunner
from core.file_manager import FileManager
from core.state import AppState

# Lexico
from ui.highlighter import SyntaxHighlighter
from ui.menu import Menu
from ui.panels import Panels
from ui.toolbar import Toolbar


class IDEWindow:
    def __init__(self, root):
        self.root = root
        self.root.geometry("800x600")
        self.state = AppState()
        self._last_errors_content = ""
        self._suppress_modified = False
        self._create_ui()

        self.file_manager = FileManager(
            root=self.root,
            state=self.state,
            get_content=self._get_editor_content,
            set_content=self._set_editor_content,
            update_title=self._on_title_update,
        )
        self.compiler = CompilerRunner()

        self._bind_keyboard_shortcuts()
        self._bind_editor_events()

        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        self._on_title_update(None, False)
        self.toolbar.set_compile_buttons_state(False)  # #Sin archivo al inicio

    def _create_ui(self):
        # Barra de menú
        Menu(
            self.root,
            {
                "new_file": self.new_file,
                "open_file": self.open_file,
                "close_file": self.close_file,
                "save_file": self.save_file,
                "save_as": self.save_as,
                "exit_app": self.exit_app,
                "lexico": self.run_lexico,
                "sintactico": self.run_sintactico,
                "semantico": self.run_semantico,
                "intermedio": self.run_intermedio,
                "ejecutar": self.run_ejecutar,
            },
        )

        # Barra de herramientas (guardar referencia para controlar estado)
        self.toolbar = Toolbar(
            self.root,
            {
                "new_file": self.new_file,
                "open_file": self.open_file,
                "save_file": self.save_file,
                "lexico": self.run_lexico,
                "sintactico": self.run_sintactico,
                "semantico": self.run_semantico,
                "intermedio": self.run_intermedio,
                "ejecutar": self.run_ejecutar,
            },
        )

        # Barra de estado (debe empaquetarse antes que los paneles)
        self._create_status_bar()

        # Paneles divididos (editor | resultados / errores)
        self.panels = Panels(self.root)

        # Área de edición con numeración de líneas
        self._create_text_area()

    # Área de texto
    def _create_text_area(self):
        frame = tk.Frame(self.panels.editor_frame)
        frame.pack(fill=tk.BOTH, expand=True)

        # Numeración de líneas
        self.line_numbers = tk.Canvas(frame, width=35, bg="lightgray")
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Scrollbar vertical
        self.scrollbar = tk.Scrollbar(frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Editor principal
        self.text_area = tk.Text(
            frame,
            wrap="none",
            width=80,
            height=20,
            yscrollcommand=self._on_yscroll,
        )
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.text_area.yview)
        self.highlighter = SyntaxHighlighter(self.text_area)

    # Barra de estado (fila inferior)
    def _create_status_bar(self):
        bar = tk.Frame(self.root, bd=1, relief=tk.SUNKEN)
        bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Posición del cursor (izquierda)
        self.status_cursor = tk.Label(bar, text="Ln 1, Col 1", anchor="w", padx=6)
        self.status_cursor.pack(side=tk.LEFT)

        tk.Label(bar, text="|", fg="#cccccc").pack(side=tk.LEFT)

        # Mensaje de estado del compilador/archivo (centro-izquierda)
        self.status_bar = tk.Label(bar, text="Listo", anchor="w", padx=6)
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Nombre del archivo activo (derecha)
        self.status_file = tk.Label(
            bar, text="Sin archivo", anchor="e", padx=6, fg="#555555"
        )
        self.status_file.pack(side=tk.RIGHT)

    # Bindings
    def _bind_keyboard_shortcuts(self):
        """Registra todos los atajos de teclado"""
        self.root.bind_all("<Control-n>", lambda e: self.new_file())
        self.root.bind_all("<Control-N>", lambda e: self.new_file())
        self.root.bind_all("<Control-o>", lambda e: self.open_file())
        self.root.bind_all("<Control-O>", lambda e: self.open_file())
        self.root.bind_all("<Control-s>", lambda e: self.save_file())
        self.root.bind_all("<Control-S>", lambda e: self.save_file())
        self.root.bind_all("<Control-Shift-s>", lambda e: self.save_as())
        self.root.bind_all("<Control-Shift-S>", lambda e: self.save_as())
        self.root.bind_all("<Control-w>", lambda e: self.close_file())
        self.root.bind_all("<Control-W>", lambda e: self.close_file())

        self.root.bind_all("<F5>", lambda e: self.run_lexico())
        self.root.bind_all("<F6>", lambda e: self.run_sintactico())
        self.root.bind_all("<F7>", lambda e: self.run_semantico())
        self.root.bind_all("<F8>", lambda e: self.run_intermedio())
        self.root.bind_all("<F9>", lambda e: self.run_ejecutar())

    def _bind_editor_events(self):
        """Bindings propios del área de texto."""
        self.text_area.bind("<<Modified>>", self._on_text_modified)
        self.text_area.bind("<KeyRelease>", self._on_key_release_highlight)
        self.text_area.bind("<ButtonRelease-1>", self._update_cursor_position)
        self._update_line_numbers()
        self._update_cursor_position()

    def _on_yscroll(self, first: float, last: float) -> None:
        """Intercepta el scroll vertical del editor.
        Actualiza la scrollbar y sincroniza el canvas de números de línea."""
        self.scrollbar.set(first, last)
        self._update_line_numbers()

    def _on_text_modified(self, event=None):
        """Se dispara via <<Modified>> cuando el contenido del editor cambia.
        Reemplaza el mecanismo de polling: más eficiente y reactivo."""
        # Resetear el flag para que el evento vuelva a dispararse en el próximo cambio
        self.text_area.edit_modified(False)
        if self._suppress_modified:
            return
        self._sync()
        # Limpiar marcas de error al detectar cualquier cambio de contenido
        if self._last_errors_content:
            self._last_errors_content = ""
            self.highlighter.clear_error_marks()
            self.line_numbers.delete("error_line")
        self._mark_as_modified()

    def _sync(self, event=None):
        self._update_line_numbers()
        self._update_cursor_position()

    def _mark_as_modified(self):
        """Marca el documento como modificado y refleja el cambio en la UI."""
        if not self.state.is_modified:
            self.state.mark_modified()
            self._refresh_title_and_status()

    def _update_line_numbers(self, event=None):
        self.line_numbers.delete("all")
        first_line = int(self.text_area.index("@0,0").split(".")[0])
        last_line = int(
            self.text_area.index(f"@0,{self.text_area.winfo_height()}").split(".")[0]
        )
        for line in range(first_line, last_line + 1):
            dline = self.text_area.dlineinfo(f"{line}.0")
            if dline:
                y = dline[1]
                self.line_numbers.create_text(18, y, anchor="nw", text=str(line))

        # Redibujar las lineas de error si existen
        if hasattr(self, "_last_errors_content") and self._last_errors_content:
            self.highlighter.mark_error_lines(
                self._last_errors_content, self.line_numbers
            )

    def _update_cursor_position(self, event=None):
        pos = self.text_area.index(tk.INSERT)
        line, col = pos.split(".")
        self.status_cursor.config(text=f"Ln {line}, Col {int(col) + 1}")

    def _on_key_release_highlight(self, event=None):
        """Actualiza numeración, cursor y resaltado al soltar una tecla."""
        self._update_line_numbers()
        self._update_cursor_position()
        self.highlighter.highlight()

    # Callbacks inyectados en FileManager
    def _get_editor_content(self) -> str:
        """Devuelve el texto del editor sin el '\n' final que añade tk.Text."""
        return self.text_area.get("1.0", tk.END).rstrip("\n")

    def _set_editor_content(self, content: str):
        """Reemplaza el contenido completo del editor."""
        self._suppress_modified = True
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert(tk.END, content)
        self.text_area.edit_modified(
            False
        )  # Descartar el <<Modified>> generado al cargar
        self._suppress_modified = False
        self._update_line_numbers()
        self._update_cursor_position()
        self.highlighter.highlight()

    def _on_title_update(self, path: str | None, modified: bool):
        """
        Callback que FileManager llama después de cada operación de archivo.
        Centraliza la actualización de título, barra de estado y toolbar.
        """
        # Título de la ventana
        if path:
            filename = os.path.basename(path)
            marker = " \u2605" if modified else ""  # ★ en lugar de asterisco
            self.root.title(f"IDE CAOS \u2014 {filename}{marker}")
        else:
            self.root.title("IDE CAOS \u2014 Nuevo Archivo")

        self._refresh_title_and_status()

    def _refresh_title_and_status(self):
        """Sincroniza la barra de estado inferior y el estado de la toolbar."""
        path = self.state.current_file
        modified = self.state.is_modified

        # Etiqueta del archivo en la esquina inferior derecha
        if path:
            self.status_file.config(text=os.path.basename(path))
        else:
            self.status_file.config(text="Sin archivo")

        # Mensaje de estado
        if modified:
            self.status_bar.config(text="\u25cf Cambios sin guardar", fg="#c0392b")
        else:
            self.status_bar.config(text="Listo", fg="#2c2c2c")

        # Habilitar botones de compilación si hay un archivo abierto.
        # Se deshabilitan únicamente cuando no hay ningún archivo (estado inicial
        # o tras cerrar). Si hay cambios sin guardar, _run_phase se encarga de
        # pedir guardar antes de ejecutar el compilador.
        has_file = bool(path)
        self.toolbar.set_compile_buttons_state(has_file)

    # Operaciones de archivo (delegan a FileManager)

    def new_file(self):
        self.file_manager.new_file()

    def open_file(self):
        self.file_manager.open_file()

    def save_file(self):
        self.file_manager.save_file()

    def save_as(self):
        self.file_manager.save_as()

    def close_file(self):
        self.file_manager.close_file()

    def exit_app(self):
        self.file_manager.exit_app()

    # API pública — Fases del compilador (delegan a CompilerRunner)
    def run_lexico(self):
        self._run_phase("lexico")

    def run_sintactico(self):
        self._run_phase("sintactico")

    def run_semantico(self):
        self._run_phase("semantico")

    def run_intermedio(self):
        self._run_phase("intermedio")

    def run_ejecutar(self):
        self._run_phase("ejecutar")

    def _run_phase(self, phase: str):

        # Guardar antes de compilar
        if self.state.has_unsaved_changes() or not self.state.current_file:
            self.file_manager.save_file()

        # Verificar que haya archivo guardado
        if not self.state.current_file:
            messagebox.showwarning(
                "Sin archivo",
                "Guarda el archivo antes de compilar.",
                parent=self.root,
            )
            return

        # Limpiar paneles
        self.panels.clear_all()
        self.status_bar.config(
            text=f"\u23f3 Ejecutando fase: {phase.capitalize()}...", fg="#7f8c8d"
        )
        self.root.update_idletasks()  # Refrescar UI antes de bloquear
        # Limpiar marcas anteriores
        self.highlighter.clear_error_marks()
        self.line_numbers.delete("error_line")

        # Ejecutar compilador
        result = self.compiler.run(
            source_file=self.state.current_file,
            phase=phase,
        )

        # Volcar salidas en paneles de resultados
        panel_map = {
            "lexico": self.panels.tab_lexico,
            "sintactico": self.panels.tab_sintactico,
            "semantico": self.panels.tab_semantico,
            "intermedio": self.panels.tab_intermedio,
            "simbolos": self.panels.tab_simbolos,
            "ejecucion": self.panels.tab_ejecucion,
        }
        for key, widget in panel_map.items():
            content = result.outputs.get(key, "")
            if content.strip():
                self.panels.write(widget, content)

        # Volcar errores en paneles de error
        error_panel_map = {
            "err_lexico": self.panels.tab_err_lexico,
            "err_sintactico": self.panels.tab_err_sintactico,
            "err_semantico": self.panels.tab_err_semantico,
        }
        for key, widget in error_panel_map.items():
            content = result.errors_by_phase.get(key, "")
            if content.strip():
                self.panels.write(widget, content)

        # stderr del proceso (error interno del compilador)

        # Marcar errores en el editor
        errors_content = result.errors_by_phase.get("err_lexico", "")
        self._last_errors_content = errors_content
        self.highlighter.mark_errors(errors_content)
        self.highlighter.mark_error_lines(errors_content, self.line_numbers)

        # stderr del proceso (error interno del compilador)
        if result.stderr.strip():
            self.panels.write(
                self.panels.tab_err_lexico,
                f"[Error interno del compilador]\n{result.stderr}",
            )

        # Navegar a la pestaña del resultado de esta fase
        self._focus_result_tab(phase, result.success)

        # Actualizar barra de estado
        if result.success:
            self.status_bar.config(
                text=f"\u2714 Fase '{phase.capitalize()}' completada sin errores",
                fg="#27ae60",
            )
        else:
            fase_fallida = result.failed_phase or "desconocida"
            self.status_bar.config(
                text=f"\u2716 Error en fase: {fase_fallida}  (c\u00f3d. {result.returncode})",
                fg="#c0392b",
            )

    # Navegación automática de pestañas tras compilar
    # Mapa fase → (notebook_attr, tab_widget_attr)
    _PHASE_TAB = {
        "lexico": ("results_notebook", "tab_lexico"),
        "sintactico": ("results_notebook", "tab_sintactico"),
        "semantico": ("results_notebook", "tab_semantico"),
        "intermedio": ("results_notebook", "tab_intermedio"),
        "ejecutar": ("bottom_notebook", "tab_ejecucion"),
    }
    _PHASE_ERR_TAB = {
        "lexico": ("bottom_notebook", "tab_err_lexico"),
        "sintactico": ("bottom_notebook", "tab_err_sintactico"),
        "semantico": ("bottom_notebook", "tab_err_semantico"),
        "intermedio": ("bottom_notebook", "tab_err_lexico"),
        "ejecutar": ("bottom_notebook", "tab_ejecucion"),
    }

    def _focus_result_tab(self, phase: str, success: bool):
        """
        Selecciona la pestaña de resultado (éxito) o de error (fallo)
        correspondiente a la fase que acaba de ejecutarse.
        """
        if success:
            entry = self._PHASE_TAB.get(phase)
        else:
            entry = self._PHASE_ERR_TAB.get(phase)

        if not entry:
            return

        notebook_attr, tab_attr = entry
        notebook = getattr(self.panels, notebook_attr, None)
        tab_widget = getattr(self.panels, tab_attr, None)

        if notebook and tab_widget:
            frame = self.panels.get_tab_frame(tab_widget)
            if frame:
                try:
                    notebook.select(frame)
                except Exception:
                    pass  # Silenciar si el frame no es seleccionable

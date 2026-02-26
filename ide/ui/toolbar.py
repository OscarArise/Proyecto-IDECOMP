import tkinter as tk


class Toolbar:
    def __init__(self, root, callbacks):
        self.root = root
        self.callbacks = callbacks
        # Guardar referencia a botones que dependen del estado (compilar/ejecutar)
        self._compile_buttons: list[tk.Button] = []
        self._build_toolbar()

    def _build_toolbar(self):
        # Contenedor del Toolbar
        self.frame = tk.Frame(self.root, bd=1, relief=tk.RAISED, bg="#f0f0f0")
        self.frame.pack(side=tk.TOP, fill=tk.X, padx=2, pady=(0, 1))

        # Definición de los botones
        # (icono, tooltip, callback_key, grupo)
        # grupo = "file" | "compile" — los del grupo "compile" se desactivan sin archivo
        buttons = [
            ("📄", "Nuevo       Ctrl+N", "new_file",   "file"),
            ("📂", "Abrir       Ctrl+O", "open_file",  "file"),
            ("💾", "Guardar     Ctrl+S", "save_file",  "file"),
            None,
            ("🔤", "Léxico      F5",     "lexico",     "compile"),
            ("🌳", "Sintáctico  F6",     "sintactico", "compile"),
            ("🔍", "Semántico   F7",     "semantico",  "compile"),
            ("⚙️", "Intermedio  F8",     "intermedio", "compile"),
            None,
            ("▶️", "Ejecutar    F9",     "ejecutar",   "compile"),
        ]

        for item in buttons:
            if item is None:
                self._add_separator()
            else:
                icon, tooltip, key, group = item
                btn = self._add_button(icon, tooltip, key)
                if group == "compile":
                    self._compile_buttons.append(btn)

    def _add_button(self, icon, tooltip, callback_key) -> tk.Button:
        btn = tk.Button(
            self.frame,
            text=icon,
            font=("Segoe UI Emoji", 10),
            relief=tk.FLAT,
            bg="#f0f0f0",
            activebackground="#dde8f0",
            cursor="hand2",
            width=2,
            command=self.callbacks.get(callback_key),
        )
        btn.pack(side=tk.LEFT, padx=1, pady=1)
        self._add_tooltip(btn, tooltip)
        return btn

    def _add_separator(self):
        sep = tk.Label(
            self.frame, text="|", bg="#f0f0f0", fg="#aaaaaa", font=("Segoe UI", 12)
        )
        sep.pack(side=tk.LEFT, padx=4, pady=2)

    def _add_tooltip(self, widget, text):
        """Tooltip emergente al pasar el mouse."""
        def on_enter(event):
            self.tooltip = tk.Toplevel(self.root)
            self.tooltip.wm_overrideredirect(True)
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + 30
            self.tooltip.wm_geometry(f"+{x}+{y}")
            label = tk.Label(
                self.tooltip,
                text=text,
                bg="#ffffe0",
                fg="black",
                font=("Segoe UI", 9),
                relief=tk.SOLID,
                borderwidth=1,
                padx=4,
                pady=2,
            )
            label.pack()

        def on_leave(event):
            if hasattr(self, "tooltip"):
                self.tooltip.destroy()

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    # API pública: habilitar / deshabilitar botones de compilación

    def set_compile_buttons_state(self, enabled: bool):
        """
        Habilita o deshabilita los botones de fase de compilación.
        Llamar con enabled=True cuando hay un archivo abierto/guardado,
        False cuando no hay archivo activo.
        """
        state = tk.NORMAL if enabled else tk.DISABLED
        for btn in self._compile_buttons:
            btn.config(state=state)
import tkinter as tk
from PIL import Image, ImageTk, ImageEnhance
import os


class Toolbar:
    def __init__(self, root, callbacks):
        self.root = root
        self.callbacks = callbacks
        # Guardar referencia a botones que dependen del estado (compilar/ejecutar)
        self._compile_buttons: list = []
        self.icons = {} # guardar referencias para evitar garbage collection
        
        #Ruta de los iconos
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icons_dir = os.path.join(base_dir, "..", "assets", "icons")
        
        self._build_toolbar()

    def _build_toolbar(self):
        # Contenedor del Toolbar
        self.frame = tk.Frame(self.root, bd=1, relief=tk.RAISED, bg="#e0e0e0")
        self.frame.pack(side=tk.TOP, fill=tk.X, padx=2, pady=(0, 1))

        # Definición de los botones
        # (icono, tooltip, callback_key, grupo)
        buttons = [
            ("new_file.png", "Nuevo       Ctrl+N", "new_file",   "file"),
            ("open_file.png", "Abrir       Ctrl+O", "open_file",  "file"),
            ("save.png", "Guardar     Ctrl+S", "save_file",  "file"),
            None,
            ("lexico.png", "Léxico      F5",     "lexico",     "compile"),
            ("sintactico.png", "Sintáctico  F6",     "sintactico", "compile"),
            ("semantico.png", "Semántico   F7",     "semantico",  "compile"),
            ("intermedio.png", "Intermedio  F8",     "intermedio", "compile"),
            None,
            ("ejecutar.png", "Ejecutar    F9",     "ejecutar",   "compile"),
        ]

        for item in buttons:
            if item is None:
                self._add_separator()
            else:
                icon, tooltip, key, group = item
                btn = self._add_button(icon, tooltip, key)
                if group == "compile":
                    self._compile_buttons.append(btn)
    
    #Carga y redimensiona el icono
    def _load_icon(self, filename):
        path = os.path.join(self.icons_dir, filename)
        try:
            img = Image.open(path).resize((32, 32), Image.LANCZOS).convert("RGBA")

            r, g, b, a = img.split()
            rgb = Image.merge("RGB", (r, g, b))
            rgb = ImageEnhance.Brightness(rgb).enhance(1.1)
            rgb = ImageEnhance.Color(rgb).enhance(1.8)
            rgb = ImageEnhance.Sharpness(rgb).enhance(2.0)
            r, g, b = rgb.split()
            img = Image.merge("RGBA", (r, g, b, a))
            
            photo = ImageTk.PhotoImage(img)
            self.icons[filename] = photo
            return photo
        
        except Exception as e:
            print(f"No se pudo encontrar el icono {filename}: {e}")
            return None
                
    def _add_button(self, icon_file, tooltip, callback_key):
        icon = self._load_icon(icon_file)
        
        btn = tk.Button(
            self.frame,
            image=icon if icon else None,
            text="" if icon else tooltip,
            relief=tk.FLAT,
            bg="#e0e0e0",
            activebackground="#c8c8c8",
            cursor="hand2",
            width=34,
            height=34,
            borderwidth=2,
            command=self.callbacks.get(callback_key),
        )
        btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Efecto visual al presionar y soltar
        btn.bind("<ButtonPress-1>",   lambda e, b=btn: b.config(relief=tk.SUNKEN, bg="#b8b8b8"))
        btn.bind("<ButtonRelease-1>", lambda e, b=btn: b.config(relief=tk.FLAT,   bg="#e0e0e0"))

        
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
            tk.Label(
                self.tooltip,
                text=text,
                bg="#ffffe0",
                fg="black",
                font=("Segoe UI", 9),
                relief=tk.SOLID,
                borderwidth=1,
                padx=4,
                pady=2,
            ).pack()

        def on_leave(event):
            if hasattr(self, "tooltip"):
                self.tooltip.destroy()

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    # API pública: habilitar / deshabilitar botones de compilación

    def set_compile_buttons_state(self, enabled: bool):
        
        #Habilita o deshabilita los botones de fase de compilación.
        
        state = tk.NORMAL if enabled else tk.DISABLED
        for btn in self._compile_buttons:
            btn.config(state=state)
            


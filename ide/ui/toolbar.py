import tkinter as tk

class Toolbar:
    def __init__(self, root, callbacks):
        self.root = root
        self.callbacks = callbacks
        self._build_toolbar()
        
    def _build_toolbar(self):
        #Contenedor del Toolbar
        self.frame = tk.Frame(self.root, bd=1, relief=tk.RAISED, bg = "#f0f0f0")
        self.frame.pack(side=tk.TOP, fill=tk.X, padx=2, pady=(0,1))
        
        #Definicion de los botones 
        buttons = [
            ("📄", "Nuevo", "new_file"),
            ("📂", "Abrir", "open_file"),
            ("💾", "Guardar", "save_file"),
            None,
            ("🔤", "Lexico", "lexico"),
            ("🌳", "Sintactico", "sintactico"),
            ("🔍", "Semantico", "semantico"),
            ("⚙️", "Intermedio", "intermendio"),
            None,
            ("▶️", "Ejecutar", "ejecutar")
        ]
        
        for item in buttons:
            if item is None:
                self._add_separator()
            else:
                icon, tooltip, key, = item
                self._add_button(icon, tooltip, key)
                
    def _add_button(self, icon, tooltip, callback_key):
        btn = tk.Button(
            self.frame,
            text=icon,
            font=("Segoe UI Emoji", 10),
            relief=tk.FLAT,
            bg="#f0f0f0",
            activebackground="#dde8f0",
            cursor="hand2",
            width=2,
            command=self.callbacks.get(callback_key)
        )
        btn.pack(side=tk.LEFT, padx=1, pady=1)
        self._add_tooltip(btn, tooltip)
        
    def _add_separator(self):
        sep = tk.Label(self.frame, text="|", bg="#f0f0f0", fg="#aaaaaa", font=("Segoe UI", 12))
        sep.pack(side=tk.LEFT, padx=4, pady=2)  
        
    def _add_tooltip(self, widget, text):
        #tool tip al pasar el mouse
        def on_enter(event):
            self.tooltip = tk.Toplevel(self.root)      
            self.tooltip.wm_overrideredirect(True)
            x = widget.winfo_rootx() + 20 
            y = widget.winfo_rooty() + 30
            self.tooltip.wm_geometry(f"+{x}+{y}")
            label = tk.Label(self.tooltip, text=text, bg="#ffffe0", fg="black", font=("Segoe UI", 9), relief=tk.SOLID, borderwidth=1, padx=4, pady=2)
            label.pack()
            
        def on_leave(event):
            if hasattr(self, "tooltip"):
                self.tooltip.destroy()
                
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        
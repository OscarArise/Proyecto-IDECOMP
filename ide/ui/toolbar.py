import tkinter as tk
from PIL import Image, ImageTk
import os

class Toolbar:
    def __init__(self, root, callbacks):
        self.root = root
        self.callbacks = callbacks
        self.icons = {} # guardar referencias para evitar garbage collection
        
        #Ruta de los iconos
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icons_dir = os.path.join(base_dir, "..", "assets", "icons")
        
        self._build_toolbar()
        
    def _build_toolbar(self):
        #Contenedor del Toolbar
        self.frame = tk.Frame(self.root, bd=1, relief=tk.RAISED, bg = "#f0f0f0")
        self.frame.pack(side=tk.TOP, fill=tk.X, padx=2, pady=(0,1))
        
        #Definicion (archivo_icono, tooltip, callback_key)
        buttons = [
            ("new_file.png", "Nuevo", "new_file"),
            ("open_file.png", "Abrir", "open_file"),
            ("save.png", "Guardar", "save_file"),
            None,
            ("lexico.png", "Lexico", "lexico"),
            ("sintactico.png", "Sintactico", "sintactico"),
            ("semantico.png", "Semantico", "semantico"),
            ("intermedio.png", "Intermedio", "intermendio"),
            None,
            ("ejecutar.png", "Ejecutar", "ejecutar")
        ]
        
        for item in buttons:
            if item is None:
                self._add_separator()
            else:
                icon_file, tooltip, key, = item
                self._add_button(icon_file, tooltip, key)
    
    #Carga y redimensiona el icono
    def _load_icon(self, filename):
        path = os.path.join(self.icons_dir, filename)
        try:
            img = Image.open(path).resize((32, 32), Image.LANCZOS).convert("RGBA")
            
            data = img.getdata()
            new_data = []
            for r, g, b ,a in data:
                if r < 30 and g < 30 and b< 30:
                    new_data.append((r, g, b, 0))
                else:
                    new_data.append((r, g, b, a))
            img.putdata(new_data)
    
            photo = ImageTk.PhotoImage(img)
            self.icons[filename] = photo
            return photo
        except Exception as e:
            print(f"No se pudo cargar el icono {filename}: {e}")
            return None
                
    def _add_button(self, icon_file, tooltip, callback_key):
        icon = self._load_icon(icon_file)
        btn = tk.Button(
            self.frame,
            image=icon if icon else None,
            text="" if icon else tooltip,
            relief=tk.FLAT,
            bg="#f0f0f0",
            activebackground="#dde8f0",
            cursor="hand2",
            width=28,
            height=28,
            command=self.callbacks.get(callback_key)
        )
        btn.pack(side=tk.LEFT, padx=2, pady=2)
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
        
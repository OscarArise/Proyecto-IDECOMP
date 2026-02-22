import tkinter as tk
from tkinter import filedialog, messagebox, font
from ui.menu import Menu
from ui.panels import Panels
from ui.toolbar import Toolbar


class IDEWindow:
    def __init__(self,root):
        self.root = root
        self.root.title("IDE")
        self.root.geometry("800x600") # tamaño de la ventana
        self.current_file = None
        
        self.create_ui()
        
    def create_ui(self):
        #Interfaz de usuario
        
        #Barra de menu
        Menu(self.root,{
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
            "ejecutar": self.run_ejecutar
        })
        
        Toolbar(self.root,{
            "new_file": self.new_file,
            "open_file": self.open_file,
            "save_file": self.save_file,
            "lexico": self.run_lexico,
            "sintactico": self.run_sintactico,
            "semantico": self.run_semantico,
            "intermedio": self.run_intermedio,
            "ejecutar": self.run_ejecutar
        })
        
        #Barra de estado
        self.create_status_bar()
        
        #Paneles
        self.panels = Panels(self.root)
        
        #Area de texto para el editor
        self.create_text_area()
    
    
    #Funcion para el area de texto y numeracion de lineas
    def create_text_area(self):
        frame = tk.Frame(self.panels.editor_frame)
        frame.pack(fill=tk.BOTH, expand=True)    
        
        #Numeracion de lineas
        self.line_numbers = tk.Canvas(frame, width=35, bg='lightgray')  
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)  
        
        #Barra de desplazamiento 
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
        #Area del texto del editor
        self.text_area = tk.Text(frame, wrap='none', width=80, height=20, yscrollcommand=scrollbar.set)
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_area.yview)
        
        #Actualizar numeracion de lineas
        self.text_area.bind("<KeyRelease>", self.update_line_numbers)
        self.text_area.bind("<MouseWheel>", self.update_line_numbers)
        self.text_area.bind("<ButtonRelease-1>",self.update_cursor_position)
        self.update_line_numbers()
        self.update_cursor_position()
    
    # Funcion para crear la barra de estado
    def create_status_bar(self):
        self.status_bar = tk.Label(self.root, text="Ln 1, Col 1", bd=1, relief=tk.SUNKEN, anchor='w')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    #Actualizar la numeracion de lineas 
    def update_line_numbers(self, event=None):
        self.line_numbers.delete("all")
        
        first_line = int(self.text_area.index("@0,0").split(".")[0])
        last_line = int(self.text_area.index(f"@0,{self.text_area.winfo_height()}").split(".")[0])
        
        for line in range(first_line, last_line + 1):
            dline = self.text_area.dlineinfo(f"{line}.0")
            if dline:
                y = dline[1]
                self.line_numbers.create_text(18, y, anchor="nw", text=str(line))
                
    #Actualizar la posicion del cursor
    def update_cursor_position(self, event=None):
        cursor_position = self.text_area.index(tk.INSERT)
        line, col = cursor_position.split('.')
        self.status_bar.config(text=f"Ln {line}, Col {int(col) + 1}")
        
    #Logica para el nuevo archivo
    def new_file(self):
        self.text_area.delete(1.0, tk.END)
        self.current_file = None
        self.root.title("IDE - Nuevo Archivo")
        self.status_bar.config(text="Nuevo Archivo")
        self.update_line_numbers()
        
    #Logica para abrir un archivo
    def open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Archivos Caos", "*.caos"), ("Todos los archivos", "*.*")]
        )
        if path:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, content)
            self.current_file = path
            self.root.title(f"IDE - {path}")
            self.update_line_numbers()
            
    def close_file(self):
        self.text_area.delete(1.0, tk.END)
        self.current_file = None
        self.root.title("IDE")
        self.status_bar.config(text="Archivo cerrado")
        self.update_line_numbers()
    
    #Logica para guardar un archivo
    def save_file(self):
        if self.current_file:
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(self.text_area.get(1.0, tk.END))
            self.status_bar.config(text=f"Guardado: {self.current_file}")
            self.root.title(f"IDE - {self.current_file}")
        else:
            self.save_as()
    
    #Logica salvar como
    def save_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".caos",
            filetypes=[("Archivos Caos", "*.caos"), ("Todos los archivos", "*.*")]
        )
        if path:
            self.current_file = path
            self.save_file()
            self.root.title(f"IDE - {path}")
    
    #Logica para salir
    def exit_app(self):
        if messagebox.askokcancel("Salir", "Deseas salir del IDE?"):
            self.root.quit()
            
    
    #Fases del compilador
    def run_lexico(self): pass
    def run_sintactico(self): pass
    def run_semantico(self): pass
    def run_intermedio(self): pass
    def run_ejecutar(self): pass
    
#Codigo para iniciar
if __name__ == "__main__":
    root = tk.Tk()
    window = IDEWindow(root)
    root.mainloop()
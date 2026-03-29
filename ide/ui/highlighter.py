import re
import tkinter as tk 

#Palabras reservadas
RESERVED_WORDS = {
    "if", "else", "end", "do", "while", "switch", "case", "int", "float", "main", "cin", "cout", "real", "then", "until"
}

#Definicion de tokens con patrones y tags
#Los patrones mas especificos importan
TOKEN_PATTERNS = [
    #Comentarios multilinea /* ... */
    ("comment", r"/\*[\s\S]*?\*/"),
    #Comentarios de una linea //
    ("comment", r"//[^\n]*"),
    #Cadenas de texto "..."
    ("string", r'"[^"]*"'),
    #Caracteres ' ... '
    ("string", r"'[^']*'"),
    #Numeros reales
    ("number", r"\b\d+\.\d+\b"),
    #Numeros enteros
    ("number", r"\b\d+\b"),
    #Operadores logicos
    ("logical", r"&&|\|\||!(?!=)"),
    #Operadores racionales
    ("relational", r"<=|>=|==|!=|<|>"),
    #Operadores aritmeticos
    ("arithmetic", r"\+\+|--|[+\-*/%^]"),
    #Asignacion simple
    ("assing", r"=(?!=)"),
    #Simbolos
    ("symbol", r"[(){},;]"),
    #Identificadores y palabras reservadas
    ("identifier", r"\b[a-zA-Z_][a-zA-Z0-9]*\b"),
    #Error lexico
    ("error", r"[^\s]"),
]

#Colores por tag
TAG_COLORS = {
    "number": {"foreground": "#0B8A00"},      
    "identifier": {"foreground": "#1F1F1F"},
    "reserved": {"foreground": "#0033CC", "font_weight": "bold"},
    "comment": {"foreground": "#008B8B", "font_style": "italic"},  # Verde-azulado
    "string": {"foreground": "#B22222"},
    "arithmetic": {"foreground": "#FF8C00"},   
    "relational": {"foreground": "#800080"},
    "logical": {"foreground": "#C71585"},
    "assign": {"foreground": "#000000"},
    "symbol": {"foreground": "#696969"},
    "error": {"foreground": "#FF0000", "underline": True},
}

#Regex combinado con grupos nombrados
_COMBINED_PATTERN = re.compile(
    "|".join(f"(?P<{tag}_{i}>{pattern})"
             for i, (tag, pattern) in enumerate(TOKEN_PATTERNS)),
    re.MULTILINE
)

class SyntaxHighlighter:
    #Resaltado de la sintaxis en tiempo real para el editor de texto
    
    def __init__(self, text_widget: tk.Text):
        self.text = text_widget
        self._after_id = None #Para el debounce
        self._configure_tags()
        
    def _configure_tags(self):
        #Configura los tags de color en el widget text
        base_font = self.text.cget("font") or ("Courier New", 10)
        
        for tag, style in TAG_COLORS.items():
            options = {"foreground": style.get("foreground", "#000000")}
            
            if style.get("font_weight") == "bold":
                if isinstance(base_font, tuple):
                    options["font"] = (base_font[0], base_font[1], "bold")
                else: 
                    options["font"] = (base_font, 10, "bold")
                    
            if style.get("underline"):
                options["underline"] = True
            
            self.text.tag_configure(tag, **options)
            
        #Prioridad de tags (mayor numero = mayor prioridad)
        for i, tag in enumerate(TAG_COLORS.keys()):
            self.text.tag_raise(tag)
            
    def highlight(self, event = None):
        #Aplica resaltado con debounce de ms para no saturar mientras el usuario escribe rapido
        if self._after_id:
            self.text.after_cancel(self._after_id)
        self._after_id = self.text.after(100, self._apply_highlight)
        
    def _apply_highlight(self):
        #Aplica el resaltado al contenido completo del editor
        content = self.text.get("1.0", tk.END)
        
        #Limpiar todos los tags antes de replicar
        for tag in TAG_COLORS:
            self.text.tag_remove(tag, "1.0", tk.END)
            
        #Aplicar cada match
        for match in _COMBINED_PATTERN.finditer(content):
            start_idx = match.start()
            end_idx = match.end()
            
            #Convertir indice de caracter a linea.columna de Tkinter
            start = self._index(start_idx)
            end = self._index(end_idx)
            
            #Determinar el tag base del grupo que hizo match
            tag = self._get_tag(match)
            if not tag:
                continue
            
            #Si es identificador verificar si es palabra reservada
            if tag == "identifier" and match.group() in RESERVED_WORDS:
                tag = "reserved"
                
            self.text.tag_add(tag, start, end)
            
    def _get_tag(self, match: re.Match) -> str | None:
        #Extrae el nombre del tag desde el grupo con el que hizo match
        for group_name, value in match.groupdict().items():
            if value is not None:
                #El nombre del grupo es tag_index
                return group_name.rsplit("_", 1)[0]
            
        return None
        
    def _index(self, char_pos: int) -> str:
        #Convierte la posicion de caracter a formato linea-columna del Tkinter
        return self.text.index(f"1.0 + {char_pos}c") 
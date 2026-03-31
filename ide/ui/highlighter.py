import re
import sys as _sys
import os as _os
import tkinter as tk

# Resolver la ruta al paquete external_compiler (un nivel fuera de ide/)
_EC_DIR = _os.path.normpath(
    _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "external_compiler")
)
if _EC_DIR not in _sys.path:
    _sys.path.insert(0, _EC_DIR)

# Importar la tabla de palabras reservadas como única fuente de verdad.
# El try/except protege contra rutas no resueltas en análisis estático
# (Pylance) y garantiza resiliencia si el paquete externo no está disponible.
try:
    from lexer.reserved_words import RESERVED as _RESERVED  # type: ignore[import-not-found]
    RESERVED_WORDS: set[str] = set(_RESERVED.keys())
except ImportError:
    # Fallback hardcoded: refleja exactamente reserved_words.py
    RESERVED_WORDS = {
        "if", "else", "end", "do", "while", "switch", "case",
        "int", "real", "float", "main", "cin", "cout",
        "for", "return", "break", "then", "until", "default",
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
    ("arithmetic",  r"\+\+|--|[+\-*/%^]"),
    #Asignacion simple
    ("assign", r"=(?!=)"),
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

    #Marcado de errores lexicos

    #Patron para extraer linea y columna del formato:
    _ERROR_PATTERN = re.compile(
        r"en\s+l.nea\s+(\d+),\s+columna\s+(\d+)",
        re.IGNORECASE
    )

    def mark_errors(self, errors_content: str):
        #Lee el contenido de los errors.txt y marca cada error en el editor
        #Con un subrayado rojo en la posicion exacta

        #Limpiar marcas anteriores
        self.text.tag_remove("error_mark", "1.0", tk.END)
        #Configurar el tag de marcado si no existe
        self.text.tag_configure(
            "error_mark",
            underline=True,
            foreground="#FF0000"
        )

        if not errors_content.strip():
            return

        for line in errors_content.splitlines():
            match = self._ERROR_PATTERN.search(line)
            if not match:
                continue

            linea = int(match.group(1))
            columna = int(match.group(2))

            #Construir indices de inicio y fin del caracter erroneo
            start = f"{linea}.{columna - 1}"
            end = f"{linea}.{columna}"

            #Verificar que el indice existe en el editor
            try:
                self.text.tag_add("error_mark", start, end)
            except Exception:
                pass #Ignorar si la posicion no existe

    def clear_error_marks(self):
        #Elimina todas las marcas de error del editor
        self.text.tag_remove("error_mark", "1.0", tk.END)

    def mark_error_lines(self, errors_content: str, line_numbers_canvas):
        line_numbers_canvas.delete("error_line")

        if not errors_content.strip():
            return

        error_lines = set()
        for line in errors_content.splitlines():
            match = self._ERROR_PATTERN.search(line)
            if match:
                error_lines.add(int(match.group(1)))

        for linea in error_lines:
            dline = self.text.dlineinfo(f"{linea}.0")
            if dline:
                y = dline[1]
                h = dline[3]
                line_numbers_canvas.create_rectangle(
                    2, y, 33, y + h,
                    fill = "#FF0000",
                    outline = "",
                    tags = "error_line"
                )
                line_numbers_canvas.create_text(
                    18, y, anchor = "nw",
                    text = str(linea),
                    fill = "white",
                    tags = "error_line"
                )

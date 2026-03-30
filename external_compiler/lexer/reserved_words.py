"""
reserved_words.py
-----------------
Tabla de palabras reservadas del lenguaje CAOS.

Mapea lexema (str) → nombre del tipo de token (str).
El nombre debe coincidir con el atributo correspondiente en TokenType.

Uso dentro del DFA:
    from .reserved_words import RESERVED
    token_type = RESERVED.get(lexema, "IDENTIFIER")
"""

# Palabras reservadas del lenguaje CAOS — 16 keywords (en inglés)
RESERVED: dict[str, str] = {
    "if":      "KW_IF",
    "else":    "KW_ELSE",
    "end":     "KW_END",
    "do":      "KW_DO",
    "while":   "KW_WHILE",
    "switch":  "KW_SWITCH",
    "case":    "KW_CASE",
    "int":     "KW_INT",
    "real":    "KW_REAL",
    "float":   "KW_FLOAT",
    "main":    "KW_MAIN",
    "cin":     "KW_CIN",
    "cout":    "KW_COUT",
    "for":     "KW_FOR",
    "return":  "KW_RETURN",
    "break":   "KW_BREAK",
    "then":    "KW_THEN",
    "until":   "KW_UNTIL",
    "default": "KW_DEFAULT",
}

"""
reserved_words.py
-----------------
Tabla de palabras reservadas del lenguaje CAOS.

Mapea lexema (str) → nombre del tipo de token (str).
El nombre debe coincidir con el atributo correspondiente en TokenType.

Uso dentro del DFA:
    from .reserved_words import RESERVED
    token_type = RESERVED.get(lexema, "IDENTIFIER")

Tipos de dato del lenguaje
--------------------------
CAOS tiene tres tipos: int, float y bool. El léxico reconoce además la palabra
`real`, que el analizador sintáctico trata como alias de `float`: produce una
declaración de tipo "float" conservando el lexema escrito. No es un cuarto tipo.

Los literales que emite el DFA son INT_NUM, FLOAT_NUM, STRING, CHAR y las
palabras `true`/`false`. STRING solo es válido dentro de `cout`.

CHAR lo reconoce el DFA, pero ninguna producción de la gramática lo acepta: un
`'a'` en el código fuente pasa el léxico y lo rechaza el analizador sintáctico
("Se esperaba componente…"). Nunca llega al análisis semántico, así que CAOS no
tiene un tipo de dato carácter.
"""

# Palabras reservadas del lenguaje CAOS — 19 keywords (en inglés)
RESERVED: dict[str, str] = {
    "if":      "KW_IF",
    "else":    "KW_ELSE",
    "end":     "KW_END",
    "do":      "KW_DO",
    "while":   "KW_WHILE",
    "switch":  "KW_SWITCH",
    "case":    "KW_CASE",
    "int":     "KW_INT",
    "bool":    "KW_BOOL",
    "real":    "KW_REAL",   # alias de float (ver encabezado)
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
    "true":    "KW_TRUE",
    "false":   "KW_FALSE",
}

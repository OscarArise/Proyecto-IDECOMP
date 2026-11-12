"""
tipos.py
--------
Sistema de tipos del lenguaje CAOS y reglas de compatibilidad.

El lenguaje tiene tres tipos de dato: int, float y bool. 'real' es un alias de
'float' que el parser ya normaliza, así que nunca llega aquí. Las cadenas solo
existen como elementos de 'cout' y no participan en la verificación de tipos.

Tipos internos del analizador:
    ERROR   tipo de un nodo que ya produjo un error. Se propaga hacia arriba
            sin generar errores nuevos (evita errores en cascada).
    CADENA  tipo de un literal de cadena dentro de 'cout'.
"""

INT = "int"
FLOAT = "float"
BOOL = "bool"
CADENA = "cadena"
ERROR = "error"

TIPOS_DECLARABLES = (INT, FLOAT, BOOL)
NUMERICOS = (INT, FLOAT)

# Operadores por categoría
ARITMETICOS = ("+", "-", "*", "/", "^")
MODULO = "%"
RELACIONALES = ("<", "<=", ">", ">=")
IGUALDAD = ("==", "!=")
LOGICOS_BINARIOS = ("&&", "||")
NEGACION = "!"

# Conversión implícita permitida (ensanchamiento): int -> float
CONVERSIONES_PERMITIDAS = {(INT, FLOAT)}

# Tipo de cada literal según la clave 'tipo_literal' del AST
TIPO_DE_LITERAL = {
    "entero": INT,
    "flotante": FLOAT,
    "booleano": BOOL,
    "cadena": CADENA,
}


def es_numerico(tipo: str) -> bool:
    return tipo in NUMERICOS


def tipo_aritmetico(izq: str, der: str) -> str:
    """int op int -> int; si alguno es float, el resultado es float."""
    return FLOAT if FLOAT in (izq, der) else INT


def conversion_permitida(origen: str, destino: str) -> bool:
    return (origen, destino) in CONVERSIONES_PERMITIDAS

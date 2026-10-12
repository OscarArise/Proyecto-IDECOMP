"""
Análisis semántico del lenguaje CAOS (Fase 3).

Uso:
    from parser.ast_formatter import ASTFormatter
    from semantic import analizar

    resultado = analizar(ASTFormatter.to_binary(ast))
    resultado.arbol_anotado   # copia del AST con anotaciones
    resultado.tabla           # TablaSimbolos
    resultado.errores         # lista de ErrorSemantico
    resultado.traza           # recorrido paso a paso
"""

from .analizador import AnalizadorSemantico, ResultadoSemantico, analizar
from .errores import ErrorSemantico
from .tabla_simbolos import Simbolo, TablaSimbolos, funcion_hash

__all__ = [
    "AnalizadorSemantico",
    "ResultadoSemantico",
    "analizar",
    "ErrorSemantico",
    "Simbolo",
    "TablaSimbolos",
    "funcion_hash",
]

"""
parser package
--------------
Contiene el analizador sintáctico y estructuras de AST para el lenguaje CAOS.
"""

from .ast_nodes import (
    ASTNode, Programa, ListaDeclaracion, Declaracion, DeclaracionVariable,
    ListaSentencias, Sentencia, Asignacion, IncrementoDecremento,
    Seleccion, Iteracion, Repeticion,
    EntradaEstandar, SalidaEstandar, Salida,
    Expresion, ExpresionSimple, Termino, Factor, Componente,
    Numero, Identificador, Cadena, Booleano, NodoError
)
from .parser import Parser, Token, SyntaxError
from .ast_formatter import ASTFormatter

__all__ = [
    'Parser', 'Token', 'SyntaxError',
    'ASTFormatter',
    'ASTNode', 'Programa', 'ListaDeclaracion', 'Declaracion', 'DeclaracionVariable',
    'ListaSentencias', 'Sentencia', 'Asignacion', 'IncrementoDecremento',
    'Seleccion', 'Iteracion', 'Repeticion',
    'EntradaEstandar', 'SalidaEstandar', 'Salida',
    'Expresion', 'ExpresionSimple', 'Termino', 'Factor', 'Componente',
    'Numero', 'Identificador', 'Cadena', 'Booleano', 'NodoError'
]

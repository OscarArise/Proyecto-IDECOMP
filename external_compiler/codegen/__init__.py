"""
Generación de código del compilador CAOS (Fase 4).

    from codegen import code_gen, generar_codigo_intermedio

    tm = code_gen(resultado.arbol_anotado, resultado.tabla, "programa.caos")
    ci = generar_codigo_intermedio(resultado.arbol_anotado, "programa.caos")

Ambas salidas parten del mismo árbol anotado por el análisis semántico y se
producen por caminos paralelos: el .ci no es la entrada de la TM.
"""

from .cgen import ErrorGeneracion, code_gen
from .intermedio import generar_codigo_intermedio

__all__ = ["code_gen", "generar_codigo_intermedio", "ErrorGeneracion"]

"""
formateador.py
--------------
Salidas de texto del análisis semántico.

    semantic_txt(resultado)   contenido de semantic.txt: resumen, árbol anotado,
                              recorrido semántico, errores y el JSON del árbol
                              anotado (mismo marcador que syntax.txt, para que
                              el IDE lo cargue con el mismo visor).
    symbols_txt(tabla)        contenido de symbols.txt
    errores_txt(errores)      una línea por error, con prefijo [SEMANTICO]
"""

import json
from typing import Any, Dict, List, Optional

from .analizador import ResultadoSemantico, formatear_valor
from .errores import ErrorSemantico
from .tabla_simbolos import TablaSimbolos

SEPARADOR = "-" * 72


def arbol_a_texto(nodo: Optional[Dict[str, Any]], nivel: int = 0) -> str:
    if not nodo:
        return ""
    sangria = "  " * nivel
    etiqueta = nodo.get("label") or nodo.get("type", "")
    linea, columna = nodo.get("linea", 0), nodo.get("columna", 0)
    ubicacion = f" [L{linea}:C{columna}]" if linea else ""
    texto = f"{sangria}{etiqueta}{ubicacion}\n"
    for hijo in nodo.get("children", []):
        texto += arbol_a_texto(hijo, nivel + 1)
    return texto


def tabla_a_texto(tabla: TablaSimbolos) -> str:
    simbolos = tabla.simbolos()
    if not simbolos:
        return "(tabla vacía)\n"
    filas = [("Nombre", "Tipo", "Loc", "Hash", "Declarada", "Valor final", "Líneas")]
    for s in simbolos:
        filas.append((
            s.nombre,
            s.tipo,
            str(s.loc),
            str(s.hash),
            f"{s.linea_decl}:{s.columna_decl}",
            formatear_valor(s.valor) if s.valor is not None else "desconocido",
            ", ".join(str(n) for n in s.lineas),
        ))
    anchos = [max(len(f[i]) for f in filas) for i in range(len(filas[0]))]

    def fila(valores):
        return "  ".join(v.ljust(anchos[i]) for i, v in enumerate(valores)).rstrip() + "\n"

    texto = fila(filas[0])
    texto += "  ".join("-" * a for a in anchos) + "\n"
    for f in filas[1:]:
        texto += fila(f)
    return texto


def symbols_txt(tabla: TablaSimbolos) -> str:
    return (
        "Tabla de Símbolos\n"
        + "=" * 50 + "\n"
        + "Tabla hash con encadenamiento (SIZE = 211, función hash de TINY).\n"
        + "Ámbito único: bloque main.\n"
        + "Líneas: una por cada aparición del identificador (se repite si aparece\n"
        + "varias veces en la misma línea). Valor final: último valor conocido en\n"
        + "compilación ('desconocido' si depende de la ejecución).\n\n"
        + tabla_a_texto(tabla)
        + f"\nTotal de identificadores: {len(tabla)}\n"
    )


def errores_txt(errores: List[ErrorSemantico]) -> str:
    return "".join(f"[SEMANTICO] {e}\n" for e in errores)


def semantic_txt(resultado: ResultadoSemantico) -> str:
    errores = resultado.errores
    texto = "Análisis Semántico\n" + "=" * 50 + "\n\n"
    texto += "Resumen:\n" + SEPARADOR + "\n"
    texto += f"  Identificadores en la tabla: {len(resultado.tabla)}\n"
    texto += f"  Conversiones implícitas aplicadas: {resultado.conversiones}\n"
    texto += f"  Errores semánticos: {len(errores)}\n\n"

    texto += "Árbol con anotaciones semánticas:\n" + SEPARADOR + "\n"
    texto += arbol_a_texto(resultado.arbol_anotado) + "\n"

    texto += "Recorrido semántico:\n" + SEPARADOR + "\n"
    texto += "".join(f"  {paso}\n" for paso in resultado.traza) + "\n"

    texto += "Errores semánticos:\n" + SEPARADOR + "\n"
    if errores:
        texto += "".join(f"  {e}\n" for e in errores)
    else:
        texto += "  Sin errores semánticos.\n"
    texto += "\n"

    texto += "Representación estructurada (para visualización):\n" + SEPARADOR + "\n"
    texto += json.dumps(resultado.arbol_anotado, indent=2, ensure_ascii=False)
    texto += "\n"
    return texto

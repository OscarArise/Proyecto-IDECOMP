"""
semantic_output.py
------------------
Utilidades (sin Tkinter) para trabajar con la salida del compilador:

    extract_ast_dict(salida)      AST (dict) de la sección "Representación
                                  estructurada" de syntax.txt o semantic.txt.
    split_semantic_output(salida) (texto_legible, ast_anotado): el texto de
                                  semantic.txt sin el JSON, y el árbol anotado.
    error_text_for_editor(...)    errores de todas las fases con posición, para
                                  marcarlos en el editor.
"""

import json
from typing import Optional, Tuple

MARCADOR = "Representación estructurada"


def extract_ast_dict(salida: str) -> Optional[dict]:
    """Devuelve el AST serializado en `salida`, o None si no hay JSON válido."""
    if not salida or not salida.strip():
        return None
    inicio = salida.find(MARCADOR)
    llave = salida.find("{", inicio if inicio >= 0 else 0)
    if llave < 0:
        return None
    try:
        ast, _ = json.JSONDecoder().raw_decode(salida[llave:])
    except json.JSONDecodeError:
        return None
    return ast if isinstance(ast, dict) else None


def split_semantic_output(salida: str) -> Tuple[str, Optional[dict]]:
    """
    Separa semantic.txt en (texto legible, árbol anotado).

    El JSON del árbol anotado ocupa la mayor parte del archivo y es solo para
    el visor; la pestaña de texto muestra únicamente lo legible.
    """
    if not salida:
        return "", None
    corte = salida.find(MARCADOR)
    texto = salida if corte < 0 else salida[:corte].rstrip() + "\n"
    return texto, extract_ast_dict(salida)


def error_text_for_editor(errors_by_phase: dict) -> str:
    """Une los errores léxicos, sintácticos y semánticos (con posición)."""
    partes = [
        errors_by_phase.get(clave, "")
        for clave in ("err_lexico", "err_sintactico", "err_semantico")
    ]
    return "\n".join(p for p in partes if p.strip())

import argparse
import sys
from pathlib import Path


# Fases

PHASES = ["lexico", "sintactico", "semantico", "intermedio", "ejecutar"]

# Archivos de salida
OUTPUT_FILES = {
    "lexico":     "tokens.txt",
    "sintactico": "syntax.txt",
    "semantico":  "semantic.txt",
    "intermedio": "intermediate.txt",
    "ejecutar":   "exec.txt",
    "simbolos":   "symbols.txt",
    "errors":     "errors.txt",
}


# Punto de entrada

def main():
    parser = argparse.ArgumentParser(
        description="Compilador stub del IDE CAOS"
    )
    parser.add_argument(
        "source",
        help="Ruta al archivo fuente .caos"
    )
    parser.add_argument(
        "--phase",
        choices=PHASES,
        default=None,
        help="Ejecutar solo hasta esta fase (por defecto: todas)"
    )
    args = parser.parse_args()

    source_path = Path(args.source)
    if not source_path.exists():
        _write("errors.txt", f"[LEXICO] Archivo fuente no encontrado: {source_path}\n")
        sys.exit(1)

    source_code = source_path.read_text(encoding="utf-8", errors="replace")
    target_phase = args.phase or "ejecutar"
    phases_to_run = PHASES[: PHASES.index(target_phase) + 1]

    errors: list[str] = []

    # Limpiar archivos anteriores
    for fname in OUTPUT_FILES.values():
        Path(fname).write_text("", encoding="utf-8")

    # Fase 1: Léxico
    if "lexico" in phases_to_run:
        tokens = _run_lexico(source_code, errors)
        _write(OUTPUT_FILES["lexico"], _format_tokens(tokens))
        _write(OUTPUT_FILES["errors"], "\n".join(errors) + ("\n" if errors else ""))

    if errors:
        sys.exit(1)

    # Fase 2: Sintáctico
    if "sintactico" in phases_to_run:
        ast_text = _run_sintactico(source_code, tokens, errors)
        _write(OUTPUT_FILES["sintactico"], ast_text)

    if errors:
        _write(OUTPUT_FILES["errors"], "\n".join(errors))
        sys.exit(2)

    # Fase 3: Semántico
    if "semantico" in phases_to_run:
        symbol_table, semantic_info = _run_semantico(source_code, tokens, errors)
        _write(OUTPUT_FILES["semantico"], semantic_info)
        _write(OUTPUT_FILES["simbolos"], symbol_table)

    if errors:
        _write(OUTPUT_FILES["errors"], "\n".join(errors))
        sys.exit(3)

    # Fase 4: Código Intermedio
    if "intermedio" in phases_to_run:
        intermediate = _run_intermedio(errors)
        _write(OUTPUT_FILES["intermedio"], intermediate)

    if errors:
        _write(OUTPUT_FILES["errors"], "\n".join(errors))
        sys.exit(4)

    # Fase 5: Ejecución
    if "ejecutar" in phases_to_run:
        exec_output = _run_ejecutar(errors)
        _write(OUTPUT_FILES["ejecutar"], exec_output)

    if errors:
        _write(OUTPUT_FILES["errors"], "\n".join(errors))
        sys.exit(5)

    # Sin errores
    _write(OUTPUT_FILES["errors"], "")
    sys.exit(0)


# Implementaciones stub de cada fase
# (serán reemplazadas por el compilador real)

def _run_lexico(source: str, errors: list) -> list[tuple]:
    """
    Analizador léxico real basado en DFA.

    Delega completamente al DFALexer definido en lexer/dfa_lexer.py,
    el cual implementa el autómata de automata.md estado por estado.

    Retorna una lista de tuplas (tipo, valor, línea, columna) compatible
    con el resto del pipeline del compilador.

    Los tokens de tipo ERROR se excluyen de la lista de tokens válidos y
    sus mensajes se propagan al listado de `errors`.

    TODO: cuando se implemente el reporte a errors.txt con línea/columna,
          los mensajes de errors[] de aquí deben escribirse en ese archivo.
    """
    import sys
    import os
    # Asegurar que el directorio external_compiler esté en el path
    # para que Python resuelva el subpaquete lexer/
    _ec_dir = os.path.dirname(os.path.abspath(__file__))
    if _ec_dir not in sys.path:
        sys.path.insert(0, _ec_dir)

    from lexer.dfa_lexer import DFALexer

    lexer = DFALexer()
    raw_tokens, lex_errors = lexer.tokenize(source)

    # Propagar errores léxicos al listado general de errores
    errors.extend(lex_errors)

    # Convertir Token dataclass → tupla, excluyendo ERROR y EOF
    result = []
    for tok in raw_tokens:
        if tok.tipo in ("ERROR", "EOF"):
            continue
        result.append((tok.tipo, tok.valor, tok.linea, tok.columna))

    return result


def _format_tokens(tokens: list[tuple]) -> str:
    if not tokens:
        return "(sin tokens)\n"
    header = f"{'#':<5} {'TIPO':<15} {'VALOR':<20} {'LÍN':>5} {'COL':>5}\n"
    sep    = "-" * 50 + "\n"
    rows   = "".join(
        f"{i:<5} {t:<15} {v:<20} {ln:>5} {col:>5}\n"
        for i, (t, v, ln, col) in enumerate(tokens, 1)
    )
    return header + sep + rows


def _run_sintactico(source: str, tokens: list, errors: list) -> str:
    """Stub: retorna una representación textual plana del árbol."""
    return (
        "Árbol Sintáctico (stub)\n"
        "=======================\n"
        f"  Tokens procesados: {len(tokens)}\n"
        "  [Implementación real pendiente]\n"
    )


def _run_semantico(source: str, tokens: list, errors: list) -> tuple[str, str]:
    """
    Stub: retorna (tabla_de_simbolos, info_semantica).
    """
    idents = {v for t, v, *_ in tokens if t == "IDENT"}
    symbol_table = (
        "Tabla de Símbolos (stub)\n"
        "========================\n"
        + "\n".join(f"  {name}" for name in sorted(idents))
        + "\n"
    )
    semantic_info = (
        "Análisis Semántico (stub)\n"
        "=========================\n"
        f"  Identificadores encontrados: {len(idents)}\n"
        "  [Implementación real pendiente]\n"
    )
    return symbol_table, semantic_info


def _run_intermedio(errors: list) -> str:
    return (
        "Código Intermedio (stub)\n"
        "========================\n"
        "  [Implementación real pendiente]\n"
    )


def _run_ejecutar(errors: list) -> str:
    return (
        "Ejecución (stub)\n"
        "================\n"
        "  [Implementación real pendiente]\n"
    )


#Util

def _write(filename: str, content: str):
    Path(filename).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()

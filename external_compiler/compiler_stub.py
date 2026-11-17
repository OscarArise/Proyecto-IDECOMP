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
    "tm":         "code.tm",
    "ci":         "code.ci",
}


# Punto de entrada

def main():
    parser = argparse.ArgumentParser(
        description="Compilador del IDE CAOS"
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
    tokens: list = []
    ast = None

    # Limpiar archivos anteriores
    for fname in OUTPUT_FILES.values():
        Path(fname).write_text("", encoding="utf-8")

    # Fase 1: Léxico
    if "lexico" in phases_to_run:
        tokens = _run_lexico(source_code, errors)
        _write(OUTPUT_FILES["lexico"], _format_tokens(tokens))
        _write_errors(errors)

    if errors:
        sys.exit(1)

    # Fase 2: Sintáctico
    if "sintactico" in phases_to_run:
        ast_text, ast = _run_sintactico(source_code, tokens, errors)
        _write(OUTPUT_FILES["sintactico"], ast_text)

    if errors:
        _write_errors(errors)
        sys.exit(2)

    # Fase 3: Semántico
    if "semantico" in phases_to_run:
        symbol_table, semantic_info = _run_semantico(ast, errors)
        _write(OUTPUT_FILES["semantico"], semantic_info)
        _write(OUTPUT_FILES["simbolos"], symbol_table)

    if errors:
        _write_errors(errors)
        sys.exit(3)

    # Fase 4: Código Intermedio (.ci) y código objetivo TM (.tm)
    if "intermedio" in phases_to_run:
        tm_code, ci_code = _run_generacion(ast, source_path, errors)
        _write(OUTPUT_FILES["tm"], tm_code)
        _write(OUTPUT_FILES["ci"], ci_code)
        _write(OUTPUT_FILES["intermedio"], tm_code)

    if errors:
        _write_errors(errors)
        sys.exit(4)

    # Fase 5: Ejecución
    if "ejecutar" in phases_to_run:
        exec_output = _run_ejecutar(errors)
        _write(OUTPUT_FILES["ejecutar"], exec_output)

    if errors:
        _write_errors(errors)
        sys.exit(5)

    # Sin errores
    _write(OUTPUT_FILES["errors"], "")
    sys.exit(0)


# Implementación de cada fase
# Léxico, sintáctico y semántico (fases 1-3, validadas) no se modifican en la
# fase 4; la generación de código solo consume sus resultados.

def _run_lexico(source: str, errors: list) -> list[tuple]:
    """
    Analizador léxico real basado en DFA.

    Delega completamente al DFALexer definido en lexer/dfa_lexer.py,
    el cual implementa el autómata de automata.md estado por estado.

    Retorna una lista de tuplas (tipo, valor, línea, columna) compatible
    con el resto del pipeline del compilador.

    Los tokens de tipo ERROR se excluyen de la lista de tokens válidos y
    sus mensajes se propagan al listado de `errors`, que `_write_errors`
    vuelca en errors.txt con línea y columna.
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


def _run_sintactico(source: str, tokens: list, errors: list) -> tuple[str, object]:
    """
    Analizador sintáctico real basado en parser descendente recursivo.
    
    Procesa los tokens generados por el analizador léxico y construye
    un Árbol Sintáctico Abstracto (AST) según la gramática de la Fase 2.

    Retorna (texto_de_syntax.txt, ast). El AST se entrega a la fase semántica.
    """
    import sys
    import os
    import json
    
    # Asegurar que el directorio external_compiler esté en el path
    _ec_dir = os.path.dirname(os.path.abspath(__file__))
    if _ec_dir not in sys.path:
        sys.path.insert(0, _ec_dir)

    from parser.parser import Parser
    from parser.ast_formatter import ASTFormatter

    # Crear el parser con los tokens
    parser = Parser(tokens)
    
    # Realizar el análisis sintáctico
    ast, syntax_errors = parser.parse()
    
    # Propagar errores sintácticos al listado general
    for error in syntax_errors:
        errors.append(f"[SINTACTICO] {str(error)}")
    
    # Generar salida formateada
    result = "Árbol Sintáctico Abstracto (AST)\n"
    result += "=" * 50 + "\n\n"
    
    if ast:
        # Incluir representación textual del AST
        result += "Representación de texto:\n"
        result += "-" * 50 + "\n"
        result += ASTFormatter.to_text(ast)
        result += "\n"
        
        # Incluir representación como diccionario (JSON-ready) para la visualización gráfica
        result += "Representación estructurada (para visualización):\n"
        result += "-" * 50 + "\n"
        ast_dict = ASTFormatter.to_dict(ast)
        result += json.dumps(ast_dict, indent=2, ensure_ascii=False)
    else:
        result += "No se pudo construir el AST debido a errores sintácticos.\n"
    
    # Agregar reporte de errores al final
    if syntax_errors:
        result += "\n" + ASTFormatter.format_errors(syntax_errors)
    else:
        result += "\nSin errores sintácticos.\n"
    
    return result, ast


def _run_semantico(ast, errors: list) -> tuple[str, str]:
    """
    Análisis semántico real (Fase 3).

    Recibe el AST del sintáctico, lo convierte a su forma binaria y llama a
    `semantic.analizar`, que trabaja sobre una copia anotada y deja el original
    intacto. Retorna (symbols.txt, semantic.txt) y agrega los errores
    semánticos con el prefijo [SEMANTICO] a `errors`.
    """
    import os

    _ec_dir = os.path.dirname(os.path.abspath(__file__))
    if _ec_dir not in sys.path:
        sys.path.insert(0, _ec_dir)

    from parser.ast_formatter import ASTFormatter
    from semantic import analizar
    from semantic.formateador import semantic_txt, symbols_txt

    resultado = analizar(ASTFormatter.to_binary(ast))
    errors.extend(f"[SEMANTICO] {e}" for e in resultado.errores)
    return symbols_txt(resultado.tabla), semantic_txt(resultado)


def _run_generacion(ast, source_path: Path, errors: list) -> tuple[str, str]:
    """
    Generación de código (Fase 4).

    Obtiene el árbol anotado y la tabla de símbolos con la API pública del
    análisis semántico (el mismo análisis, determinista, que ya validó la fase
    3) y produce por caminos paralelos:
        code.tm  instrucciones para la TM (codegen/cgen.py + codegen/code.py)
        code.ci  código de tres direcciones (codegen/intermedio.py)
    Retorna (texto_tm, texto_ci). Los fallos se reportan con [GENERACION].
    """
    import os
    from datetime import datetime

    _ec_dir = os.path.dirname(os.path.abspath(__file__))
    if _ec_dir not in sys.path:
        sys.path.insert(0, _ec_dir)

    from parser.ast_formatter import ASTFormatter
    from semantic import analizar
    from codegen import ErrorGeneracion, code_gen, generar_codigo_intermedio

    resultado = analizar(ASTFormatter.to_binary(ast))
    if resultado.errores:
        errors.extend(f"[GENERACION] El árbol no es válido: {e}" for e in resultado.errores)
        return "", ""

    encabezado = [
        f"Fuente: {source_path.resolve()}",
        f"Compilado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    try:
        tm_code = code_gen(resultado.arbol_anotado, resultado.tabla, source_path.name, encabezado)
        ci_code = generar_codigo_intermedio(resultado.arbol_anotado, source_path.name, encabezado)
    except ErrorGeneracion as exc:
        errors.append(f"[GENERACION] {exc}")
        return "", ""
    return tm_code, ci_code


def _run_ejecutar(errors: list) -> str:
    """
    La ejecución es interactiva (las instrucciones IN piden datos), así que la
    realiza el simulador TM (tm/tm.py en el IDE o tm/tm.exe en consola) sobre
    el code.tm que generó la fase 4.
    """
    return (
        "Código TM generado en code.tm.\n"
        "Ejecútelo en el simulador TM: tm/tm.py (IDE) o tm/tm.exe code.tm (consola).\n"
    )


#Util

def _write(filename: str, content: str):
    Path(filename).write_text(content, encoding="utf-8")


def _write_errors(errors: list[str]):
    """Escribe errors.txt con una línea por error y salto de línea final."""
    contenido = "\n".join(errors) + "\n" if errors else ""
    _write(OUTPUT_FILES["errors"], contenido)


if __name__ == "__main__":
    main()

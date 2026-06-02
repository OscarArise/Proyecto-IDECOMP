#!/usr/bin/env python3
"""
Script de prueba para el analizador sintáctico.
"""

import sys
import os

# Agregar el directorio external_compiler al path
_ec_dir = os.path.dirname(os.path.abspath(__file__))
if _ec_dir not in sys.path:
    sys.path.insert(0, _ec_dir)

from lexer.dfa_lexer import DFALexer
from parser.parser import Parser
from parser.ast_formatter import ASTFormatter

# Código de prueba
test_code = """
main {
    int x;
    x = 5;
}
"""

print("=" * 60)
print("PRUEBA DEL ANALIZADOR SINTÁCTICO")
print("=" * 60)
print("\nCódigo fuente:")
print(test_code)

# Fase 1: Análisis Léxico
print("\n" + "=" * 60)
print("FASE 1: ANÁLISIS LÉXICO")
print("=" * 60)

lexer = DFALexer()
raw_tokens, lex_errors = lexer.tokenize(test_code)

print(f"\nTokens encontrados: {len(raw_tokens)}")
for tok in raw_tokens[:10]:  # Mostrar los primeros 10
    print(f"  {tok}")

if lex_errors:
    print(f"\nErrores léxicos: {len(lex_errors)}")
    for error in lex_errors:
        print(f"  {error}")

# Convertir a tuplas para el parser
tokens = [(tok.tipo, tok.valor, tok.linea, tok.columna) 
          for tok in raw_tokens if tok.tipo not in ("ERROR", "EOF")]

# Fase 2: Análisis Sintáctico
print("\n" + "=" * 60)
print("FASE 2: ANÁLISIS SINTÁCTICO")
print("=" * 60)

parser = Parser(tokens)
ast, syntax_errors = parser.parse()

print(f"\nErrores sintácticos: {len(syntax_errors)}")
if syntax_errors:
    for error in syntax_errors:
        print(f"  {error}")

if ast:
    print("\nÁrbol Sintáctico (texto):")
    print("-" * 60)
    print(ASTFormatter.to_text(ast))
    
    print("\nÁrbol Sintáctico (estructura):")
    print("-" * 60)
    import json
    ast_dict = ASTFormatter.to_dict(ast)
    print(json.dumps(ast_dict, indent=2, ensure_ascii=False))
else:
    print("\nNo se pudo construir el AST")

print("\n" + "=" * 60)
print("FIN DE LA PRUEBA")
print("=" * 60)

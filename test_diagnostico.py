#!/usr/bin/env python3
"""
Script de diagnóstico para verificar la salida del compilador sintáctico.
"""

import sys
import os

# Asegurar que el directorio external_compiler esté en el path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
compiler_dir = os.path.join(project_root, "external_compiler")
sys.path.insert(0, compiler_dir)

# Crear un archivo de prueba
test_code = """main {
    int x;
    x = 5;
}"""

test_file = os.path.join(project_root, "test_temp.caos")
with open(test_file, "w") as f:
    f.write(test_code)

print("Archivo de prueba creado:", test_file)
print("Contenido:")
print(test_code)
print("\n" + "="*60)

# Ejecutar el compilador
from external_compiler.compiler_stub import _run_lexico, _run_sintactico

# Fase 1: Léxico
print("FASE 1: ANÁLISIS LÉXICO")
print("="*60)
errors = []
tokens = _run_lexico(test_code, errors)
print(f"Tokens: {len(tokens)}")
for tok in tokens:
    print(f"  {tok}")

# Fase 2: Sintáctico
print("\n" + "="*60)
print("FASE 2: ANÁLISIS SINTÁCTICO")
print("="*60)
syntax_output = _run_sintactico(test_code, tokens, errors)
print(syntax_output)

# Limpiar
os.remove(test_file)
print("\nArchivo temporal eliminado.")

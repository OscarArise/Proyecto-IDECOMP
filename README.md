# Proyecto IDECOMP — IDE y compilador del lenguaje CAOS

Proyecto de Compiladores II (UAA). IDE en Python/Tkinter con un compilador por fases para el lenguaje CAOS.

| Fase | Estado | Código |
|---|---|---|
| 1. Léxico | Completa | `external_compiler/lexer/` |
| 2. Sintáctico (AST) | Completa | `external_compiler/parser/` |
| 3. Semántico (tabla de símbolos, tipos) | Completa | `external_compiler/semantic/` |
| Código intermedio / ejecución | Stubs (fases futuras) | `external_compiler/compiler_stub.py` |

## Requisitos

Python 3.10+ con Tkinter. Para regenerar el PDF de entrega: `pip install -r requirements.txt`.

## Uso

```
python ide/main.py        # abre el IDE (F5 léxico, F6 sintáctico, F7 semántico)
```

Línea de comandos (desde `external_compiler/`):

```
python compiler_stub.py ../pruebas/TestSemantica.txt --phase semantico
```

Códigos de salida: 0 ok, 1 léxico, 2 sintáctico, 3 semántico. Ver `external_compiler/README_run.txt`.

## Pruebas

```
cd external_compiler
python -m unittest test_semantico test_integracion test_parser_recovery
cd ../ide
python -m unittest test_semantic_output
```

## Estructura

- `ide/` — interfaz gráfica (editor, paneles, visor de árboles).
- `external_compiler/` — compilador (lexer, parser, semantic) y sus pruebas.
- `pruebas/` — programas de prueba; `TestSemantica.txt` es la prueba oficial de la Fase 3.
- `docs/` — documentación por bloque e `informe-fase3.md` (construcción, decisiones y demostración).
- `entrega/` — entregables de la Fase 3 (salidas, capturas, PDF y su generador).

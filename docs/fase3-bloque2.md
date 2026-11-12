# Fase 3 · Bloque 2 — Núcleo semántico

Base: rama `B` (commit `0a27649`). Rama de trabajo: `fase3/b2-semantico`.

Este documento es para el **Bloque 3 (integración, IDE y entregables)** y para
el PDF de la fase. Resume qué hace el analizador, qué decisiones se tomaron y
qué falta conectar.

---

## 1. Estado

El paquete `external_compiler/semantic/` está completo y probado:

```
cd external_compiler
python -m unittest test_semantico test_parser_recovery    # 49 pruebas
```

Con `pruebas/TestSemantica.txt` produce exactamente los **6 errores esperados**
y la tabla de símbolos esperada:

| Línea:col | Código | Mensaje |
| --- | --- | --- |
| 4:5 | E1 | 'suma' no está declarada |
| 5:5 | E4 | No se puede asignar un valor float a 'x', que es int |
| 14:5 | E4 | No se puede asignar un valor float a 'y', que es int |
| 16:9 | E4 | No se puede asignar un valor float a 'y', que es int |
| 33:13 | E1 | 'mas' no está declarada |
| 37:13 | E1 | 'mas' no está declarada |

| Nombre | Tipo | Loc | Líneas |
| --- | --- | --- | --- |
| x | int | 0 | 2, 5, 6, 11, 27, 30, 31, 32, 38 |
| y | int | 1 | 2, 7, 8, 9, 12, 14, 16, 23, 29, 35, 36 |
| z | int | 2 | 2, 8, 13 |
| a | float | 3 | 3, 10, 16, 25 |
| b | float | 4 | 3, 19, 21 |
| c | float | 5 | 3, 26 |

**Ya está conectado al compilador** (Bloque 3): `compiler_stub.py::_run_semantico`
llama a `semantic.analizar` con el AST del parser. Ver `docs/fase3-bloque3.md`.

---

## 2. Archivos

```
external_compiler/semantic/__init__.py         API pública: analizar()
external_compiler/semantic/tipos.py            tipos y reglas de compatibilidad
external_compiler/semantic/errores.py          códigos E1–E7 y ErrorSemantico
external_compiler/semantic/tabla_simbolos.py   tabla hash con encadenamiento
external_compiler/semantic/analizador.py       recorrido, atributos y verificación
external_compiler/semantic/formateador.py      semantic.txt, symbols.txt, errores
external_compiler/test_semantico.py            30 pruebas
```

---

## 3. Cómo se usa

```python
from parser.ast_formatter import ASTFormatter
from semantic import analizar
from semantic.formateador import semantic_txt, symbols_txt, errores_txt

resultado = analizar(ASTFormatter.to_binary(ast))

resultado.arbol_original    # el AST del sintáctico, sin tocar
resultado.arbol_anotado     # copia del AST con las anotaciones
resultado.tabla             # TablaSimbolos
resultado.errores           # lista de ErrorSemantico (codigo, mensaje, linea, columna)
resultado.traza             # recorrido semántico paso a paso
resultado.conversiones      # cuántas conversiones int → float se aplicaron
```

---

## 4. Diseño

### 4.1 Tabla de símbolos

Es la tabla de TINY (la misma de `TablaHash_Probar.cpp`): tamaño 211, función
hash `temp = ((temp << 4) + c) % 211` y encadenamiento separado para las
colisiones. Se extendió con el tipo y la posición de la declaración.

| Campo | Contenido |
| --- | --- |
| `nombre` | lexema |
| `tipo` | `int`, `float` o `bool` (viene del atributo heredado `dtype`) |
| `loc` | desplazamiento de memoria: 0, 1, 2… en orden de declaración, como `location` en TINY |
| `linea_decl`, `columna_decl` | dónde se declaró |
| `lineas` | línea de la declaración y de cada uso, sin repetir |
| `siguiente` | siguiente símbolo de la misma cubeta |

Operaciones: `insertar`, `buscar`, `agregar_linea`, `eliminar`, `simbolos`.
Un solo ámbito, porque el lenguaje solo tiene el bloque `main`. `eliminar` no la
usa el análisis, pero está implementada y probada porque la guía la menciona.

Las variables no declaradas **no se insertan**: se reporta E1 en cada uso.

### 4.2 Recorrido

Un solo recorrido del árbol, en el orden del programa:

- **Declaración → inserción** (preorden, atributo heredado). El `dtype` de la
  declaración se propaga a cada identificador y se inserta en la tabla. Si ya
  existía: E2.
- **Uso de identificador → búsqueda.** Se agrega la línea a la tabla. Si no
  existe: E1.
- **Expresión → tipos** (postorden, atributos sintetizados). Primero los hijos,
  luego el padre.
- **Asignación → comparación** del tipo de la variable con el de la expresión.

Como el recorrido sigue el orden del programa, usar una variable antes de su
declaración es E1.

### 4.3 Reglas de tipos

| Operador | Operandos válidos | Resultado | Si no |
| --- | --- | --- | --- |
| `+ - * / ^` | int, float | int si ambos son int; float si alguno es float | E5 |
| `%` | int, int | int | E5 |
| `< <= > >=` | int, float | bool | E5 |
| `== !=` | numérico con numérico, o bool con bool | bool | E3 |
| `&& \|\|` | bool, bool | bool | E5 |
| `!` | bool | bool | E5 |
| `id = expr` | mismo tipo, o float ← int | — | E4 si int ← float; E6 si mezcla bool y número |
| `id++`, `id--` | int, float | — | E5 |
| condición de `if`, `while`, `until` | bool | — | E7 |

**División entre enteros:** `int / int` da `int` y **trunca hacia cero**, como en
C. La guía (sección 7) solo pide conversión cuando los operandos son de tipos
diferentes; con dos `int` no hay conversión. Con división real, las líneas 11,
12, 13 y 31 del test darían cuatro E4 que el archivo no busca provocar.

**Conversión:** la única implícita es int → float, al combinar un int con un
float o al asignar un int a una variable float. float → int y cualquier
conversión con bool no son válidas.

### 4.4 Atributo de valor

Se calcula solo cuando todos los operandos son constantes (`2 + 3 - 1` → 4). Si
interviene un identificador, el valor queda sin determinar: la guía pide no
forzarlo. Una división entre una constante cero tampoco se pliega.

### 4.5 Errores en cascada

Un nodo con error recibe el tipo interno `error`. Cualquier operación con un
operando `error` no genera errores nuevos. Por eso `x = (y + 1.5) * 2` con `y`
no declarada da un solo E1, y no un E1 más un E4.

---

## 5. El árbol anotado

`arbol_anotado` es una **copia** (`deepcopy`) del árbol del sintáctico; el
original no se modifica (hay una prueba que lo verifica). Así se pueden mostrar
lado a lado, como pide la guía en la sección 5.

### Claves que se agregan

| Clave | Dónde | Contenido |
| --- | --- | --- |
| `tipo_dato` | expresiones, asignaciones, `cin`, `++`/`--` | tipo calculado |
| `atributo_tipo` | expresiones e identificadores declarados | `sintetizado` o `heredado` |
| `valor_calculado` | expresiones constantes | valor en compilación |
| `dtype` | declaraciones e identificadores declarados | tipo heredado |
| `loc` | identificadores | localidad en la tabla |
| `tipo_expresion`, `verificacion` | asignaciones | tipo de la expresión; `compatible`, `conversion` o `error` |
| `tipo_requerido` | secciones `CONDICION*` | siempre `bool` |
| `errores_semanticos` | nodo que causó un error | lista de códigos |
| `label_sintactico` | todo nodo anotado | etiqueta original del sintáctico |

`label` se reescribe con las anotaciones, por lo que el visor del IDE las
muestra sin cambios:

```
ASIGNACION: x  ⟨x: int, expresión: float, ✗ E4⟩
OPERACION: +  ⟨tipo: float, valor: 28.0⟩
```

**No se usa la clave `valor`** en nodos nuevos: `ast_tree_viewer.py` le agrega
`(valor)` a la etiqueta de cualquier nodo que la tenga.

### Nodos nuevos

- **`IdentificadorDeclarado`**: hijos de cada `DeclaracionVariable`, uno por
  variable, con su `dtype` heredado y su `loc`. Hacen visible la propagación del
  atributo heredado.
- **`ConversionTipo`**: envuelve al operando que se convirtió de int a float,
  con claves `de` y `a`. Por ejemplo, en la línea 10 aparecen cuatro.

---

## 6. Pendiente para el Bloque 3 (resuelto)

Los cuatro puntos de esta sección se completaron en el Bloque 3: conexión de
`_run_semantico` con el AST (exit code 3 si hay errores semánticos), visor del
árbol anotado y comparación en el IDE, marcado de errores semánticos en el
editor, y capturas/PDF en `entrega/`. Detalle en `docs/fase3-bloque3.md` e
`docs/informe-fase3.md`.

---

## 7. Cambio en el parser

Se encontró un error que ya existía en `master`: el parser rechazaba una
declaración que viniera después de una sentencia (`int x; x = 1; int y;`), aunque
la gramática (`programa ::= "main" "{" { declaracion } "}"`) lo permite. La
lista de sentencias no se detenía al encontrar un tipo.

Se corrigió en `Parser._declaracion` con una línea: la lista de sentencias se
detiene en `int`, `float`, `real` o `bool`. Las 19 pruebas del parser siguen
pasando y todos los archivos de `pruebas/` y `ide/samples/` dan los mismos
errores que antes. `TestSemantica.txt` no cambia.

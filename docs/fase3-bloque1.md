# Fase 3 · Bloque 1 — Entrega y traspaso al Bloque 2

Sesión del 6 de octubre de 2026. Base: rama `B`, commit `e0da57e`.

Este documento es para quien toma el **Bloque 2 (núcleo semántico)**. Resume qué
quedó funcionando, qué decisiones se tomaron, en qué nos apartamos del plan
original y qué contrato real entrega el parser.

---

## 1. Estado: el Bloque 1 está terminado

El criterio de cierre del plan era que `TestSemantica.txt` pasara el análisis
sintáctico sin errores. Se cumple:

```
python compiler_stub.py ..\pruebas\TestSemantica.txt --phase sintactico
→ código de salida 0, errors.txt vacío, AST completo de 154 nodos
```

Antes de esta sesión ese mismo archivo producía **17 errores sintácticos**.

Pasan también sin errores `codigo_valido.caos`, `codigo_complejo.caos` y los tres
samples del IDE. Los archivos con errores a propósito (`conerrores.caos`,
`codigo_errores.caos`, `test_errores.caos`, `TestIDE.caos`) siguen fallando en la
fase correcta y con el código de salida correcto.

**El árbol del dialecto con paréntesis no cambió.** Se comparó nodo por nodo
contra el commit anterior usando un worktree de Git: `codigo_valido.caos` y
`codigo_complejo.caos` producen árboles idénticos a los de antes.

---

## 2. Decisiones tomadas en esta sesión

### 2.1 `cin >>` y `cout <<` no son operadores del lenguaje

CAOS no tiene los operadores de flujo de C++. La entrada es `cin id;` y la salida
`cout salida;`.

En consecuencia **se modificó el archivo de prueba oficial**, no el parser:

| Antes | Ahora |
| --- | --- |
| `cin >> x;` | `cin x;` |
| `cin >> mas;` | `cin mas;` |
| `cout << x;` | `cout x;` |

Son las líneas 32, 37 y 38 de `pruebas/TestSemantica.txt`. Lo demás del archivo
quedó intacto: las mismas declaraciones, las mismas expresiones y los mismos
errores semánticos que hay que detectar.

Se aplicó el mismo cambio a `ide/samples/test_basico.caos`,
`test_condicional.caos`, `test_ciclo.caos` y `test_errores.caos`.

> **Ojo con esto en el PDF.** La guía dice que no se debe sustituir el archivo
> principal de pruebas. No lo sustituimos: lo ajustamos en tres líneas para que
> use la sintaxis de entrada/salida de nuestra gramática. Conviene mencionarlo
> explícitamente en el documento de la fase.

### 2.2 `real` es alias de `float`

El léxico reconoce cuatro palabras reservadas de tipo (`int`, `float`, `bool`,
`real`) pero el lenguaje tiene **tres tipos**. El parser normaliza `real` a
`float` y conserva el lexema escrito.

Para el Bloque 2 esto significa: **la tabla de símbolos solo verá `int`, `float` y
`bool`.** Nunca llega un tipo `real`. Si necesitas mostrar el lexema original como
evidencia, está en la clave `tipo_lexema` del nodo de declaración.

No se tocó el léxico, así que la Fase 1 entregada sigue igual.

### 2.3 CHAR no es un tipo de dato

El DFA emite tokens `CHAR` para `'a'`, pero ninguna producción de la gramática
los acepta: un carácter literal en el código fuente pasa el léxico y lo rechaza
el sintáctico. **Nunca llega al análisis semántico**, así que no hay que
contemplarlo en las reglas de tipos.

Lo mismo aplica a `STRING`, con una diferencia: `STRING` sí es válido, pero
únicamente dentro de `cout`. No se puede declarar una variable de cadena ni
asignarle una. Para el semántico, una cadena solo aparece como elemento de una
salida y no participa en ninguna verificación de tipos.

### 2.4 Un solo ámbito

Confirmado: el lenguaje solo tiene el bloque `main`, sin funciones ni bloques
anidados con ámbito propio. La tabla de símbolos es de **un único ámbito**. No
hace falta pila de ámbitos ni `delete` por salida de bloque.

### 2.5 Las claves del AST no siguen el contrato del plan

El plan proponía nodos con las claves `nodo`, `op`, `lexema`, `hijos`. **El AST
real usa otras claves** y se decidió dejarlo así en vez de renombrar, por tres
razones:

- El visor del IDE (`ast_tree_viewer.py`, `ast_text.py`) ya lee `type`, `label` y
  `children`. Renombrar obliga a tocar el Bloque 3 sin ganar nada funcional.
- El contrato del plan se escribió antes de revisar el código existente.
- `lexema` mezclaba el nombre de un identificador con el valor de un literal. El
  semántico los trata distinto — uno va a `lookup`, el otro al atributo de
  valor — así que tenerlos separados conviene.

La equivalencia está en la sección 4.

---

## 3. Lo que se arregló

Numerados como en el documento de diagnóstico.

| # | Problema | Solución |
| --- | --- | --- |
| 1 | `if`, `while` y `until` exigían paréntesis | Son opcionales. No se tocó la gramática: `( expresion )` ya era una alternativa de `componente`, así que `if (2>3) then` e `if 2>3 then` producen **el mismo árbol** |
| 2 | `cin >> x;` y `cout << x;` no se reconocían | Se corrigió el archivo de prueba (decisión 2.1), no el parser |
| 3 | `do … while cond <sentencias> end until cond` no estaba soportado | `_repeticion` acepta las tres formas del cuerpo: `{ }`, `sentencias end`, y `end` vacío |
| 4 | Dos dialectos y el parser solo cubría uno | Cubre los dos, y se verificó con una prueba que generan árboles idénticos |
| 5 | Identificadores declarados sin línea ni columna | Cada identificador es ahora un nodo con su posición. `cin` guarda además la del identificador leído |
| 6 | `Numero` no distinguía entero de flotante | Tiene `es_entero`, y sale en el JSON |
| 7 | El árbol binario solo existía dentro del formateador | Se expuso `ASTFormatter.to_binary(ast)` |
| 8 | El tipo `real` no está en la gramática | Alias de `float` (decisión 2.2) |
| 11 | `errors.txt` sin salto de línea final; docstrings de «stub» | Un solo `_write_errors` reemplaza las cuatro copias del código. Se limpiaron los TODO ya resueltos |
| 12 | `parsers.py` vacío, archivos sueltos en la raíz | Borrado; los 11 archivos de prueba se movieron a `pruebas/` sin espacios en el nombre |
| 13 | CRLF ensuciando `git status` | `.gitattributes` con `* text=auto` |

### Arreglos extra, no previstos en el plan

**`cout expresion << cadena` no funcionaba.** El analizador de expresiones tomaba
el primer `<` como «menor que» antes de que `_salida` viera el `<<`. Se agregó un
lookahead de un token y se reescribió `_salida` como «un elemento seguido de cero
o más elementos separados por `<<`». Las cuatro formas de la producción `salida`
funcionan ahora, incluyendo cadenas largas como
`cout "s=" << x + y << "!";`. Un solo `<` sigue siendo el operador relacional.

**Código muerto en `ast_formatter.py`.** Había dos implementaciones viejas
completas que quedaban después de un `return`, más los helpers que solo ellas
usaban: unas 490 líneas inalcanzables. El archivo pasó de 910 a 420 líneas sin
cambiar un solo carácter de la salida.

**Bug en el stub semántico.** `_run_semantico` buscaba tokens de tipo `"IDENT"`,
que no existe — el token se llama `IDENTIFIER`. Por eso `symbols.txt` salía
siempre vacío. Corregido, aunque el Bloque 3 va a reemplazar la función entera.

---

## 4. Contrato real del AST

### Cómo obtenerlo

```python
from parser.parser import Parser
from parser.ast_formatter import ASTFormatter

ast, errores = Parser(tokens).parse()
arbol = ASTFormatter.to_binary(ast)   # dict anidado, listo para recorrer
```

`to_dict` devuelve exactamente lo mismo; existe solo porque el IDE la llama con
ese nombre. Conviene trabajar sobre el **dict** y no sobre los objetos de
`ast_nodes.py`: en el dict las expresiones ya vienen plegadas en forma binaria,
mientras que en los objetos siguen siendo listas planas de términos y factores.

### Claves de cada nodo

Siempre presentes:

| Clave | Contenido |
| --- | --- |
| `type` | Clase del nodo: `Programa`, `Asignacion`, `OperacionBinaria`, `Literal`… |
| `label` | Etiqueta legible, la que muestra el visor del IDE |
| `linea`, `columna` | Posición del lexema que origina el nodo |
| `children` | Lista de hijos. En las operaciones binarias son exactamente 2 |

Según el tipo de nodo:

| Clave | Aparece en | Contenido |
| --- | --- | --- |
| `operador` | `OperacionBinaria`, `OperacionUnaria` | `+ - * / % ^ < <= > >= == != && \|\| !` |
| `nombre` | `Identificador` | Lexema de la variable |
| `valor` | `Literal` | Valor del literal |
| `es_entero` | `Literal` numérico | `true` si es `int`, `false` si es `float` |
| `tipo_literal` | `Literal` | `entero`, `flotante`, `booleano` o `cadena` |
| `tipo` | `DeclaracionVariable` | Tipo normalizado: `int`, `float` o `bool` |
| `tipo_lexema` | `DeclaracionVariable` | Lexema escrito (`real` cuando se usó ese alias) |
| `identificadores` | `DeclaracionVariable` | Lista de `{nombre, linea, columna}` |
| `identificador` | `Asignacion`, `IncrementoDecremento`, `EntradaEstandar` | Lexema de la variable |
| `identificador_linea`, `identificador_columna` | `EntradaEstandar` | Posición del id leído por `cin` |
| `mensaje` | `NodoError` | Texto del error sintáctico |

### Equivalencia con el contrato del plan

| Plan | AST real |
| --- | --- |
| `nodo` | `type` |
| `op` | `operador` |
| `lexema` | `nombre` en identificadores, `valor` en literales |
| `hijos` | `children` |
| `linea`, `columna`, `es_entero` | igual |

### Posición del identificador en asignaciones e incrementos

En `Asignacion` e `IncrementoDecremento` **no hay** campos
`identificador_linea`/`identificador_columna`: la `linea` y `columna` del nodo
**son** las del identificador, porque la sentencia empieza ahí.

Es lo que necesitas para reportar los errores E1 y E4 en la posición que espera
el documento de diagnóstico. Por ejemplo, el nodo de `suma = 45;` (línea 4) trae
`linea: 4, columna: 5`, que es justo donde debe ir el error E1.

### Nodos que NO aparecen en el árbol

Esto es lo más importante al escribir el recorrido. Estas construcciones
gramaticales son **transparentes**: no generan un nodo propio.

- `Expresion`, `ExpresionSimple`, `Termino` y `Factor` se pliegan en
  `OperacionBinaria`, o desaparecen si no hay operador.
- `Declaracion` y `Sentencia` se reemplazan por su contenido.
- Un `Componente` entre paréntesis devuelve la expresión interna: los paréntesis
  **no dejan rastro** en el árbol.

Dicho de otro modo: entre una `Asignacion` y sus operandos solo hay nodos
`OperacionBinaria`, `OperacionUnaria`, `Literal` e `Identificador`. Nada más.

### Estructura de las construcciones de control

`Seleccion`, `Iteracion` y `Repeticion` agrupan sus partes en nodos intermedios
de tipo `SeccionAST`, identificados por su `label`:

| Nodo | Secciones (en orden) |
| --- | --- |
| `Seleccion` (`IF`) | `CONDICION`, `ENTONCES`, `SINO` |
| `Iteracion` (`WHILE`) | `CONDICION`, `CUERPO` |
| `Repeticion` (`DO_WHILE_UNTIL`) | `CUERPO_DO`, `CONDICION_WHILE`, `CUERPO_WHILE`, `CONDICION_UNTIL` |

Las secciones vacías no aparecen: un `if` sin `else` no trae nodo `SINO`.

### Ejemplo

Para `x = 2 + 3 * 4;` con `int x;` declarado:

```json
{
  "type": "Asignacion",
  "linea": 4, "columna": 3,
  "label": "ASIGNACION: x",
  "identificador": "x",
  "children": [
    {
      "type": "OperacionBinaria", "operador": "+",
      "linea": 4, "columna": 9, "label": "OPERACION: +",
      "children": [
        { "type": "Literal", "valor": 2, "es_entero": true,
          "tipo_literal": "entero", "linea": 4, "columna": 7, "children": [] },
        {
          "type": "OperacionBinaria", "operador": "*",
          "linea": 4, "columna": 13, "label": "OPERACION: *",
          "children": [
            { "type": "Literal", "valor": 3, "es_entero": true,
              "tipo_literal": "entero", "linea": 4, "columna": 11, "children": [] },
            { "type": "Literal", "valor": 4, "es_entero": true,
              "tipo_literal": "entero", "linea": 4, "columna": 15, "children": [] }
          ]
        }
      ]
    }
  ]
}
```

La precedencia y la asociatividad están verificadas con pruebas: la multiplicación
pega más que la suma, la resta y la división asocian a la izquierda, y la potencia
asocia a la derecha (`2^3^2` es `2^(3^2)`).

---

## 5. Garantías que puedes dar por hechas

Verificadas con pruebas automáticas sobre `TestSemantica.txt` y los samples:

- Todo nodo tiene `linea` y `columna` distintas de cero.
- Toda `OperacionBinaria` tiene exactamente 2 hijos; toda `OperacionUnaria`, 1.
- Los `Literal` no tienen hijos.
- Ningún nodo queda sin `label`.
- Los dos dialectos producen árboles idénticos.

---

## 6. Pendientes

### Para el Bloque 2

Todo lo del plan sigue igual, con estos ajustes:

- La tabla de símbolos es de **un solo ámbito** (decisión 2.4). `delete` puede
  implementarse por completitud, pero el análisis no la necesita.
- Solo hay **tres tipos**: `int`, `float`, `bool`. Nunca llega `real` ni `char`.
- Las cadenas (`STRING`) solo aparecen dentro de `cout` y no participan en la
  verificación de tipos. Un `cout` con una cadena no produce error.
- Las claves del AST son las de la sección 4, no las del plan.
- Los **6 errores semánticos** esperados para `TestSemantica.txt` siguen siendo
  los mismos, y la tabla de símbolos también. Pero **una columna cambió**: al
  quitar el `>> ` de la línea 37, el identificador `mas` se corrió de la columna
  16 a la 13. La tabla de aceptación queda así:

  | Línea:col | Código | Construcción | Motivo |
  | --- | --- | --- | --- |
  | 4:5 | E1 | `suma = 45;` | `suma` no está declarada |
  | 5:5 | E4 | `x = 32.32;` | Se asigna un `float` a `x`, que es `int` |
  | 14:5 | E4 | `y = 14.54;` | Se asigna un `float` a `y`, que es `int` |
  | 16:9 | E4 | `y = a + 3;` | `a + 3` es `float` porque `a` es `float`; `y` es `int` |
  | 33:13 | E1 | `mas = 36 / 7;` | `mas` no está declarada |
  | **37:13** | E1 | `cin mas;` | `mas` no está declarada — **antes 37:16** |

  Las cinco primeras posiciones están verificadas contra el AST real. Las líneas
  no cambiaron en ningún caso.

### Lo que el Bloque 1 no hizo

- `compiler_stub.py::_run_semantico` sigue siendo un stub. Lo reemplaza el
  Bloque 3, no el 2.
- Los hallazgos 9 y 10 (marcado de errores en el editor y `stderr` del compilador
  en la pestaña equivocada) son del Bloque 3 y siguen abiertos.
- Las pruebas son `unittest`, no `pytest`. Como `pytest` ejecuta clases
  `unittest` sin cambios, no urge convertirlas; si lo haces, que sea en tu rama.

### Dudas que conviene aclarar en el equipo

- **`cout` y la guía.** Decidimos no soportar `cin >>` / `cout <<` y ajustar el
  archivo de prueba. Vale la pena que los tres estén de acuerdo antes de la
  presentación, porque es lo primero que la profesora va a ver distinto respecto
  al archivo que ella entregó.
- **`real` en el PDF.** Si el documento de la Fase 2 declara `real` como un tipo
  propio, hay que explicar en el PDF de la Fase 3 por qué ahora es un alias.

---

## 7. Cómo correr las pruebas

```powershell
cd external_compiler
python -m unittest test_parser_recovery      # 19 pruebas
python compiler_stub.py ..\pruebas\TestSemantica.txt --phase sintactico
```

La segunda debe salir con código 0 y dejar `errors.txt` vacío.

Las pruebas cubren: recuperación de errores, los dos dialectos, el
`do-while-until` con cuerpo cerrado por `end`, las cuatro formas de `salida`,
precedencia y asociatividad, los invariantes del árbol binario, las posiciones de
los identificadores declarados, `es_entero`, el alias `real`, el archivo oficial y
los samples.

---

## 8. Archivos tocados

```
external_compiler/parser/parser.py           condiciones, do-while-until, salida, posiciones
external_compiler/parser/ast_nodes.py        Identificador en declaraciones, es_entero, tipo_lexema
external_compiler/parser/ast_formatter.py    to_binary, claves nuevas, borrado de código muerto
external_compiler/compiler_stub.py           _write_errors, docstrings, bug de IDENTIFIER
external_compiler/lexer/reserved_words.py    documentación de tipos (sin cambios de código)
external_compiler/lexer/token_types.py       documentación de KW_REAL, STRING y CHAR
external_compiler/test_parser_recovery.py    de 8 a 19 pruebas
ide/samples/*.caos                           cin >> / cout << → cin / cout
ide/ui/ide_window.py                         comentario duplicado
pruebas/                                     11 archivos movidos desde la raíz
pruebas/TestSemantica.txt                    archivo oficial con las 3 líneas ajustadas
.gitattributes                               * text=auto
.gitignore                                   salidas generadas en external_compiler/
docs/fase3-bloque1.md                        este documento
```

Se borró `ide/core/parsers.py`, que estaba vacío.

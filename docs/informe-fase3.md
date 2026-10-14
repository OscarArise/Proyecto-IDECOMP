# Informe de la Fase 3 — Análisis semántico (CAOS)

Compiladores II · UAA · Integrantes en `entrega/integrantes.txt`.

## 1. Qué se construyó

Una fase semántica real, conectada al pipeline y visible en el IDE.

- **Entrada:** el AST del parser (`ASTFormatter.to_binary(ast)`).
- **Proceso:** `semantic.analizar` trabaja sobre una copia profunda del árbol; recorre, declara variables, infiere tipos y detecta errores.
- **Salida:** `ResultadoSemantico` con árbol original, árbol anotado, tabla de símbolos, errores, traza de recorrido y conversiones.
- **Archivos generados:** `semantic.txt` (recorrido, tipos, árbol anotado y una sección JSON estructurada), `symbols.txt`, `errors.txt`.

Módulos en `external_compiler/semantic/`: `tipos.py` (tipos y compatibilidad), `tabla_simbolos.py`, `analizador.py`, `errores.py`, `formateador.py`.

## 2. Cómo se dividió el trabajo

| Bloque | Responsable | Contenido |
|---|---|---|
| 1 | Carlos | Tipos, reglas y tabla de símbolos |
| 2 | Oscar | Analizador, anotación del árbol, errores E1–E7, formateador |
| 3 | Equipo | Conexión al compilador, IDE, entregables (PDF y capturas) |

Cada bloque vivió en su rama, se integró por Pull Request y se etiquetó (`fase3-b1`, `fase3-b2`). El Bloque 3 está en `fase3/b3-integracion`.

## 3. Decisiones de diseño

1. **Prueba oficial adaptada.** `TestSemantica.txt` se adaptó a la gramática del proyecto con aprobación de la profesora; es la referencia de aceptación.
2. **Tabla de símbolos estilo TINY.** Hash de tamaño 211, `hash = ((temp << 4) + c) % 211`, encadenamiento separado, ubicación (`loc`) consecutiva desde 0. Como en `st_insert` de TINY, cada aparición de un identificador agrega su línea, aunque se repita (`y = y + 1` en la línea 9 registra `9, 9`). Además guarda el valor actual de cada variable.
3. **Tipos int / float / bool.** `real` es alias de `float`.
4. **Una sola conversión implícita:** int → float. float → int es error (E4). `int/int` trunca hacia cero.
5. **Un solo ámbito.** El lenguaje no define bloques con variables locales, así que una sola tabla basta.
6. **Valores de las variables.** Cada asignación guarda su valor en la tabla y cada identificador toma ese valor (en `z = y + 7`, `y` vale 4 y `z` recibe 11). El valor no se fuerza cuando depende de la ejecución: sin asignar, `cin`, o variables modificadas dentro de un ciclo quedan *desconocidas*. En un `if` con condición conocida solo cambia valores la rama que se ejecuta; la otra se verifica igual y se marca *no se ejecuta*.
7. **Árbol anotado sobre una copia.** El AST original no se modifica, lo que permite compararlos lado a lado. Los nodos anotados llevan `⟨tipo⟩`, `valor_calculado`, `loc`, etc.; se agregaron los nodos `IdentificadorDeclarado` y `ConversionTipo`.
8. **Sin errores en cascada.** Una variable no declarada se reporta una vez por uso y su tipo queda "desconocido"; las expresiones que la contienen no generan más errores.
9. **Códigos de salida:** 0 ok, 1 léxico, 2 sintáctico, 3 semántico. Con errores léxicos o sintácticos la fase semántica no se ejecuta.
10. **`semantic.txt` autocontenido.** Termina con una sección JSON que los visores del IDE reutilizan, sin duplicar lógica (`ide/core/semantic_output.py`).
11. **Se conservó el nombre `compiler_stub.py`.** Renombrarlo rompería la invocación del IDE justo antes de la entrega; el nombre y los stubs de intermedio/ejecución quedan como deuda para la siguiente fase.
12. **Cambio mínimo en el parser** para exponer los datos que el análisis necesita (ver `docs/fase3-bloque2.md`, sección 7).
13. **Ciclos anidados.** `repeticion → do lista_sentencias until expresion`. El cuerpo del `do` es una lista de sentencias normal, así que un `while` (u otro `do`) dentro de él es un ciclo anidado con su propio nodo.

## 4. Integración en el IDE

- Pestañas nuevas: **Arbol Anotado**, **Comparacion** (AST original vs anotado, con botón para abrirla en ventana grande) y **Simbolos**.
- Los errores semánticos se marcan en el editor por línea y columna (`[línea:col]`).
- Atajo **F7** ejecuta hasta la fase semántica.
- Colores: errores en rojo, conversiones de tipo y declaraciones resaltadas, con leyenda.

## 5. Verificación

- 69 pruebas del compilador (`test_semantico`, `test_integracion`, `test_parser_recovery`) y 5 del IDE (`test_semantic_output`), todas OK.
- `test_integracion` ejecuta el compilador como proceso y comprueba códigos de salida de todos los programas de `pruebas/` y `ide/samples/` (regresión de léxico y sintáctico).
- Resultado esperado de `TestSemantica.txt`: **exit 3, 6 errores**:

| Línea:col | Error |
|---|---|
| 4:5 | E1 `suma` no declarada |
| 5:5 | E4 float → `x` (int) |
| 14:5 | E4 float → `y` (int) |
| 16:9 | E4 float → `y` (int) |
| 33:13 | E1 `mas` no declarada |
| 37:13 | E1 `mas` no declarada |

## 6. Instrucciones de demostración

1. Abrir una terminal en la raíz del repositorio y ejecutar `python ide/main.py`.
2. **Archivo → Abrir** `pruebas/TestSemantica.txt`.
3. Pulsar **F5** (léxico) y **F6** (sintáctico): ambos terminan sin errores.
4. Pulsar **F7** (semántico). Mostrar:
   - la pestaña **Semantico**: recorrido, inserciones/búsquedas en la tabla y tipos;
   - **Simbolos**: variables `x y z a b c` con tipo, ubicación, valor final y una línea por cada aparición (`y`: `9, 9`, `23, 23`, `29, 29`);
   - **Arbol Anotado**: nodos con `⟨tipo⟩` y valores; los identificadores muestran el valor que toman de la tabla, y el `while` de la línea 30 aparece anidado dentro del `DO_UNTIL`;
   - **Comparacion** → "Comparar en ventana grande": AST original frente al anotado;
   - **Errores**: los 6 errores de la tabla anterior, y su marca roja en el editor.
5. Abrir `pruebas/codigo_valido.caos` y pulsar F7: sin errores, tabla completa.
6. Abrir `pruebas/conerrores.caos` y pulsar F6: el error sintáctico se detiene antes de la fase semántica (regresión).
7. Pruebas automáticas (opcional):
   ```
   cd external_compiler
   python -m unittest test_semantico test_integracion test_parser_recovery
   ```
8. Línea de comandos: `python compiler_stub.py ../pruebas/TestSemantica.txt --phase semantico` (desde `external_compiler/`); `echo $?` / `echo %ERRORLEVEL%` debe mostrar 3.

## 7. Correcciones de la prerevisión

| Observación | Causa | Corrección |
|---|---|---|
| El árbol no jala el valor de la variable | Se había decidido calcular valores solo con constantes: los identificadores nunca tenían valor y la tabla no lo guardaba. | La tabla guarda el valor de cada variable; las asignaciones, `++`/`--` y `cin` lo actualizan y los identificadores lo toman (`analizador.py`, `tabla_simbolos.py`). |
| Los ciclos no se anidan | El parser tenía `repeticion → do sentencias while cond sentencias until cond`: el `while` de TestSemantica se tomaba como parte del `do` y el cuerpo del `do` terminaba en el primer `while`. | `repeticion → do lista_sentencias until expresion`; el `while` es una iteración normal dentro del cuerpo (`parser.py`, `ast_nodes.py`, `ast_formatter.py`). |
| La tabla no repite la línea | `agregar_linea` descartaba una línea que ya estaba en la lista. | Cada aparición agrega su línea, como en TINY. |

## 8. Entregables y pasos pendientes

- `entrega/`: `ast_original.txt`, `arbol_anotado.txt`, `tabla_simbolos.txt`, `errores_semanticos.txt`, `TestSemantica.txt`, PDF y capturas.
- Regenerar el PDF con capturas definitivas de Windows: copiarlas a `entrega/capturas/` con los mismos nombres que `capturas_borrador/` y ejecutar, desde `entrega/`, `python generar_pdf.py --capturas capturas` (requiere `pip install -r requirements.txt`).
- Pendiente del equipo: probar F5/F6/F7 en Windows, subir capturas definitivas, abrir el PR `fase3/b3-integracion` → `master`, etiquetar `fase3-entrega` y entregar en el Aula Virtual el **15 de octubre** (10 % de penalización por día de retraso).

## 9. Deuda técnica (después de la entrega)

Renombrar `compiler_stub.py`, limpiar ramas antiguas (`B`, `c`, `d`, `fase3/b2-semantico`, `backup/b2-antes-de-reescribir`), convertir `test_parser.py` en pruebas `unittest`, resolver los TODO de `lexer/dfa_lexer.py` y eliminar duplicados (`ide/samples/TestIDE.txt` = `TestIDE.caos`; `external_compiler/testLexico.txt` ≠ `pruebas/testLexico.txt`).

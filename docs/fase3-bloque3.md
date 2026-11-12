# Fase 3 · Bloque 3 — Integración, IDE y entregables

Rama: `fase3/b3-integracion` (sale de `master` en `57dd17f`, etiqueta `fase3-b2`).
Responsables: Oscar y Carlos. Entrega: **15 de octubre de 2026** (Aula Virtual).

Este bloque conecta el analizador semántico (Bloque 2) con el compilador y el
IDE, y produce las evidencias y el PDF que pide la guía (secciones 9, 10 y 11).

---

## 1. Punto de partida (verificado el 12/10)

| Pieza | Estado |
| --- | --- |
| `external_compiler/semantic/` | Completo. 49 pruebas pasan. `TestSemantica.txt` da los 6 errores esperados. |
| `compiler_stub.py::_run_semantico` | **Sigue siendo el stub**: lista identificadores, no llama a `analizar`. |
| `_run_sintactico` | Devuelve solo texto; el AST no llega a la fase semántica. |
| `ASTFormatter.to_dict` / `to_binary` | Son la misma estructura: el JSON de `syntax.txt` es el árbol que recibe el semántico. |
| IDE · pestaña Semántico / Símbolos | Ya existen y ya se llenan con `semantic.txt` / `symbols.txt` (`panel_map`). |
| IDE · árbol | Solo hay un visor (`ASTTreeViewer`) para el AST sintáctico. No hay visor del árbol anotado ni comparación. |
| IDE · errores en el editor | `highlighter.py` solo reconoce el formato léxico `en línea N, columna M`. Los errores sintácticos y semánticos usan `[l:c]` y **no se marcan**. `ide_window.py` solo le pasa los errores léxicos. |
| IDE · stderr del compilador | Se escribe en la pestaña *Errores Léxicos* (confunde un fallo interno con un error léxico). |
| `semantic.txt` | ~2 400 líneas con `TestSemantica.txt`; el JSON final (para el visor) ocupa la mayor parte. Conviene no mostrarlo en la pestaña de texto. |

---

## 2. Tareas

Las tareas están repartidas **por archivo** para que los dos trabajen en la
misma rama sin conflictos.

### B3.1 Conectar el semántico al compilador — Oscar

Archivos: `external_compiler/compiler_stub.py`, `README_run.txt`, prueba nueva.

1. `_run_sintactico` devuelve `(texto, ast)`.
2. `_run_semantico(ast, errors)` llama a `analizar(ASTFormatter.to_binary(ast))` y
   escribe `semantic.txt` (`semantic_txt`) y `symbols.txt` (`symbols_txt`).
3. Los errores se agregan como `[SEMANTICO] [l:c] Error semántico Ex: …`.
4. Con errores semánticos: código de salida **3**. `semantic.txt` y
   `symbols.txt` se escriben aunque haya errores (la tabla es evidencia).
5. `test_integracion.py`: ejecuta el compilador como subproceso sobre
   `TestSemantica.txt` y comprueba código 3, los 6 errores y la tabla.
   Corre también `pruebas/*` y `ide/samples/*` para confirmar que los códigos
   0/1/2 no cambian.

**Termina cuando:** `python compiler_stub.py ../pruebas/TestSemantica.txt` da
código 3 y los cinco archivos; todas las pruebas pasan. Se sube antes que B3.2,
porque el IDE necesita el nuevo `semantic.txt`.

### B3.2 Visualización en el IDE — Carlos

Archivos: `ide/ui/panels.py`, `ide/ui/ide_window.py`, `ide/ui/ast_tree_viewer.py`.

1. **Pestaña Semántico (texto):** mostrar `semantic.txt` hasta el marcador
   *Representación estructurada* (sin el JSON).
2. **Pestaña Árbol Anotado:** segundo `ASTTreeViewer` que carga el JSON de
   `semantic.txt`. Generalizar `_load_ast_to_tree(salida, visor)` para usarlo
   con los dos visores.
3. **Pestaña Comparación:** `PanedWindow` con el AST original (de `syntax.txt`)
   a la izquierda y el anotado a la derecha. Es lo que pide la guía en la
   sección 5: *AST original → AST con anotaciones semánticas*.
4. **Colores en el visor:** nodos con `errores_semanticos` en rojo (tag
   `error`), `ConversionTipo` e `IdentificadorDeclarado` con un color propio.
5. **Marcar en el editor todos los errores**, no solo los léxicos: pasar
   `err_lexico + err_sintactico + err_semantico` a `mark_errors` y
   `mark_error_lines` (B3.3 hace que el resaltador los entienda).
6. **stderr del proceso:** escribirlo en *Ejecución* o en la barra de estado, no
   en *Errores Léxicos*.
7. `clear_all` limpia los visores nuevos; con F7 sin errores, enfocar la
   pestaña Semántico.

### B3.3 Resaltado de errores con `[l:c]` — Oscar

Archivo: `ide/ui/highlighter.py`.

Ampliar `_ERROR_PATTERN` para aceptar también `[l:c]` y marcar el lexema
completo (hasta el siguiente separador) en lugar de un solo carácter. No toca
`ide_window.py`.

### B3.4 Pruebas en Windows — ambos

El IDE usa Tkinter; solo se puede probar en sus equipos. Con
`pruebas/TestSemantica.txt` abierto en el IDE:

| Paso | Debe verse |
| --- | --- |
| F5 | Tokens; sin errores léxicos. |
| F6 | AST en *Sintactico* y *Arbol Conectado*; sin errores. |
| F7 | *Semántico* con resumen, árbol anotado en texto y recorrido; *Árbol Anotado*; *Comparación*; *Simbolos* con x, y, z (int, loc 0–2) y a, b, c (float, loc 3–5); *Errores Semanticos* con los 6 errores; líneas 4, 5, 14, 16, 33 y 37 marcadas en rojo en el editor; barra de estado “Error en fase: err_semantico (cód. 3)”. |
| Regresión | `codigo_valido.caos` y `test_basico.caos` siguen sin errores; `conerrores.caos` sigue en la fase sintáctica. |

### B3.5 Evidencias y entregables — ambos

Carpeta `entrega/` en la raíz del repositorio:

| Entregable (guía §11) | Archivo |
| --- | --- |
| 1. Código fuente | el repositorio (zip de `master` con la etiqueta final) |
| 2. AST base | `entrega/ast_original.txt` (`syntax.txt` de TestSemantica) |
| 3. Árbol anotado | `entrega/arbol_anotado.txt` (`semantic.txt`) |
| 4. Tabla de símbolos | `entrega/tabla_simbolos.txt` (`symbols.txt`) |
| 5. Errores semánticos | `entrega/errores_semanticos.txt` (`errors.txt`) |
| 6. Capturas | `entrega/capturas/`: árbol anotado, comparación, tabla, comprobación de tipos (nodos con conversión), errores, editor con errores marcados, barra de estado |
| 7. PDF | `entrega/Fase3_Analisis_Semantico.pdf` |
| 8. Integrantes | `entrega/integrantes.txt` (nombres completos y matrículas) |

### B3.6 Documento PDF — ambos

Secciones según la guía §11.7: implementación, reglas semánticas, atributos
sintetizados y heredados, anotación del AST, tabla de símbolos, comprobación de
tipos, conversiones, errores E1–E7, pruebas y capturas. Fuente principal:
`docs/fase3-bloque1.md` y `docs/fase3-bloque2.md`.

Debe justificar explícitamente:

- el archivo de prueba adaptado al lenguaje, aprobado por la profesora;
- `real` como alias de `float` y `char` fuera del sistema de tipos;
- la división entera que trunca hacia cero;
- un solo ámbito (solo existe `main`).

### B3.7 Cierre — Oscar

PR `fase3/b3-integracion` → `master`, etiqueta `fase3-entrega`, zip y entrega
en el Aula Virtual.

---

## 3. Calendario

| Día | Oscar | Carlos |
| --- | --- | --- |
| Lun 12 | B3.1 y B3.3; subir a la rama | Revisar este plan; preparar `integrantes.txt` |
| Mar 13 | Apoyar B3.2; esqueleto del PDF | B3.2 (visores, comparación, errores en editor) |
| Mié 14 | B3.4 y capturas; PDF | B3.4 y capturas; PDF |
| Jue 15 | B3.7: PR, etiqueta y entrega | Revisión final del PDF |

Margen: el miércoles en la noche todo debe estar en `master`. El jueves solo es
para entregar.

---

## 4. Reglas de trabajo en git

- Los dos trabajan en `fase3/b3-integracion`. Antes de empezar: *Fetch* y *Pull*.
- Commits pequeños, uno por tarea. *Push* al terminar cada uno.
- Oscar no toca `ide_window.py`, `panels.py` ni `ast_tree_viewer.py`; Carlos no
  toca `compiler_stub.py` ni `highlighter.py`. Si hace falta, se avisa antes.
- Los archivos de `ide/outputs/` no se suben (ya están en `.gitignore`); las
  copias para la entrega van en `entrega/`.

---

## 5. Estado al 12 de octubre (noche)

| Tarea | Estado |
| --- | --- |
| B3.1 Semántico conectado al compilador | Hecho. `TestSemantica.txt` sale con código 3, 6 errores y tabla. `test_integracion.py` (8 pruebas). |
| B3.2 Visualización en el IDE | Hecho: pestañas Arbol Anotado y Comparacion, texto de Semantico sin JSON, errores de las tres fases marcados en el editor, stderr fuera de Errores Lexicos. Probado con el IDE real en Linux sin pantalla (Xvfb + Tk 8.6). |
| B3.3 Resaltado `[l:c]` | Hecho (`highlighter.py`). |
| B3.4 Pruebas en Windows | **Pendiente.** Repetir la tabla de la sección 2 en el IDE de Windows con F5, F6 y F7. |
| B3.5 Entregables | Salidas generadas en `entrega/`. Falta: matrículas en `integrantes.txt` y capturas definitivas tomadas en Windows (`entrega/capturas_borrador/` son de prueba). |
| B3.6 PDF | Borrador generado (`entrega/Fase3_Analisis_Semantico.pdf`). Para regenerarlo con las capturas de Windows: poner los PNG con los mismos nombres en `entrega/capturas/` y ejecutar `python generar_pdf.py --capturas capturas` (requiere `pip install reportlab pillow`). Completar las matrículas en `INTEGRANTES`/portada. |
| B3.7 Cierre | Pendiente: PR a `master`, etiqueta `fase3-entrega`, entrega en el Aula Virtual. |

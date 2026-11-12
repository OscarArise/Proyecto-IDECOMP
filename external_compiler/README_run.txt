================================================================================
 README_run.txt — Cómo invocar el compilador del IDE CAOS
================================================================================

DESCRIPCIÓN
-----------
compiler_stub.py es el punto de entrada del pipeline de compilación del
lenguaje CAOS. Fases reales: léxico, sintáctico y semántico. Las fases de
código intermedio y ejecución siguen siendo stubs (fases futuras). Es invocado
por el IDE a través de CompilerRunner usando el módulo subprocess.
(El nombre del archivo se conserva por compatibilidad con el IDE.)


INVOCACIÓN
----------
Sintaxis general:

    python compiler_stub.py <ruta_fuente> [--phase <fase>]

Argumentos:

    <ruta_fuente>         Ruta (absoluta o relativa) al archivo .caos a compilar.
                          Este argumento es OBLIGATORIO.

    --phase <fase>        (Opcional) Ejecuta únicamente hasta la fase indicada.
                          Valores válidos:
                              lexico       → Solo análisis léxico
                              sintactico   → Léxico + análisis sintáctico
                              semantico    → + análisis semántico (real: tabla de símbolos, tipos, errores E1-E7)
                              intermedio   → + generación de código intermedio
                              ejecutar     → Pipeline completo + ejecución
                          Si se omite --phase, se ejecuta el pipeline completo.

DIRECTORIO DE TRABAJO
---------------------
El IDE lanza el compilador con cwd=outputs/, por lo que los archivos de salida
se escriben directamente en ese directorio sin prefijo de ruta.


ARCHIVOS DE SALIDA
------------------
Todos los archivos se escriben en el directorio  ide/outputs/ :

    tokens.txt          Tabla de tokens (resultado del análisis léxico)
    syntax.txt          Árbol sintáctico o derivaciones
    semantic.txt        Información del análisis semántico
    intermediate.txt    Código intermedio (cuádruplos / TAC)
    symbols.txt         Tabla de símbolos
    errors.txt          Errores de todas las fases (ver formato más abajo)
    exec.txt            Salida de la ejecución del programa compilado

Si una fase no se ejecuta, el archivo correspondiente puede quedar vacío o
no existir.


FORMATO DE errors.txt
---------------------
Cada error debe ir precedido de una etiqueta de fase entre corchetes:

    [LEXICO] [4:7] Carácter inválido '@'
    [SINTACTICO] [12:5] Se esperaba ';' al final de la sentencia
    [SEMANTICO] [18:3] Variable 'x' no declarada
    [INTERMEDIO] Error generando cuádruplo para operación binaria
    [EJECUCION] División por cero en línea 25

Las etiquetas no distinguen mayúsculas/minúsculas.
Las líneas sin etiqueta se asocian automáticamente a la última fase activa.


CÓDIGOS DE RETORNO
------------------
    0   Éxito total (o hasta la fase indicada).
    1   Error en análisis léxico.
    2   Error en análisis sintáctico.
    3   Error en análisis semántico.
    4   Error en generación de código intermedio.
    5   Error en ejecución.
   -1   Timeout (IDE mató el proceso).
   -2   Compilador no encontrado.
   -3   Error interno inesperado.


EJEMPLO DE USO (desde línea de comandos)
-----------------------------------------
    # Compilación completa
    python compiler_stub.py C:\proyectos\hola.caos

    # Solo análisis léxico
    python compiler_stub.py C:\proyectos\hola.caos --phase lexico

    # Solo hasta análisis semántico
    python compiler_stub.py C:\proyectos\hola.caos --phase semantico
================================================================================

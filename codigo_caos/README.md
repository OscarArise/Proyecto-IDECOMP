# Ejercicios finales en CAOS

Programas `.caos` de los problemas de [`docs/ejercicios_finales_compiladores_ii.md`](../docs/ejercicios_finales_compiladores_ii.md), escritos para probar el compilador completo: léxico, sintáctico, semántico, generación de código TM / tres direcciones y ejecución en la TM.

## Organización

`grupo_01/` a `grupo_12/` tienen los 5 ejercicios de cada grupo (`ej1` secuencial, `ej2` y `ej3` selectivos, `ej4` y `ej5` repetitivos). Cuando un problema se repite entre grupos (por ejemplo, las lluvias en los grupos 1, 9 y 11), el archivo es el mismo y tiene el mismo nombre en cada carpeta.

| Archivo | Uso |
| :--- | :--- |
| `casos.py` | Entradas y salida esperada de cada programa, calculadas a mano a partir del enunciado |
| `probar_ejercicios.py` | Compila todos los programas, revisa cada fase, ejecuta el `code.tm` con cada caso en `tm.py` y `tm.exe` y escribe un resumen |
| `test_ejercicios.py` | Lo mismo como prueba `unittest` |
| `salidas/` | Evidencia generada: por programa `tokens.txt`, `syntax.txt`, `semantic.txt`, `symbols.txt`, `code.tm`, `code.ci` y `ejecucion.txt`; además `resumen.txt` |

## Uso

```powershell
python codigo_caos\probar_ejercicios.py          # todos los grupos
python codigo_caos\probar_ejercicios.py 4        # solo el grupo 4
python -m unittest codigo_caos.test_ejercicios   # como prueba unitaria
```

Cada programa también se puede abrir en el IDE (`python ide\main.py`). F8 muestra el código TM y el de tres direcciones, y F9 lo ejecuta pidiendo las entradas.

## Decisiones de los programas

CAOS no tiene arreglos, cadenas como variables ni menos unario, así que:

- Los datos por tipo (5 vinos, 5 localidades, 4 candidatos, 3 regiones) usan una variable por tipo.
- Los datos de texto se representan con claves numéricas. En las llamadas telefónicas, el tipo 1 es Internacional, el 2 Nacional y el 3 Local; en las facultades, las carreras van de 1 a 4. Los nombres solo se imprimen con `cout`.
- El valor `-1` de fin de datos se compara con una variable `fin = 0 - 1`. Desde la entrada sí se puede teclear `-1`.
- Cuando el enunciado no dice cómo terminan los datos, el programa lee primero cuántos son (N). Así ocurre en vendedor y mayor/menor. En las llamadas telefónicas, el fin de datos es el tipo 0.

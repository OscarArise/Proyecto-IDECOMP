"""
casos.py
--------
Casos de prueba de los ejercicios finales (docs/ejercicios_finales_compiladores_ii.md).

Cada programa .caos se identifica por su nombre de archivo; los ejercicios que
se repiten entre grupos son el mismo archivo copiado, así que comparten casos.

Cada caso es (entradas, salida esperada). Las entradas se dan en el orden en
que el programa las pide con cin; la salida es exactamente lo que imprime la
TM con OUT/OUTF/OUTS/OUTLN. Los valores esperados se calcularon a mano a partir
del enunciado, no ejecutando el compilador.
"""


def L(*lineas) -> str:
    """Salida esperada: una línea por cada cout."""
    return "".join(f"{linea}\n" for linea in lineas)


def lluvias(norte, centro, sur):
    """Entradas del ejercicio de lluvias: por mes, NORTE, CENTRO y SUR."""
    datos = []
    for mes in range(12):
        datos += [norte[mes], centro[mes], sur[mes]]
    return datos


_VENTAS_ESTADIO = [(1, 2), (3, 4), (2, 1), (5, 10), (1, 1)]
_PRECIOS_ESTADIO = [100, 80.5, 60, 40, 20]
_SALIDA_ESTADIO = L(
    "Venta: clave 1, cantidad 2, importe 200.0",
    "Venta: clave 3, cantidad 4, importe 240.0",
    "Venta: clave 2, cantidad 1, importe 80.5",
    "Venta: clave 5, cantidad 10, importe 200.0",
    "Venta: clave 1, cantidad 1, importe 100.0",
    "Boletos tipo 1: 3",
    "Boletos tipo 2: 1",
    "Boletos tipo 3: 4",
    "Boletos tipo 4: 0",
    "Boletos tipo 5: 10",
    "Recaudacion total: 820.5",
)

_VOTOS = [1, 3, 1, 4, 2, 2, 1, 4, 1, 1, 1, 2, 1, 3, 1, 4, 0]

CASOS = {
    # ------------------------------------------------------------ Grupo 1
    "ej1_orden_inverso.caos": [
        ([1, 2, 3, 4], L("4 3 2 1")),
        ([10, -5, 0, 7], L("7 0 -5 10")),
    ],
    "ej2_positivo_negativo_nulo.caos": [
        ([7], L("0")),
        ([-3], L("1")),
        ([0], L("2")),
    ],
    "ej3_orden_creciente_si_no.caos": [
        ([1, 2, 3], L("1")),
        ([3, 2, 1], L("0")),
        ([1, 1, 2], L("0")),
    ],
    "ej4_fibonacci.caos": [
        ([1], L("Termino 1: 0")),
        ([2], L("Termino 2: 1")),
        ([10], L("Termino 10: 34")),
    ],
    "ej5_lluvias_regiones.caos": [
        (lluvias([m for m in range(1, 13)], [2 * m for m in range(1, 13)],
                 [30 - m for m in range(1, 13)]),
         L("Promedio anual centro: 13.0",
           "Menor lluvia sur: mes 12, registro 18.0",
           "Region con mayor lluvia: SUR")),
        (lluvias([1] * 12, [10] * 12, [5, 5, 5, 5, 5, 5, 2, 5, 5, 5, 5, 5]),
         L("Promedio anual centro: 10.0",
           "Menor lluvia sur: mes 7, registro 2.0",
           "Region con mayor lluvia: CENTRO")),
        (lluvias([50] * 12, [10] * 12, [5] * 12),
         L("Promedio anual centro: 10.0",
           "Menor lluvia sur: mes 1, registro 5.0",
           "Region con mayor lluvia: NORTE")),
    ],
    # ------------------------------------------------------------ Grupo 2
    "ej1_promedio_calificaciones.caos": [
        ([12345, 8, 9.5, 7, 10, 6.5], L("Matricula: 12345", "Promedio: 8.2")),
        ([100, 10, 10, 10, 10, 10], L("Matricula: 100", "Promedio: 10.0")),
    ],
    "ej2_temperatura_grillo.caos": [
        ([80], L("Temperatura (F): 60.0")),
        ([50], L("Temperatura (F): 52.5")),
    ],
    "ej3_impuesto_articulo.caos": [
        ([15], L("Precio total: 15.0")),
        ([30], L("Precio total: 33.0")),
        ([100], L("Precio total: 130.0")),
        ([600], L("Precio total: 886.0")),
    ],
    "ej4_llamadas_telefonicas.caos": [
        # 13.65 (internacional 5 min) + 1.20 + 4.56 (nacional 10 min) + 0 (local)
        ([1, 5, 2, 2, 2, 10, 3, 4, 0], L("Total a pagar: 19.41")),
        # 52 llamadas locales: solo se cobran las 2 que pasan de 50
        ([3, 1] * 52 + [0], L("Total a pagar: 1.2")),
        ([0], L("Total a pagar: 0.0")),
    ],
    "ej5_produccion_vinos.caos": [
        ([3, 10, 20, 30, 40, 50, 5, 25, 0, 10, 10, 1, 2, 3, 4, 5],
         L("Anio 1: 150 litros",
           "Anio 2: 50 litros",
           "Anio 2 sin produccion de vino tipo 3",
           "Anio 3: 15 litros",
           "Total tipo 1: 16",
           "Total tipo 2: 47",
           "Total tipo 3: 33",
           "Total tipo 4: 54",
           "Total tipo 5: 65",
           "Mayor produccion tipo 2: anio 2 con 25 litros")),
        ([2, 1, 1, 1, 1, 1, 2, 3, 4, 5, 6],
         L("Anio 1: 5 litros",
           "Anio 2: 20 litros",
           "Total tipo 1: 3",
           "Total tipo 2: 4",
           "Total tipo 3: 5",
           "Total tipo 4: 6",
           "Total tipo 5: 7",
           "Mayor produccion tipo 2: anio 2 con 3 litros",
           "Ningun anio sin produccion de vino tipo 3")),
    ],
    # ------------------------------------------------------------ Grupo 3
    "ej1_rectangulo.caos": [
        ([3, 4.5], L("Perimetro: 15.0", "Area: 13.5")),
        ([10, 2], L("Perimetro: 24.0", "Area: 20.0")),
    ],
    "ej2_descendente.caos": [
        ([1, 2, 3], L("3 2 1")),
        ([2, 3, 1], L("3 2 1")),
        ([5, 1, 3], L("5 3 1")),
    ],
    "ej3_mayor_tres_reales.caos": [
        ([1.5, 2.5, 0.5], L("Mayor: 2.5")),
        ([3, 3, 1], L("Mayor: 3.0")),
        ([1, 2, 7.25], L("Mayor: 7.25")),
        ([2, 2, 2], L("Los tres son iguales: 2.0")),
    ],
    "ej4_serie_potencias.caos": [
        ([1], L("Suma: 1")),
        ([3], L("Suma: 32")),
        ([5], L("Suma: 3413")),
    ],
    "ej5_produccion_fabricas.caos": [
        ([2, 101] + [1000000] * 12 + [202] + [2000000] * 6 + [3500000] + [2000000] * 5,
         L("Fabrica 101: total anual 12000000.0",
           "Fabrica 202: total anual 25500000.0",
           "Fabrica 202 supero 3000000 en julio",
           "Fabrica que mas produjo: 202 con 25500000.0")),
        # julio exactamente en 3 000 000 no "supera"
        ([1, 7] + [0] * 6 + [3000000] + [0] * 5,
         L("Fabrica 7: total anual 3000000.0",
           "Fabrica que mas produjo: 7 con 3000000.0")),
    ],
    # ------------------------------------------------------------ Grupo 4
    "ej1_dinosaurio.caos": [
        ([1000, 50], L("Peso (kg): 453.592", "Longitud (m): 15.24")),
    ],
    "ej2_funcion_val.caos": [
        ([1, 5], L("VAL = 500.0")),
        ([2, 2], L("VAL = 10000.0")),
        ([3, 8], L("VAL = 12.5")),
        ([3, 0], L("No se puede dividir entre cero", "VAL = 0.0")),
        ([7, 3], L("VAL = 0.0")),
    ],
    "ej3_horas_extras.caos": [
        ([1000, 10, 2], L("Pago total: 1380.0")),
        ([1000, 40, 4], L("Pago total: 3100.0")),
        ([1500, 10, 5], L("Pago total: 1500.0")),
    ],
    "ej4_ventas_vendedor.caos": [
        ([6, 150, 200, 250, 399.5, 400, 1000],
         L("Ventas de 200 o menos: 2 por 350.0",
           "Ventas entre 200 y 400: 2 por 649.5",
           "Ventas de 400 o mas: 2 por 1400.0")),
    ],
    "ej5_estadio.caos": [
        (_PRECIOS_ESTADIO + [x for venta in _VENTAS_ESTADIO for x in venta] + [-1],
         _SALIDA_ESTADIO),
    ],
    # ------------------------------------------------------------ Grupo 5
    "ej1_cilindro.caos": [
        ([2, 5], L("Area: 62.8318", "Volumen: 62.8318")),
        ([1, 1], L("Area: 6.28318", "Volumen: 3.14159")),
    ],
    "ej2_aumento_sueldo.caos": [
        ([800], L("Nuevo sueldo: 920.0")),
        ([1000], L("Nuevo sueldo: 1120.0")),
        ([2000], L("Nuevo sueldo: 2240.0")),
    ],
    "ej3_facultades.caos": [
        ([1001, 1, 6, 8.8], L("Matricula: 1001", "Carrera: 1", "Aceptado = 1")),
        ([1002, 2, 6, 9.0], L("No aceptado = 0")),
        ([1003, 3, 6, 8.6], L("Matricula: 1003", "Carrera: 3", "Aceptado = 1")),
        ([1004, 4, 5, 9.5], L("No aceptado = 0")),
    ],
    "ej4_mayor_menor.caos": [
        ([5, 3, -2, 9, 0, 4], L("Mayor: 9", "Menor: -2")),
        ([1, 7], L("Mayor: 7", "Menor: 7")),
    ],
    # ------------------------------------------------------------ Grupo 6
    "ej1_segundos_dias.caos": [
        ([2], L("Segundos: 172800")),
        ([1], L("Segundos: 86400")),
    ],
    "ej2_aprobado.caos": [
        ([8], L("aprobado = 1")),
        ([7.9], L("reprobado = 0")),
        ([10], L("aprobado = 1")),
    ],
    "ej3_costo_hospital.caos": [
        ([1, 10, 30], L("Costo total: 250.0")),
        ([4, 5, 18], L("Costo total: 176.0")),
        ([2, 3, 14], L("Costo total: 52.8")),
        ([3, 2, 23], L("Costo total: 40.0")),
    ],
    "ej4_serie_alternada.caos": [
        ([1], L("Resultado: 1.0")),
        ([4], L("Resultado: 0.583333")),
        ([5], L("Resultado: 0.783333")),
    ],
    # ------------------------------------------------------------ Grupo 7
    "ej1_expresion_ab.caos": [
        ([2, 4], L("Resultado: 12.0")),
        ([1, 1], L("Resultado: 1.333333")),
    ],
    "ej3_orden_creciente.caos": [
        ([3, 1, 2], L("1 2 3")),
        ([2, 2, 1], L("1 2 2")),
        ([9, 5, 1], L("1 5 9")),
    ],
    "ej4_votos_candidatos.caos": [
        (_VOTOS, L("Candidato 1: 8 votos, 50.0%",
                   "Candidato 2: 3 votos, 18.75%",
                   "Candidato 3: 2 votos, 12.5%",
                   "Candidato 4: 3 votos, 18.75%")),
        ([0], L("Sin votos")),
    ],
    # ------------------------------------------------------------ Grupo 8
    "ej1_cambio.caos": [
        ([75.5, 100], L("Cambio: 24.5")),
    ],
    "ej2_expresion_pq.caos": [
        ([2, 3], L("P y Q satisfacen la expresion (81 < 680)")),
        ([5, 5], L("P y Q no satisfacen la expresion (700 >= 680)")),
    ],
    "ej3_descuento_compra.caos": [
        ([300], L("Total a pagar: 300.0")),
        ([800], L("Total a pagar: 760.0")),
        ([5000], L("Total a pagar: 4450.0")),
        ([10000], L("Total a pagar: 8200.0")),
        ([20000], L("Total a pagar: 15000.0")),
    ],
    "ej4_contar_ceros.caos": [
        ([3, 0, 5, 0, 0, -2, -1], L("Numero de ceros: 3")),
        ([-1], L("Numero de ceros: 0")),
    ],
    # ------------------------------------------------------------ Grupo 9
    "ej4_numeros_primos.caos": [
        ([20], L(2, 3, 5, 7, 11, 13, 17, 19, "Primos menores a 20: 8")),
        ([2], L("Primos menores a 2: 0")),
    ],
    # ------------------------------------------------------------ Grupo 10
    "ej2_aumento_categoria.caos": [
        ([2, 1000], L("Categoria: 2", "Nuevo sueldo: 1100.0")),
        ([4, 2000], L("Categoria: 4", "Nuevo sueldo: 2140.0")),
        ([5, 1500], L("Categoria: 5", "Nuevo sueldo: 1500.0")),
    ],
    "ej4_numeros_perfectos.caos": [
        ([30], L(6, 28)),
        ([500], L(6, 28, 496)),
    ],
    "ej5_estadio_fin_doble.caos": [
        (_PRECIOS_ESTADIO + [x for venta in _VENTAS_ESTADIO for x in venta] + [-1, -1],
         _SALIDA_ESTADIO),
    ],
    # ------------------------------------------------------------ Grupo 11
    "ej3_llamadas_zona.caos": [
        ([15, 10], L("Costo de la llamada: 22.0")),
        ([23, 3], L("Costo de la llamada: 18.0")),
        ([12, 7], L("Costo de la llamada: 14.0")),
        ([99, 5], L("Clave de zona no valida")),
    ],
    "ej4_ulam.caos": [
        ([6], L(6, 3, 10, 5, 16, 8, 4, 2, 1)),
        ([26], L(26, 13, 40, 20, 10, 5, 16, 8, 4, 2, 1)),
        ([1], L(1)),
    ],
}

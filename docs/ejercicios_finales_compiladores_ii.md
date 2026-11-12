# Ejercicios Finales — Compiladores II

---

## Grupo 1

> **Instrucciones:** Programa en su compilador cada uno de los siguientes ejercicios, tomando en cuenta que el primer ejercicio es secuencial, los ejercicios 2 y 3 son selectivos y el 4 y 5 son repetitivos, así que debe respetar las estructuras de implementación que se mencionaron.

1. Construya un programa tal que dados los datos $A$, $B$, $C$ y $D$ que representan números enteros, escriba los mismos en orden inverso.
2. Construya un programa tal que dado como dato un número entero, determine e imprima si el mismo es positivo ($0$), negativo ($1$) o nulo ($2$).
3. Construya un programa tal que dados como datos de entrada tres números enteros, determine si los mismos están en orden creciente ($1 = \text{Sí}$ o $0 = \text{No}$).
4. Haga un programa que calcule el término número $N$ de la secuencia FIBONACCI. Recuerde que los dos primeros números de la serie son $0$ y $1$. El resto se calcula como la suma de los dos números inmediatos que le preceden.
5. En el centro meteorológico de Argentina se llevan los promedios mensuales de las lluvias caídas en las principales regiones cerealeras del país. Existen 3 regiones importantes denominadas `NORTE`, `CENTRO` y `SUR`. Haga un programa para calcular lo siguiente:
   * a) El promedio anual de la región centro.
   * b) El mes y registro con menor lluvia en la región sur.
   * c) La región con mayor lluvia anual (Considere que los registros anuales de las regiones son diferentes).

---

## Grupo 2

> **Instrucciones:** Programa en su compilador cada uno de los siguientes ejercicios, tomando en cuenta que el primer ejercicio es secuencial, los ejercicios 2 y 3 son selectivos y el 4 y 5 son repetitivos, así que debe respetar las estructuras de implementación que se mencionaron.

1. Dado el ID y 5 calificaciones de un alumno obtenidas a lo largo del semestre, construya un programa que imprima la matrícula del alumno y el promedio de sus calificaciones.
2. El número de sonidos emitidos por un grillo en un minuto, es una función de la temperatura. Como resultado de esto, es posible determinar el nivel de la temperatura haciendo uso de un grillito como termómetro.
   La fórmula para la función es:
   $$T = \frac{N}{4} + 40$$
   Donde $T$ representa la temperatura en grados Fahrenheit y $N$ el número de sonidos emitidos por minuto.  
   Construya un programa que le permita calcular la temperatura, teniendo en cuenta el número de sonidos emitidos por el grillo.
3. En un cierto país el impuesto que se debe pagar por los artículos se calcula mediante la siguiente regla: los primeros $\$20$ no causan impuesto, los siguientes $\$20$ tienen el $30\%$ de impuesto y el resto el $40\%$ de impuesto, pero si el costo del producto es mayor a $\$500$, entonces en lugar del $40\%$ se cobra el $50\%$. Diseñe un diagrama de flujo que lea el costo básico de un artículo y calcule su precio total ($\text{precio total} = \text{precio básico} + \text{impuesto}$).
4. Haga un programa para calcular lo que hay que pagar por un conjunto de llamadas telefónicas. Por cada llamada se ingresa el tipo (Internacional, Nacional, Local) y la duración en minutos. El criterio que se sigue para calcular el costo de cada llamada es el siguiente:
   * **Internacional:** 3 primeros minutos $\$7.59$. Cada minuto adicional $\$3.03$.
   * **Nacional:** 3 primeros minutos $\$1.20$. Cada minuto adicional $\$0.48$.
   * **Local:** Las primeras 50 llamadas no se cobran. Luego, cada llamada cuesta $\$0.60$.
5. En una bodega se tiene información sobre las cantidades producidas de cada tipo de vino, a lo largo de los últimos años. Haga un programa que calcule e imprima lo siguiente:
   * a) El total producido de cada tipo de vino (son 5 tipos) a lo largo de los $N$ años.
   * b) El total producido de vino por año.
   * c) Año en que se produjo la mayor cantidad de litros de vino del tipo 2. Imprimir también la cantidad de litros.
   * d) Verificar si hubo algún año en el cual no se produjo el vino tipo 3. Si existe dicho año, imprimirlo.

---

## Grupo 3

> **Instrucciones:** Programa en su compilador cada uno de los siguientes ejercicios, tomando en cuenta que el primer ejercicio es secuencial, los ejercicios 2 y 3 son selectivos y el 4 y 5 son repetitivos, así que debe respetar las estructuras de implementación que se mencionaron.

1. Construya un programa tal que dados como datos la base y la altura de un rectángulo, calcule el perímetro y el área del mismo.
2. Dados los datos $A$, $B$ y $C$ que representan números enteros diferentes, construya un programa para escribir estos números en forma descendente.
3. Dados como datos tres números reales, identifique cuál es el mayor. Considere que los números pueden ser iguales.
4. Escriba un diagrama de flujo que lea un número entero $N$ y calcule la suma de la siguiente serie:
   $$1^1 + 2^2 + 3^3 + \dots + N^N$$
5. Los datos reunidos en la Secretaría de Industrias relacionado a la producción de $N$ fábricas ($N < 1000$) en cada uno de los meses del año anterior, se proporcionan de la siguiente forma:
   * **Datos:**
     $$N$$
     $$\text{FABRICA}_1, \text{MES}_{1,1}, \text{MES}_{1,2}, \dots, \text{MES}_{1,12}$$
     $$\text{FABRICA}_2, \text{MES}_{2,1}, \text{MES}_{2,2}, \dots, \text{MES}_{2,12}$$
     $$\vdots$$
     $$\text{FABRICA}_N, \text{MES}_{N,1}, \text{MES}_{N,2}, \dots, \text{MES}_{N,12}$$
   * **Donde:**
     * $N$: es una variable de tipo entero que indica el número de fábricas registradas en la Secretaría de Industrias ($N \le 100$).
     * $\text{FABRICA}_i$: es una variable de tipo entero que indica la clave que identifica a la fábrica ($1 \le i \le N$).
     * $\text{MES}_{i,j}$: es una variable de tipo real que representa la producción de la fábrica $i$ en el mes $j$ ($1 \le i \le N$, $1 \le j \le 12$).
   * Haga un programa que calcule lo siguiente:
     * i. Los totales anuales de producción de cada fábrica.
     * ii. La clave de la fábrica que más produjo en el año. Indicar también el total de la producción.
     * iii. Imprimir las claves de las fábricas cuyas producciones en el mes de julio superaron los $\$3\,000\,000$.

---

## Grupo 4

> **Instrucciones:** Programa en su compilador cada uno de los siguientes ejercicios, tomando en cuenta que el primer ejercicio es secuencial, los ejercicios 2 y 3 son selectivos y el 4 y 5 son repetitivos, así que debe respetar las estructuras de implementación que se mencionaron.

1. Escriba un programa tal que dados como datos el peso y la longitud de un dinosaurio expresados estos en libras y pies respectivamente; escriba su peso expresado en kilogramos y su longitud expresada en metros.
2. Construya un programa tal que dados como datos dos variables de tipo entero (`NUM` y `V`), obtenga el resultado de la siguiente función:
   $$\text{VAL} = \begin{cases} 100 \cdot V & \text{si } \text{NUM} = 1 \\ 100^V & \text{si } \text{NUM} = 2 \\ 100 / V & \text{si } \text{NUM} = 3 \\ 0 & \text{para cualquier otro valor de } \text{NUM} \end{cases}$$
3. Escriba un programa que permita calcular lo que hay que pagarle a un trabajador teniendo en cuenta su sueldo y las horas extras trabajadas. Para el pago de horas extras se toma en cuenta la categoría del trabajador. Cada trabajador puede tener como máximo 30 horas extras; si tienen más, sólo se les pagarán 30. A los trabajadores con categoría mayor a 4 no debemos pagarles horas extras.

   **Tabla 2.18**

   | CATEGORÍA | PRECIO HORA EXTRA |
   | :---: | :---: |
   | 1 | $\$30$ |
   | 2 | $\$38$ |
   | 3 | $\$50$ |
   | 4 | $\$70$ |

4. Un vendedor ha hecho una serie de ventas y desea conocer aquellas de $\$200$ o menos, las mayores a $\$200$ pero inferiores a $\$400$, y el número de ventas de $\$400$ o superiores a tal cantidad. Haga un programa que le proporcione al vendedor esta información después de haber leído los datos de entrada.
5. En un estadio se tienen 5 tipos diferentes de localidades, las cuales se identifican por una clave numérica que es un valor comprendido entre 1 y 5. Los precios de cada localidad y los datos referentes a las ventas de boletos para el próximo juego se proporcionan como sigue:
   * **Datos:**
     $$P_1, P_2, P_3, P_4, P_5$$
     $$\text{CLAVE}_1, \text{CANT}_1$$
     $$\text{CLAVE}_2, \text{CANT}_2$$
     $$\vdots$$
     $$-1$$
   * **Donde:**
     * $P_1, P_2, P_3, P_4$ y $P_5$ son variables de tipo real que representan los precios de las localidades 1, 2, 3, 4 y 5, respectivamente.
     * $\text{CLAVE}_i$ es una variable de tipo entero que representa el tipo de localidad de la venta $i$.
     * $\text{CANT}_i$ es una variable de tipo entero que indica la cantidad de boletos vendidos de un cierto tipo, en la venta $i$.
   * Construya un programa que:
     * a) Lea los precios.
     * b) Lea los datos de las ventas de boletos.
     * c) Imprima para cada venta, la clave, la cantidad y el importe total de los boletos vendidos en esta venta.
     * d) Calcule e imprima la cantidad de boletos vendidos de cada tipo.
     * e) Calcule e imprima la recaudación total del estadio.

---

## Grupo 5

> **Instrucciones:** Programa en su compilador cada uno de los siguientes ejercicios, tomando en cuenta que el primer ejercicio es secuencial, los ejercicios 2 y 3 son selectivos y el 4 y 5 son repetitivos, así que debe respetar las estructuras de implementación que se mencionaron.

1. Construya un programa tal que dados como datos el radio y la altura de un cilindro, calcule e imprima el área y su volumen:
   $$\text{Volumen} = \pi \cdot \text{radio}^2 \cdot \text{altura}$$
   $$\text{Área} = 2 \cdot \pi \cdot \text{radio} \cdot \text{altura}$$
2. Construya un programa tal que dado como dato el sueldo de un trabajador, le aplique un aumento del $15\%$ si su sueldo es inferior a $\$1000$ y $12\%$ en caso contrario. Imprima el nuevo sueldo del trabajador.
3. Construya un programa tal que dados como datos la matrícula de un alumno, la carrera en la que está inscrito, su semestre y su promedio; determine si el mismo es apto para pertenecer a alguna de las facultades menores que tiene la universidad. Si el alumno es aceptado teniendo en cuenta las especificaciones que se listan abajo, se debe imprimir su matrícula, carrera y la palabra `"Aceptado = 1"`.
   * **Especificaciones para pertenecer a las facultades menores:**
     * **Economía:** $\text{Semestre} \ge 6$ y $\text{promedio} \ge 8.8$
     * **Computación:** $\text{Semestre} > 6$ y $\text{promedio} > 8.5$
     * **Administración:** $\text{Semestre} > 5$ y $\text{promedio} > 8.5$
     * **Contabilidad:** $\text{Semestre} > 5$ y $\text{promedio} > 8.5$
4. Construya un programa tal que dados $N$ números enteros como dato, calcule y muestre el mayor y el menor de estos números.
5. En una bodega se tiene información sobre las cantidades producidas de cada tipo de vino, a lo largo de los últimos años. Haga un diagrama de flujo que calcule e imprima lo siguiente:
   * a) El total producido de cada tipo de vino (son 5 tipos) a lo largo de los $N$ años.
   * b) El total producido de vino por año.
   * c) Año en que se produjo la mayor cantidad de litros de vino del tipo 2. Imprimir también la cantidad de litros.
   * d) Verificar si hubo algún año en el cual no se produjo el vino tipo 3. Si existe dicho año, imprimirlo.

---

## Grupo 6

> **Instrucciones:** Programa en su compilador cada uno de los siguientes ejercicios, tomando en cuenta que el primer ejercicio es secuencial, los ejercicios 2 y 3 son selectivos y el 4 y 5 son repetitivos, así que debe respetar las estructuras de implementación que se mencionaron.

1. Construya un programa que calcule e imprima el número de segundos que hay en un determinado número de días.
2. Construya un programa tal que dado como dato la calificación de un alumno en un examen, escriba `"aprobado = 1"` si su calificación es mayor o igual que $8$ y `"reprobado = 0"` en caso contrario.
3. En un hospital se ha hecho un estudio sobre los pacientes registrados durante los últimos 10 años, con el objeto de hacer una aproximación de los costos de internación por paciente. Se obtuvo un costo promedio diario según el tipo de enfermedad que aqueja al paciente. Además se pudo determinar que en promedio todos los pacientes con edad entre 14 y 22 años implican un costo adicional del $10\%$. La siguiente tabla expresa los costos diarios, según el tipo de enfermedad.

   **Tabla 2.21**

   | TIPO DE ENFERMEDAD | COSTO/PACIENTE/DÍA |
   | :---: | :---: |
   | 1 | $25$ |
   | 2 | $16$ |
   | 3 | $20$ |
   | 4 | $32$ |

   Construya un programa que calcule e imprima el costo total que representa un paciente.
4. Escriba un programa que lea un número entero $N$ y calcule el resultado de la siguiente serie:
   $$1 - \frac{1}{2} + \frac{1}{3} - \frac{1}{4} + \dots \pm \frac{1}{N}$$
5. Los datos reunidos en la Secretaría de Industrias relacionado a la producción de $N$ fábricas ($N < 1000$) en cada uno de los meses del año anterior, se proporcionan de la siguiente forma:
   * **Datos:**
     $$N$$
     $$\text{FABRICA}_1, \text{MES}_{1,1}, \text{MES}_{1,2}, \dots, \text{MES}_{1,12}$$
     $$\text{FABRICA}_2, \text{MES}_{2,1}, \text{MES}_{2,2}, \dots, \text{MES}_{2,12}$$
     $$\vdots$$
     $$\text{FABRICA}_N, \text{MES}_{N,1}, \text{MES}_{N,2}, \dots, \text{MES}_{N,12}$$
   * **Donde:**
     * $N$: es una variable de tipo entero que indica el número de fábricas registradas en la Secretaría de Industrias ($N \le 100$).
     * $\text{FABRICA}_i$: es una variable de tipo entero que indica la clave que identifica a la fábrica ($1 \le i \le N$).
     * $\text{MES}_{i,j}$: es una variable de tipo real que representa la producción de la fábrica $i$ en el mes $j$ ($1 \le i \le N$, $1 \le j \le 12$).
   * Haga un programa que calcule lo siguiente:
     * d) Los totales anuales de producción de cada fábrica.
     * e) La clave de la fábrica que más produjo en el año. Indicar también el total de la producción.
     * f) Imprimir las claves de las fábricas cuyas producciones en el mes de julio superaron los $\$3\,000\,000$.

---

## Grupo 7

> **Instrucciones:** Programa en su compilador cada uno de los siguientes ejercicios, tomando en cuenta que el primer ejercicio es secuencial, los ejercicios 2 y 3 son selectivos y el 4 y 5 son repetitivos, así que debe respetar las estructuras de implementación que se mencionaron.

1. Construya un programa tal que dados los datos enteros $A$ y $B$, escriba el resultado de la siguiente expresión:
   $$\frac{(A + B)^2}{3}$$
2. Construya un programa tal que dado como dato un número entero, determine e imprima si el mismo es positivo ($0$), negativo ($1$) o nulo ($2$).
3. Construya un programa tal que dados como datos de entrada tres números enteros, los imprima en orden creciente.
4. Supóngase que en una reciente elección hubo cuatro candidatos (con identificadores 1, 2, 3, 4). Usted habrá de encontrar, mediante un programa, el número de votos correspondiente a cada candidato y el porcentaje que obtuvo respecto al total de los votantes. El usuario tecleará los votos de manera desorganizada, tal y como se obtuvieron en la elección; el final de datos está representado por un cero.  
   Observe, como ejemplo, la siguiente lista:  
   `1 3 1 4 2 2 1 4 1 1 1 2 1 3 1 4 0`  
   Donde `1` representa un voto para el candidato 1; `3` un voto para el candidato 3; y así sucesivamente.
5. Los datos reunidos en la Secretaría de Industrias relacionado a la producción de $N$ fábricas ($N < 1000$) en cada uno de los meses del año anterior, se proporcionan de la siguiente forma:
   * **Datos:**
     $$N$$
     $$\text{FABRICA}_1, \text{MES}_{1,1}, \text{MES}_{1,2}, \dots, \text{MES}_{1,12}$$
     $$\text{FABRICA}_2, \text{MES}_{2,1}, \text{MES}_{2,2}, \dots, \text{MES}_{2,12}$$
     $$\vdots$$
     $$\text{FABRICA}_N, \text{MES}_{N,1}, \text{MES}_{N,2}, \dots, \text{MES}_{N,12}$$
   * **Donde:**
     * $N$: es una variable de tipo entero que indica el número de fábricas registradas en la Secretaría de Industrias ($N \le 100$).
     * $\text{FABRICA}_i$: es una variable de tipo entero que indica la clave que identifica a la fábrica ($1 \le i \le N$).
     * $\text{MES}_{i,j}$: es una variable de tipo real que representa la producción de la fábrica $i$ en el mes $j$ ($1 \le i \le N$, $1 \le j \le 12$).
   * Haga un programa que calcule lo siguiente:
     * g) Los totales anuales de producción de cada fábrica.
     * h) La clave de la fábrica que más produjo en el año. Indicar también el total de la producción.
     * i) Imprimir las claves de las fábricas cuyas producciones en el mes de julio superaron los $\$3\,000\,000$.

---

## Grupo 8

> **Instrucciones:** Programa en su compilador cada uno de los siguientes ejercicios, tomando en cuenta que el primer ejercicio es secuencial, los ejercicios 2 y 3 son selectivos y el 4 y 5 son repetitivos, así que debe respetar las estructuras de implementación que se mencionaron.

1. Construya un programa tal que dado el costo de un artículo vendido y la cantidad de dinero entregada por el cliente, calcule e imprima el cambio que se debe entregar al mismo.
2. Construya un programa tal que dados como datos los valores enteros $P$ y $Q$, determine si los mismos satisfacen la siguiente expresión:
   $$P^3 + Q^4 - 2 \cdot P^2 < 680$$
3. En una tienda efectúan un descuento a los clientes dependiendo del monto de la compra. El descuento se efectúa con base en el siguiente criterio:
   * Si el monto es menor que $\$500$: no hay descuento.
   * Si el monto está comprendido entre $\$500$ y $\$1\,000$ inclusive: $5\%$ de descuento.
   * Si el monto está comprendido entre $\$1\,000$ y $\$7\,000$ inclusive: $11\%$ de descuento.
   * Si el monto está comprendido entre $\$7\,000$ y $\$15\,000$ inclusive: $18\%$ de descuento.
   * Si el monto es mayor a $\$15\,000$: $25\%$ de descuento.
   
   Construya un programa tal que dado el monto de la compra de un cliente, determine lo que el mismo debe pagar.
4. Escriba un programa tal que dados como datos $N$ números enteros, obtenga el número de ceros que hay entre estos números; el fin de datos se da cuando se introduce un $-1$.
5. En una bodega se tiene información sobre las cantidades producidas de cada tipo de vino, a lo largo de los últimos años. Haga un diagrama de flujo que calcule e imprima lo siguiente:
   * j) El total producido de cada tipo de vino (son 5 tipos) a lo largo de los $N$ años.
   * k) El total producido de vino por año.
   * l) Año en que se produjo la mayor cantidad de litros de vino del tipo 2. Imprimir también la cantidad de litros.
   * m) Verificar si hubo algún año en el cual no se produjo el vino tipo 3. Si existe dicho año, imprimirlo.

---

## Grupo 9

> **Instrucciones:** Programa en su compilador cada uno de los siguientes ejercicios, tomando en cuenta que el primer ejercicio es secuencial, los ejercicios 2 y 3 son selectivos y el 4 y 5 son repetitivos, así que debe respetar las estructuras de implementación que se mencionaron.

1. Construya un programa tal que dados como datos el radio y la altura de un cilindro, calcule e imprima el área y su volumen:
   $$\text{Volumen} = \pi \cdot \text{radio}^2 \cdot \text{altura}$$
   $$\text{Área} = 2 \cdot \pi \cdot \text{radio} \cdot \text{altura}$$
2. El número de sonidos emitidos por un grillo en un minuto, es una función de la temperatura. Como resultado de esto, es posible determinar el nivel de la temperatura haciendo uso de un grillito como termómetro.
   La fórmula para la función es:
   $$T = \frac{N}{4} + 40$$
   Donde $T$ representa la temperatura en grados Fahrenheit y $N$ el número de sonidos emitidos por minuto.  
   Construya un programa que le permita calcular la temperatura, teniendo en cuenta el número de sonidos emitidos por el grillo.
3. En un cierto país el impuesto que se debe pagar por los artículos se calcula mediante la siguiente regla: los primeros $\$20$ no causan impuesto, los siguientes $\$20$ tienen el $30\%$ de impuesto y el resto el $40\%$ de impuesto, pero si el costo del producto es mayor a $\$500$, entonces en lugar del $40\%$ se cobra el $50\%$. Diseñe un diagrama de flujo que lea el costo básico de un artículo y calcule su precio total ($\text{precio total} = \text{precio básico} + \text{impuesto}$).
4. Se dice que un entero positivo $N$ es un número primo si los únicos enteros positivos que lo dividen son exactamente $1$ y $N$. Diseñe un programa que lea un número $M$, y obtenga y cuente todos los números primos menores a $M$.
5. En el centro meteorológico de Argentina se llevan los promedios mensuales de las lluvias caídas en las principales regiones cerealeras del país. Existen 3 regiones importantes denominadas `NORTE`, `CENTRO` y `SUR`. Haga un programa para calcular lo siguiente:
   * n) El promedio anual de la región centro.
   * o) El mes y registro con menor lluvia en la región sur.
   * p) La región con mayor lluvia anual (Considere que los registros anuales de las regiones son diferentes).

---

## Grupo 10

> **Instrucciones:** Programa en su compilador cada uno de los siguientes ejercicios, tomando en cuenta que el primer ejercicio es secuencial, los ejercicios 2 y 3 son selectivos y el 4 y 5 son repetitivos, así que debe respetar las estructuras de implementación que se mencionaron.

1. Construya un programa tal que dados como datos la base y la altura de un rectángulo, calcule el perímetro y el área del mismo.
2. Construya un programa tal que dados como datos la categoría y el sueldo de un trabajador, calcule el aumento correspondiente teniendo en cuenta la siguiente tabla. Imprima la categoría del trabajador y su nuevo sueldo.

   **Tabla 2.6**

   | CATEGORÍA | AUMENTO |
   | :---: | :---: |
   | 1 | $15\%$ |
   | 2 | $10\%$ |
   | 3 | $8\%$ |
   | 4 | $7\%$ |

3. Dados como datos tres números reales, identifique cuál es el mayor. Considere que los números pueden ser iguales.
4. Un número es perfecto si *"la suma de sus divisores excepto él mismo es igual al propio número"*. Haga un programa para calcular e imprimir los números perfectos menores o iguales que $N$.
5. En un estadio se tienen 5 tipos diferentes de localidades, las cuales se identifican por una clave numérica que es un valor comprendido entre 1 y 5. Los precios de cada localidad y los datos referentes a las ventas de boletos para el próximo juego se proporcionan como sigue:
   * **Datos:**
     $$P_1, P_2, P_3, P_4, P_5$$
     $$\text{CLAVE}_1, \text{CANT}_1$$
     $$\text{CLAVE}_2, \text{CANT}_2$$
     $$\vdots$$
     $$-1, -1$$
   * **Donde:**
     * $P_1, P_2, P_3, P_4$ y $P_5$ son variables de tipo real que representan los precios de las localidades 1, 2, 3, 4 y 5, respectivamente.
     * $\text{CLAVE}_i$ es una variable de tipo entero que representa el tipo de localidad de la venta $i$.
     * $\text{CANT}_i$ es una variable de tipo entero que indica la cantidad de boletos vendidos de un cierto tipo, en la venta $i$.
   * Construya un programa que:
     * Lea los precios.
     * Lea los datos de las ventas de boletos.
     * Imprima para cada venta, la clave, la cantidad y el importe total de los boletos vendidos en esta venta.
     * Calcule e imprima la cantidad de boletos vendidos de cada tipo.
     * Calcule e imprima la recaudación total del estadio.

---

## Grupo 11

> **Instrucciones:** Programa en su compilador cada uno de los siguientes ejercicios, tomando en cuenta que el primer ejercicio es secuencial, los ejercicios 2 y 3 son selectivos y el 4 y 5 son repetitivos, así que debe respetar las estructuras de implementación que se mencionaron.

1. Construya un programa tal que dado el costo de un artículo vendido y la cantidad de dinero entregada por el cliente, calcule e imprima el cambio que se debe entregar al mismo.
2. Construya un programa tal que dados como datos la categoría y el sueldo de un trabajador, calcule el aumento correspondiente teniendo en cuenta la siguiente tabla. Imprima la categoría del trabajador y su nuevo sueldo.

   **Tabla 2.6**

   | CATEGORÍA | AUMENTO |
   | :---: | :---: |
   | 1 | $15\%$ |
   | 2 | $10\%$ |
   | 3 | $8\%$ |
   | 4 | $7\%$ |

3. El costo de las llamadas telefónicas internacionales depende de la zona geográfica en la que se encuentre el país destino y del número de minutos hablados. En la siguiente tabla se presenta el costo del minuto por zona. A cada zona se le ha asociado una clave.

   **Tabla 2.16**

   | CLAVE | ZONA | PRECIO |
   | :---: | :--- | :---: |
   | 12 | América del Norte | $2$ |
   | 15 | América Central | $2.2$ |
   | 18 | América del Sur | $4.5$ |
   | 19 | Europa | $3.5$ |
   | 23 | Asia | $6$ |
   | 25 | África | $6$ |
   | 29 | Oceanía | $5$ |

   Construya un programa que le permita calcular e imprimir el costo total de una llamada.
4. La siguiente se llama la conjetura de ULAM en honor del matemático S. Ulam:
   * Comience con cualquier entero positivo.
   * Si es par, divídalo entre $2$; si es impar, multiplíquelo por $3$ y agréguele $1$.
   * Obtenga enteros sucesivamente repitiendo el proceso.
   * Al final, obtendrá el número $1$, independientemente del entero inicial. Por ejemplo, cuando el entero inicial es $26$, la secuencia será: `26, 13, 40, 20, 10, 5, 16, 8, 4, 2, 1`.
   
   Construya un programa que lea un entero positivo y obtenga e imprima la sucesión de ULAM.
5. En el centro meteorológico de Argentina se llevan los promedios mensuales de las lluvias caídas en las principales regiones cerealeras del país. Existen 3 regiones importantes denominadas `NORTE`, `CENTRO` y `SUR`. Haga un programa para calcular lo siguiente:
   * El promedio anual de la región centro.
   * El mes y registro con menor lluvia en la región sur.
   * La región con mayor lluvia anual (Considere que los registros anuales de las regiones son diferentes).

---

## Grupo 12

> **Instrucciones:** Programa en su compilador cada uno de los siguientes ejercicios, tomando en cuenta que el primer ejercicio es secuencial, los ejercicios 2 y 3 son selectivos y el 4 y 5 son repetitivos, así que debe respetar las estructuras de implementación que se mencionaron.

1. Construya un programa tal que dados los datos enteros $A$ y $B$, escriba el resultado de la siguiente expresión:
   $$\frac{(A + B)^2}{3}$$
2. Construya un programa tal que dados como datos los valores enteros $P$ y $Q$, determine si los mismos satisfacen la siguiente expresión:
   $$P^3 + Q^4 - 2 \cdot P^2 < 680$$
3. En una tienda efectúan un descuento a los clientes dependiendo del monto de la compra. El descuento se efectúa con base en el siguiente criterio:
   * Si el monto es menor que $\$500$: no hay descuento.
   * Si el monto está comprendido entre $\$500$ y $\$1\,000$ inclusive: $5\%$ de descuento.
   * Si el monto está comprendido entre $\$1\,000$ y $\$7\,000$ inclusive: $11\%$ de descuento.
   * Si el monto está comprendido entre $\$7\,000$ y $\$15\,000$ inclusive: $18\%$ de descuento.
   * Si el monto es mayor a $\$15\,000$: $25\%$ de descuento.
   
   Construya un programa tal que dado el monto de la compra de un cliente, determine lo que el mismo debe pagar.
4. Supóngase que en una reciente elección hubo cuatro candidatos (con identificadores 1, 2, 3, 4). Usted habrá de encontrar, mediante un programa, el número de votos correspondiente a cada candidato y el porcentaje que obtuvo respecto al total de los votantes. El usuario tecleará los votos de manera desorganizada, tal y como se obtuvieron en la elección; el final de datos está representado por un cero.  
   Observe, como ejemplo, la siguiente lista:  
   `1 3 1 4 2 2 1 4 1 1 1 2 1 3 1 4 0`  
   Donde `1` representa un voto para el candidato 1; `3` un voto para el candidato 3; y así sucesivamente.
5. En un estadio se tienen 5 tipos diferentes de localidades, las cuales se identifican por una clave numérica que es un valor comprendido entre 1 y 5. Los precios de cada localidad y los datos referentes a las ventas de boletos para el próximo juego se proporcionan como sigue:
   * **Datos:**
     $$P_1, P_2, P_3, P_4, P_5$$
     $$\text{CLAVE}_1, \text{CANT}_1$$
     $$\text{CLAVE}_2, \text{CANT}_2$$
     $$\vdots$$
     $$-1$$
   * **Donde:**
     * $P_1, P_2, P_3, P_4$ y $P_5$ son variables de tipo real que representan los precios de las localidades 1, 2, 3, 4 y 5, respectivamente.
     * $\text{CLAVE}_i$ es una variable de tipo entero que representa el tipo de localidad de la venta $i$.
     * $\text{CANT}_i$ es una variable de tipo entero que indica la cantidad de boletos vendidos de un cierto tipo, en la venta $i$.
   * Construya un programa que:
     * q) Lea los precios.
     * r) Lea los datos de las ventas de boletos.
     * s) Imprima para cada venta, la clave, la cantidad y el importe total de los boletos vendidos en esta venta.
     * t) Calcule e imprima la cantidad de boletos vendidos de cada tipo.
     * u) Calcule e imprima la recaudación total del estadio.
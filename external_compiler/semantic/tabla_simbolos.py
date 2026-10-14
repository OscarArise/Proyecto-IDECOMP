"""
tabla_simbolos.py
-----------------
Tabla de símbolos del lenguaje CAOS.

Se implementa como la tabla del compilador TINY (Louden), revisada en clase con
TablaHash_Probar.cpp: una tabla hash de tamaño fijo con encadenamiento separado
para resolver colisiones. Se extiende con lo que TINY no tiene: el tipo de dato
de cada identificador y la posición de su declaración.

Cada entrada (cubeta) guarda:
    nombre         lexema del identificador
    tipo           int | float | bool (atributo heredado dtype de la declaración)
    loc            desplazamiento de memoria, asignado en orden de declaración
    linea_decl     línea y columna donde se declaró
    lineas         una línea por cada aparición del identificador (declaración
                   y cada uso). Si aparece dos veces en la misma línea, el número
                   se repite, igual que en st_insert de TINY.
    valor          último valor conocido en compilación (None si no se puede
                   determinar: sin asignar, leído con cin o modificado en un ciclo)
    siguiente      siguiente cubeta de la misma posición hash (encadenamiento)

El lenguaje tiene un solo ámbito (el bloque main), así que basta una tabla.
"""

from dataclasses import dataclass, field
from typing import Any, Iterator, List, Optional

SIZE = 211   # número primo, igual que en TINY
SHIFT = 4    # desplazamiento de la función hash de TINY


def funcion_hash(clave: str) -> int:
    """Función hash de TINY: temp = ((temp << SHIFT) + c) % SIZE."""
    temp = 0
    for caracter in clave:
        temp = ((temp << SHIFT) + ord(caracter)) % SIZE
    return temp


@dataclass
class Simbolo:
    nombre: str
    tipo: str
    loc: int
    linea_decl: int
    columna_decl: int
    lineas: List[int] = field(default_factory=list)
    valor: Any = None
    siguiente: Optional["Simbolo"] = field(default=None, repr=False)

    @property
    def hash(self) -> int:
        return funcion_hash(self.nombre)


class TablaSimbolos:
    """Tabla hash con encadenamiento: insertar, buscar, agregar línea, eliminar."""

    def __init__(self, size: int = SIZE):
        self._cubetas: List[Optional[Simbolo]] = [None] * size
        self._siguiente_loc = 0

    # ------------------------------------------------------------------
    # Operaciones
    # ------------------------------------------------------------------

    def insertar(self, nombre: str, tipo: str, linea: int, columna: int = 0) -> Simbolo:
        """
        Inserta un identificador declarado y le asigna la siguiente localidad.
        Quien llama debe verificar antes con buscar() que no exista (E2).
        """
        posicion = funcion_hash(nombre)
        simbolo = Simbolo(
            nombre=nombre,
            tipo=tipo,
            loc=self._siguiente_loc,
            linea_decl=linea,
            columna_decl=columna,
            lineas=[linea],
        )
        # Se inserta al inicio de la lista de la cubeta, como en TINY
        simbolo.siguiente = self._cubetas[posicion]
        self._cubetas[posicion] = simbolo
        self._siguiente_loc += 1
        return simbolo

    def buscar(self, nombre: str) -> Optional[Simbolo]:
        """Recorre la lista de la cubeta; None si el identificador no existe."""
        simbolo = self._cubetas[funcion_hash(nombre)]
        while simbolo is not None and simbolo.nombre != nombre:
            simbolo = simbolo.siguiente
        return simbolo

    def agregar_linea(self, nombre: str, linea: int) -> bool:
        """
        Registra una aparición del identificador. Cada aparición agrega su
        línea, aunque ya esté en la lista (x = x + 1 en la línea 9 → 9, 9).
        False si no existe.
        """
        simbolo = self.buscar(nombre)
        if simbolo is None:
            return False
        simbolo.lineas.append(linea)
        return True

    def asignar_valor(self, nombre: str, valor: Any) -> bool:
        """Actualiza el valor conocido del identificador. False si no existe."""
        simbolo = self.buscar(nombre)
        if simbolo is None:
            return False
        simbolo.valor = valor
        return True

    def eliminar(self, nombre: str) -> bool:
        """
        Elimina un identificador. El análisis no la necesita porque el lenguaje
        tiene un solo ámbito, pero forma parte de las operaciones de la tabla.
        """
        posicion = funcion_hash(nombre)
        anterior = None
        actual = self._cubetas[posicion]
        while actual is not None:
            if actual.nombre == nombre:
                if anterior is None:
                    self._cubetas[posicion] = actual.siguiente
                else:
                    anterior.siguiente = actual.siguiente
                return True
            anterior, actual = actual, actual.siguiente
        return False

    # ------------------------------------------------------------------
    # Consulta
    # ------------------------------------------------------------------

    def simbolos(self) -> List[Simbolo]:
        """Todos los símbolos, ordenados por localidad de memoria."""
        return sorted(self._iterar(), key=lambda s: s.loc)

    def _iterar(self) -> Iterator[Simbolo]:
        for cubeta in self._cubetas:
            simbolo = cubeta
            while simbolo is not None:
                yield simbolo
                simbolo = simbolo.siguiente

    def __contains__(self, nombre: str) -> bool:
        return self.buscar(nombre) is not None

    def __len__(self) -> int:
        return sum(1 for _ in self._iterar())

"""
code.py
-------
Utilidades de emisión de código TM. Port de code.c / code.h del compilador
TINY (Louden) para el compilador CAOS.

Convenciones de registros (code.h):
    pc  = 7   contador del programa
    mp  = 6   "memory pointer": tope de memoria, base de los temporales
    gp  = 5   "global pointer": base de las variables globales
    ac  = 0   acumulador
    ac1 = 1   segundo acumulador

Como en code.c, cada instrucción se escribe en el momento en que se emite.
Por eso una instrucción reservada con emit_skip y completada después con
emit_backup / emit_restore aparece físicamente más abajo en el archivo .tm;
la TM la carga en su dirección y la ejecuta en el orden correcto.
"""

from typing import List, Union

pc = 7
mp = 6
gp = 5
ac = 0
ac1 = 1

Numero = Union[int, float]


def formato_numero(valor: Numero) -> str:
    """Desplazamiento o constante tal como lo lee la TM (entero o real)."""
    if isinstance(valor, bool):
        return "1" if valor else "0"
    if isinstance(valor, int):
        return str(valor)
    return repr(float(valor))


class Emisor:
    """
    Equivale a las variables estáticas y funciones de code.c:
    emitLoc, highEmitLoc, emitComment, emitRO, emitRM, emitSkip,
    emitBackup, emitRestore y emitRM_Abs.
    """

    def __init__(self, trace_code: bool = True):
        self.trace_code = trace_code
        self.emit_loc = 0        # posición TM de la instrucción que se emite
        self.high_emit_loc = 0   # posición más alta emitida hasta ahora
        self.lineas: List[str] = []

    def texto(self) -> str:
        return "\n".join(self.lineas) + "\n"

    def emit_comment(self, c: str) -> None:
        """Línea de comentario (solo si trace_code está activo)."""
        if self.trace_code:
            self.lineas.append(f"* {c}")

    def _instruccion(self, linea: str, c: str) -> None:
        if self.trace_code and c:
            linea += f"\t{c}"
        self.lineas.append(linea)
        self.emit_loc += 1
        if self.high_emit_loc < self.emit_loc:
            self.high_emit_loc = self.emit_loc

    def emit_ro(self, op: str, r: int, s: int, t: int, c: str = "") -> None:
        """Instrucción de solo registros: op r,s,t"""
        self._instruccion(f"{self.emit_loc:3d}:  {op:>5}  {r},{s},{t} ", c)

    def emit_rm(self, op: str, r: int, d: Numero, s: int, c: str = "") -> None:
        """Instrucción registro-memoria: op r,d(s)"""
        self._instruccion(f"{self.emit_loc:3d}:  {op:>5}  {r},{formato_numero(d)}({s}) ", c)

    def emit_skip(self, how_many: int) -> int:
        """Reserva how_many posiciones para parcharlas después; devuelve la actual."""
        i = self.emit_loc
        self.emit_loc += how_many
        if self.high_emit_loc < self.emit_loc:
            self.high_emit_loc = self.emit_loc
        return i

    def emit_backup(self, loc: int) -> None:
        """Regresa a una posición reservada previamente."""
        if loc > self.high_emit_loc:
            self.emit_comment("BUG in emitBackup")
        self.emit_loc = loc

    def emit_restore(self) -> None:
        """Vuelve a la posición más alta no emitida."""
        self.emit_loc = self.high_emit_loc

    def emit_rm_abs(self, op: str, r: int, a: int, c: str = "") -> None:
        """Convierte la dirección absoluta a en un desplazamiento relativo a pc."""
        self._instruccion(
            f"{self.emit_loc:3d}:  {op:>5}  {r},{a - (self.emit_loc + 1)}({pc}) ", c
        )

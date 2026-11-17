"""
tm.py
-----
Simulador de la TM (Tiny Machine) de Louden, port a Python de tm/tm.c.

Implementa la misma TM extendida para CAOS que tm/tm.c:
    - registros y memoria de datos con valores reales (float de Python = double de C)
    - LDC acepta constantes reales: LDC 0,3.14(0)
    - DIV conserva la división entera (trunca hacia cero)
    - INF r,0,0     lee un número real          (IN lee solo enteros)
    - OUTF r,0,0    imprime un real
    - OUTLN 0,0,0   imprime un salto de línea
    - DIVF r,s,t    división real
    - POW r,s,t     reg(r) = reg(s) ^ reg(t)
    - OUTS r,d(s)   imprime la cadena terminada en 0 que inicia en dMem[d+reg(s)]

La clase TMSimulator separa la máquina de la interfaz: la entrada y la salida
se resuelven con callbacks, así la usan tanto el IDE como la línea de comandos.

Uso desde consola (mismos comandos que tm.c):
    python tm.py programa.tm
"""

from __future__ import annotations

import math
import re
import sys
from typing import Callable, List, Optional

IADDR_SIZE = 8192
DADDR_SIZE = 4096
NO_REGS = 8
PC_REG = 7

RR_OPS = ("HALT", "IN", "OUT", "ADD", "SUB", "MUL", "DIV",
          "INF", "OUTF", "OUTLN", "DIVF", "POW")
RM_OPS = ("LD", "ST", "OUTS")
RA_OPS = ("LDA", "LDC", "JLT", "JLE", "JGT", "JGE", "JEQ", "JNE")

# Resultados de un paso, con los mismos textos que stepResultTab de tm.c
OKAY = "OK"
HALT = "Halted"
IMEM_ERR = "Instruction Memory Fault"
DMEM_ERR = "Data Memory Fault"
ZERODIVIDE = "Division by 0"
INPUT_CANCELLED = "Input cancelled"
STEP_LIMIT = "Step limit reached"

_NUM = r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?"
_RE_LOC = re.compile(r"\s*(\d+)\s*:\s*([A-Za-z0-9]*)")
_RE_RR = re.compile(r"\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)")
_RE_RM = re.compile(rf"\s*(-?\d+)\s*,\s*({_NUM})\s*[(,]\s*(-?\d+)")


class TMLoadError(Exception):
    """Error al cargar un archivo .tm (mismo mensaje que tm.c)."""


def format_real(v: float) -> str:
    """Hasta 6 decimales, sin ceros sobrantes, mínimo x.0 (igual que formatReal de tm.c)."""
    if math.isnan(v):
        return "nan"
    if math.isinf(v):
        return "inf" if v > 0 else "-inf"
    texto = f"{v:.6f}".rstrip("0")
    if texto.endswith("."):
        texto += "0"
    return "0.0" if texto == "-0.0" else texto


def format_int(v: float) -> str:
    if not math.isfinite(v):
        return format_real(v)
    return str(int(v))


def format_value(v: float) -> str:
    """Valor de registro o memoria para los comandos r y d."""
    if math.isfinite(v) and v == math.floor(v) and abs(v) < 1e15:
        return str(int(v))
    return format_real(v)


def parse_input(texto: str, real: bool) -> Optional[float]:
    """Valida la entrada de IN (entero) o INF (real). None si es ilegal."""
    texto = texto.strip()
    if not re.fullmatch(_NUM, texto):
        return None
    valor = float(texto)
    if not math.isfinite(valor):
        return None
    if not real and valor != math.floor(valor):
        return None
    return valor


class Instruction:
    __slots__ = ("op", "a1", "a2", "a3")

    def __init__(self, op: str = "HALT", a1: int = 0, a2: float = 0, a3: int = 0):
        self.op, self.a1, self.a2, self.a3 = op, a1, a2, a3

    def __str__(self) -> str:
        if self.op in RR_OPS:
            return f"{self.op:>6}{self.a1:3d},{int(self.a2)},{self.a3}"
        return f"{self.op:>6}{self.a1:3d},{format_value(self.a2):>3}({self.a3})"


class TMSimulator:
    """
    Máquina TM. `on_input(real)` debe devolver el valor leído (float) o None
    para cancelar; `on_output(texto)` recibe lo que imprimen OUT/OUTF/OUTS/OUTLN.
    """

    def __init__(self,
                 on_input: Optional[Callable[[bool], Optional[float]]] = None,
                 on_output: Optional[Callable[[str], None]] = None):
        self.on_input = on_input
        self.on_output = on_output or (lambda texto: None)
        self.i_mem: List[Instruction] = [Instruction() for _ in range(IADDR_SIZE)]
        self.d_mem: List[float] = [0.0] * DADDR_SIZE
        self.reg: List[float] = [0.0] * NO_REGS
        self.steps = 0
        self.reset()

    # ------------------------------------------------------------------
    # Carga del programa
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Equivale al comando c(lear) de tm.c."""
        self.reg = [0.0] * NO_REGS
        self.d_mem = [0.0] * DADDR_SIZE
        self.d_mem[0] = float(DADDR_SIZE - 1)
        self.steps = 0

    def load(self, texto: str) -> None:
        """Lee las instrucciones de un .tm. Lanza TMLoadError como readInstructions."""
        self.i_mem = [Instruction() for _ in range(IADDR_SIZE)]
        self.reset()
        for numero, linea in enumerate(texto.splitlines(), 1):
            contenido = linea.strip()
            if not contenido or contenido.startswith("*"):
                continue
            m = _RE_LOC.match(linea)
            if not m:
                raise TMLoadError(f"Line {numero}   Bad location")
            loc = int(m.group(1))
            if loc >= IADDR_SIZE:
                raise TMLoadError(f"Line {numero} (Instruction {loc})   Location too large")
            op = m.group(2)
            if not op:
                raise TMLoadError(f"Line {numero} (Instruction {loc})   Missing opcode")
            resto = linea[m.end():]
            if op in RR_OPS:
                ops = _RE_RR.match(resto)
            elif op in RM_OPS or op in RA_OPS:
                ops = _RE_RM.match(resto)
            else:
                raise TMLoadError(f"Line {numero} (Instruction {loc})   Illegal opcode")
            if not ops:
                raise TMLoadError(f"Line {numero} (Instruction {loc})   Bad operands")
            a1, a2, a3 = int(ops.group(1)), float(ops.group(2)), int(ops.group(3))
            registros = (a1, a3) if op not in RR_OPS else (a1, int(a2), a3)
            if any(r < 0 or r >= NO_REGS for r in registros):
                raise TMLoadError(f"Line {numero} (Instruction {loc})   Bad register")
            self.i_mem[loc] = Instruction(op, a1, a2, a3)

    # ------------------------------------------------------------------
    # Ejecución
    # ------------------------------------------------------------------

    def step(self) -> str:
        """Ejecuta una instrucción (stepTM). Devuelve el resultado del paso."""
        pc = int(self.reg[PC_REG])
        if pc < 0 or pc >= IADDR_SIZE:
            return IMEM_ERR
        self.reg[PC_REG] = float(pc + 1)
        ins = self.i_mem[pc]
        op, r = ins.op, ins.a1
        self.steps += 1
        reg = self.reg

        if op in RR_OPS:
            s, t = int(ins.a2), ins.a3
            if op == "HALT":
                return HALT
            if op in ("IN", "INF"):
                if self.on_input is None:
                    return INPUT_CANCELLED
                valor = self.on_input(op == "INF")
                if valor is None:
                    return INPUT_CANCELLED
                reg[r] = float(valor)
            elif op == "OUT":
                self.on_output(format_int(reg[r]))
            elif op == "OUTF":
                self.on_output(format_real(reg[r]))
            elif op == "OUTLN":
                self.on_output("\n")
            elif op == "ADD":
                reg[r] = reg[s] + reg[t]
            elif op == "SUB":
                reg[r] = reg[s] - reg[t]
            elif op == "MUL":
                reg[r] = reg[s] * reg[t]
            elif op == "DIV":
                if reg[t] == 0:
                    return ZERODIVIDE
                reg[r] = float(math.trunc(reg[s] / reg[t]))
            elif op == "DIVF":
                if reg[t] == 0:
                    return ZERODIVIDE
                reg[r] = reg[s] / reg[t]
            elif op == "POW":
                reg[r] = _pow(reg[s], reg[t])
            return OKAY

        s = ins.a3
        m = int(ins.a2 + reg[s])

        if op in RM_OPS:
            if m < 0 or m >= DADDR_SIZE:
                return DMEM_ERR
            if op == "LD":
                reg[r] = self.d_mem[m]
            elif op == "ST":
                self.d_mem[m] = reg[r]
            elif op == "OUTS":
                caracteres = []
                while m < DADDR_SIZE and self.d_mem[m] != 0:
                    caracteres.append(chr(int(self.d_mem[m])))
                    m += 1
                self.on_output("".join(caracteres))
                if m >= DADDR_SIZE:
                    return DMEM_ERR
            return OKAY

        # RA
        if op == "LDA":
            reg[r] = float(m)
        elif op == "LDC":
            reg[r] = ins.a2
        elif op == "JLT":
            if reg[r] < 0:
                reg[PC_REG] = float(m)
        elif op == "JLE":
            if reg[r] <= 0:
                reg[PC_REG] = float(m)
        elif op == "JGT":
            if reg[r] > 0:
                reg[PC_REG] = float(m)
        elif op == "JGE":
            if reg[r] >= 0:
                reg[PC_REG] = float(m)
        elif op == "JEQ":
            if reg[r] == 0:
                reg[PC_REG] = float(m)
        elif op == "JNE":
            if reg[r] != 0:
                reg[PC_REG] = float(m)
        return OKAY

    def run(self, max_steps: Optional[int] = None) -> str:
        """Ejecuta hasta que el resultado deje de ser OK (comando g)."""
        ejecutados = 0
        while True:
            if max_steps is not None and ejecutados >= max_steps:
                return STEP_LIMIT
            resultado = self.step()
            ejecutados += 1
            if resultado != OKAY:
                return resultado


def _pow(base: float, exponente: float) -> float:
    """pow de C: devuelve inf/nan en lugar de lanzar excepciones."""
    try:
        return math.pow(base, exponente)
    except OverflowError:
        return math.inf
    except ValueError:
        if base == 0 and exponente < 0:
            return math.inf
        return math.nan


# ----------------------------------------------------------------------
# Línea de comandos (mismo ciclo de comandos que tm.c)
# ----------------------------------------------------------------------

def _consola_input(real: bool) -> Optional[float]:
    while True:
        prompt = ("Enter real value for INF instruction: " if real
                  else "Enter value for IN instruction: ")
        try:
            texto = input(prompt)
        except EOFError:
            return None
        valor = parse_input(texto, real)
        if valor is not None:
            return valor
        print("Illegal value")


def _consola_output(texto: str) -> None:
    sys.stdout.write(texto)
    sys.stdout.flush()


def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} <filename>")
        return 1
    nombre = argv[1]
    if "." not in nombre.replace("\\", "/").rsplit("/", 1)[-1]:
        nombre += ".tm"
    try:
        with open(nombre, encoding="utf-8") as archivo:
            texto = archivo.read()
    except OSError:
        print(f"file '{nombre}' not found")
        return 1

    tm = TMSimulator(on_input=_consola_input, on_output=_consola_output)
    try:
        tm.load(texto)
    except TMLoadError as exc:
        print(exc)
        return 1

    print("TM  simulation (enter h for help)...")
    trace = False
    icount = False
    iloc = dloc = 0
    while True:
        try:
            linea = input("Enter command: ").split()
        except EOFError:
            break
        if not linea:
            continue
        cmd, args = linea[0][0], linea[1:]
        if cmd == "q":
            break
        if cmd == "h":
            print("Commands are:\n"
                  "   s(tep <n>      Execute n (default 1) TM instructions\n"
                  "   g(o            Execute TM instructions until HALT\n"
                  "   r(egs          Print the contents of the registers\n"
                  "   i(Mem <b <n>>  Print n iMem locations starting at b\n"
                  "   d(Mem <b <n>>  Print n dMem locations starting at b\n"
                  "   t(race         Toggle instruction trace\n"
                  "   p(rint         Toggle print of total instructions executed ('go' only)\n"
                  "   c(lear         Reset simulator for new execution of program\n"
                  "   h(elp          Cause this list of commands to be printed\n"
                  "   q(uit          Terminate the simulation")
        elif cmd == "t":
            trace = not trace
            print(f"Tracing now {'on' if trace else 'off'}.")
        elif cmd == "p":
            icount = not icount
            print(f"Printing instruction count now {'on' if icount else 'off'}.")
        elif cmd == "r":
            for i, valor in enumerate(tm.reg):
                fin = "\n" if i % 4 == 3 else ""
                print(f"{i}: {format_value(valor):>4}    ", end=fin)
        elif cmd in ("i", "d"):
            try:
                numeros = [int(a) for a in args]
            except ValueError:
                print("Instruction locations?" if cmd == "i" else "Data locations?")
                continue
            if cmd == "i":
                iloc = numeros[0] if numeros else iloc
                for loc in range(iloc, min(iloc + (numeros[1] if len(numeros) > 1 else 1), IADDR_SIZE)):
                    print(f"{loc:5d}: {tm.i_mem[loc]}")
            else:
                dloc = numeros[0] if numeros else dloc
                for loc in range(dloc, min(dloc + (numeros[1] if len(numeros) > 1 else 1), DADDR_SIZE)):
                    print(f"{loc:5d}: {format_value(tm.d_mem[loc]):>5}")
        elif cmd == "c":
            tm.reset()
        elif cmd in ("g", "s"):
            pasos = None if cmd == "g" else (abs(int(args[0])) if args else 1)
            resultado = OKAY
            contador = 0
            while resultado == OKAY and (pasos is None or contador < pasos):
                if trace:
                    pc = int(tm.reg[PC_REG])
                    if 0 <= pc < IADDR_SIZE:
                        print(f"{pc:5d}: {tm.i_mem[pc]}")
                resultado = tm.step()
                contador += 1
            if resultado == HALT:
                print("HALT: 0,0,0")
            if cmd == "g" and icount:
                print(f"Number of instructions executed = {contador}")
            print(resultado)
        else:
            print(f"Command {cmd} unknown.")
    print("Simulation done.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

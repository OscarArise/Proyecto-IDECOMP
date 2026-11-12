"""
probar_ejercicios.py
--------------------
Compila con el compilador CAOS todos los ejercicios finales de codigo_caos/
(12 grupos x 5 ejercicios) y verifica cada fase hasta la ejecución:

    1. Léxico       tokens.txt con tokens y sin errores
    2. Sintáctico   syntax.txt con el AST y "Sin errores sintácticos."
    3. Semántico    semantic.txt con "Sin errores semánticos." y tabla de símbolos
    4. Generación   code.tm que la TM carga (termina en HALT) y code.ci de tres direcciones
    5. Ejecución    el code.tm se ejecuta con los casos de casos.py en tm/tm.py y,
                    si hay gcc, en tm/tm.exe; la salida debe ser exactamente la esperada

Las salidas de cada programa quedan como evidencia en codigo_caos/salidas/.

Uso:
    python codigo_caos/probar_ejercicios.py            # todos los grupos
    python codigo_caos/probar_ejercicios.py 3 7        # solo los grupos 3 y 7
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
STUB = RAIZ / "external_compiler" / "compiler_stub.py"
TM_C = RAIZ / "tm" / "tm.c"
SALIDAS = AQUI / "salidas"

for ruta in (str(RAIZ), str(AQUI)):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

from casos import CASOS  # noqa: E402
from tm.tm import HALT, OKAY, TMLoadError, TMSimulator, parse_input  # noqa: E402

FASES = ("lexico", "sintactico", "semantico", "generacion", "ejecucion")
MAX_PASOS = 5_000_000


@dataclass
class ResultadoCaso:
    entradas: list
    esperado: str
    obtenido_py: str
    estado_py: str
    obtenido_c: Optional[str] = None

    @property
    def correcto(self) -> bool:
        ok_py = self.estado_py == HALT and self.obtenido_py == self.esperado
        ok_c = self.obtenido_c is None or self.obtenido_c == self.esperado
        return ok_py and ok_c


@dataclass
class ResultadoPrograma:
    archivo: Path
    codigo_salida: int = -1
    fases: dict = field(default_factory=dict)   # fase -> (ok, detalle)
    casos: List[ResultadoCaso] = field(default_factory=list)
    instrucciones: int = 0

    @property
    def nombre(self) -> str:
        return f"{self.archivo.parent.name}/{self.archivo.name}"

    @property
    def correcto(self) -> bool:
        return all(ok for ok, _ in self.fases.values()) and len(self.fases) == len(FASES)


def programas(grupos: Optional[List[int]] = None) -> List[Path]:
    archivos = sorted(AQUI.glob("grupo_*/ej*.caos"))
    if grupos:
        archivos = [a for a in archivos if int(a.parent.name.split("_")[1]) in grupos]
    return archivos


# ----------------------------------------------------------------------
# Simuladores
# ----------------------------------------------------------------------

def ejecutar_py(tm_code: str, entradas: list) -> Tuple[str, str]:
    """Ejecuta en tm.py. Cada entrada se valida como en el IDE (IN entero, INF real)."""
    pendientes = [str(e) for e in entradas]
    salida: List[str] = []

    def leer(real: bool):
        if not pendientes:
            return None
        valor = parse_input(pendientes.pop(0), real)
        if valor is None:
            raise ValueError(f"entrada no válida para {'INF' if real else 'IN'}")
        return valor

    tm = TMSimulator(on_input=leer, on_output=salida.append)
    tm.load(tm_code)
    estado = tm.run(max_steps=MAX_PASOS)
    if pendientes and estado == HALT:
        estado = f"{HALT} (sobraron {len(pendientes)} entradas)"
    return "".join(salida), estado


_TM_EXE: Optional[Path] = None
_TM_EXE_BUSCADO = False


def tm_exe() -> Optional[Path]:
    """Compila tm/tm.c una vez en un directorio temporal (None si no hay gcc)."""
    global _TM_EXE, _TM_EXE_BUSCADO
    if not _TM_EXE_BUSCADO:
        _TM_EXE_BUSCADO = True
        gcc = shutil.which("gcc")
        if gcc:
            destino = Path(tempfile.gettempdir()) / "tm_codigo_caos.exe"
            r = subprocess.run([gcc, "-std=c11", "-O2", str(TM_C), "-o", str(destino), "-lm"],
                               capture_output=True, text=True)
            if r.returncode == 0:
                _TM_EXE = destino
    return _TM_EXE


_PROMPTS = ("TM  simulation (enter h for help)...\n", "Enter command: ",
            "Enter value for IN instruction: ", "Enter real value for INF instruction: ",
            "Simulation done.\n")


def ejecutar_c(tm_file: Path, entradas: list) -> str:
    """Ejecuta en tm.exe con el comando g; devuelve solo la salida del programa."""
    stdin = "g\n" + "".join(f"{e}\n" for e in entradas) + "q\n"
    r = subprocess.run([str(tm_exe()), str(tm_file)], input=stdin.encode("utf-8"),
                       capture_output=True, timeout=60)
    texto = r.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n")
    for prompt in _PROMPTS:
        texto = texto.replace(prompt, "")
    return texto.replace("HALT: 0,0,0\nHalted\n", "")


# ----------------------------------------------------------------------
# Compilación y verificación por fase
# ----------------------------------------------------------------------

def _leer(directorio: Path, nombre: str) -> str:
    ruta = directorio / nombre
    return ruta.read_text(encoding="utf-8") if ruta.exists() else ""


def probar_programa(archivo: Path, con_tm_exe: bool = True) -> ResultadoPrograma:
    resultado = ResultadoPrograma(archivo)
    destino = SALIDAS / archivo.parent.name / archivo.stem
    destino.mkdir(parents=True, exist_ok=True)

    # Compilación completa (todas las fases), como F9 en el IDE
    r = subprocess.run([sys.executable, str(STUB), str(archivo)], cwd=destino,
                       capture_output=True, text=True, encoding="utf-8")
    resultado.codigo_salida = r.returncode
    errores = _leer(destino, "errors.txt").strip() or r.stderr.strip()
    f = resultado.fases

    tokens = _leer(destino, "tokens.txt")
    filas = [l for l in tokens.splitlines()[2:] if l.strip()]
    f["lexico"] = (bool(filas) and not errores.startswith("[LEXICO]"),
                   f"{len(filas)} tokens" if filas else (errores or "sin tokens"))
    if r.returncode == 1:
        return resultado

    sintaxis = _leer(destino, "syntax.txt")
    f["sintactico"] = ("Sin errores sintácticos." in sintaxis and r.returncode != 2,
                       "AST construido" if r.returncode != 2 else errores)
    if r.returncode == 2:
        return resultado

    semantico = _leer(destino, "semantic.txt")
    simbolos = _leer(destino, "symbols.txt")
    ids = [l for l in simbolos.splitlines() if l.startswith("Total de identificadores")]
    f["semantico"] = ("Sin errores semánticos." in semantico and r.returncode != 3,
                      ids[0] if ids and r.returncode != 3 else errores)
    if r.returncode == 3:
        return resultado

    tm_code = _leer(destino, "code.tm")
    ci_code = _leer(destino, "code.ci")
    instrucciones = [l for l in tm_code.splitlines() if l.strip() and not l.lstrip().startswith("*")]
    resultado.instrucciones = len(instrucciones)
    detalle_gen = f"{len(instrucciones)} instrucciones TM"
    try:
        TMSimulator().load(tm_code)
        carga_ok = True
    except TMLoadError as exc:
        carga_ok, detalle_gen = False, f"la TM no pudo cargar code.tm: {exc}"
    gen_ok = (r.returncode == 0 and carga_ok and "HALT" in tm_code
              and archivo.name in tm_code and ci_code.rstrip().endswith("halt;"))
    f["generacion"] = (gen_ok, detalle_gen if r.returncode == 0 else errores)
    if not gen_ok:
        return resultado

    # Ejecución de cada caso en las dos TM
    casos = CASOS.get(archivo.name)
    if not casos:
        f["ejecucion"] = (False, "no hay casos definidos en casos.py")
        return resultado
    usar_c = con_tm_exe and tm_exe() is not None
    reporte = []
    for entradas, esperado in casos:
        try:
            obtenido, estado = ejecutar_py(tm_code, entradas)
        except ValueError as exc:
            obtenido, estado = "", str(exc)
        caso = ResultadoCaso(entradas, esperado, obtenido, estado)
        if usar_c:
            caso.obtenido_c = ejecutar_c(destino / "code.tm", entradas)
        resultado.casos.append(caso)
        reporte.append(
            f"Entradas: {' '.join(str(e) for e in entradas) or '(ninguna)'}\n"
            f"Estado TM: {estado}\n"
            f"Salida:\n{obtenido}"
            f"Resultado: {'CORRECTO' if caso.correcto else 'INCORRECTO'}\n"
            + ("" if caso.correcto else f"Esperado:\n{esperado}"
               + (f"tm.exe:\n{caso.obtenido_c}" if caso.obtenido_c is not None else ""))
        )
    (destino / "ejecucion.txt").write_text("\n".join(reporte), encoding="utf-8")
    correctos = sum(c.correcto for c in resultado.casos)
    simuladores = "tm.py y tm.exe" if usar_c else "tm.py"
    f["ejecucion"] = (correctos == len(casos),
                      f"{correctos}/{len(casos)} casos correctos ({simuladores})")
    return resultado


def probar_todos(grupos: Optional[List[int]] = None, con_tm_exe: bool = True) -> List[ResultadoPrograma]:
    if con_tm_exe:
        tm_exe()  # compilar una sola vez antes de lanzar los hilos
    with ThreadPoolExecutor(max_workers=6) as pool:
        return list(pool.map(lambda a: probar_programa(a, con_tm_exe), programas(grupos)))


def resumen(resultados: List[ResultadoPrograma]) -> str:
    lineas = []
    ancho = max((len(r.nombre) for r in resultados), default=10)
    encabezado = f"{'Programa':<{ancho}}  " + "  ".join(f"{fase[:10]:<10}" for fase in FASES)
    lineas.append(encabezado)
    lineas.append("-" * len(encabezado))
    for r in resultados:
        marcas = []
        for fase in FASES:
            if fase not in r.fases:
                marcas.append(f"{'-':<10}")
            else:
                marcas.append(f"{'OK' if r.fases[fase][0] else 'FALLA':<10}")
        lineas.append(f"{r.nombre:<{ancho}}  " + "  ".join(marcas))
    fallas = [r for r in resultados if not r.correcto]
    lineas.append("")
    lineas.append(f"Programas: {len(resultados)}   correctos: {len(resultados) - len(fallas)}"
                  f"   con fallas: {len(fallas)}")
    casos = sum(len(r.casos) for r in resultados)
    lineas.append(f"Casos ejecutados: {casos}   correctos: "
                  f"{sum(c.correcto for r in resultados for c in r.casos)}")
    for r in fallas:
        lineas.append(f"\n{r.nombre} (código de salida {r.codigo_salida})")
        for fase in FASES:
            if fase in r.fases and not r.fases[fase][0]:
                lineas.append(f"  {fase}: {r.fases[fase][1]}")
    return "\n".join(lineas) + "\n"


def main(argv: List[str]) -> int:
    grupos = [int(a) for a in argv[1:]] or None
    resultados = probar_todos(grupos)
    texto = resumen(resultados)
    SALIDAS.mkdir(exist_ok=True)
    if not grupos:
        (SALIDAS / "resumen.txt").write_text(texto, encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(texto)
    return 0 if all(r.correcto for r in resultados) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

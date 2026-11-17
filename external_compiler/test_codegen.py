"""
Pruebas de la Fase 4: generación de código intermedio (.ci), código TM (.tm)
y su ejecución en el simulador TM (tm/tm.py y, si hay gcc, tm/tm.exe).

    cd external_compiler
    python -m unittest test_codegen
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
STUB = AQUI / "compiler_stub.py"
PRUEBAS = RAIZ / "pruebas"
CODEGEN = PRUEBAS / "codegen"
TM_DIR = RAIZ / "tm"

for ruta in (str(AQUI), str(RAIZ)):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

from codegen.code import Emisor  # noqa: E402
from tm.tm import HALT, ZERODIVIDE, TMSimulator  # noqa: E402


def compilar(fuente: Path, fase: str = "intermedio"):
    """Compila en un directorio temporal; devuelve (código, archivos de salida)."""
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(
            [sys.executable, str(STUB), str(fuente), "--phase", fase],
            cwd=tmp, capture_output=True, text=True, encoding="utf-8",
        )
        archivos = {p.name: p.read_text(encoding="utf-8") for p in Path(tmp).iterdir()}
        return r.returncode, archivos, r.stderr


def ejecutar_py(tm_code: str, entradas):
    """Ejecuta el .tm en tm.py con entradas fijas; devuelve (salida, resultado)."""
    pendientes = list(entradas)
    salida = []
    tm = TMSimulator(
        on_input=lambda real: float(pendientes.pop(0)) if pendientes else None,
        on_output=salida.append,
    )
    tm.load(tm_code)
    resultado = tm.run(max_steps=2_000_000)
    return "".join(salida), resultado


_TM_EXE = None


def tm_exe():
    """Compila tm/tm.c una sola vez (None si no hay gcc)."""
    global _TM_EXE
    if _TM_EXE is None:
        gcc = shutil.which("gcc")
        if not gcc:
            _TM_EXE = False
        else:
            destino = Path(tempfile.gettempdir()) / "tm_caos_test.exe"
            r = subprocess.run([gcc, "-std=c11", "-O2", str(TM_DIR / "tm.c"), "-o", str(destino), "-lm"],
                               capture_output=True, text=True)
            _TM_EXE = destino if r.returncode == 0 else False
    return _TM_EXE or None


def ejecutar_c(tm_code: str, entradas):
    """Ejecuta el .tm en tm.exe (comando g) y devuelve solo la salida del programa."""
    with tempfile.TemporaryDirectory() as tmp:
        archivo = Path(tmp) / "code.tm"
        archivo.write_text(tm_code, encoding="utf-8")
        stdin = "g\n" + "".join(f"{e}\n" for e in entradas) + "q\n"
        r = subprocess.run([str(tm_exe()), str(archivo)], input=stdin.encode("utf-8"),
                           capture_output=True, timeout=30)
    texto = r.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n")
    for prompt in ("TM  simulation (enter h for help)...\n", "Enter command: ",
                   "Enter value for IN instruction: ", "Enter real value for INF instruction: ",
                   "Simulation done.\n"):
        texto = texto.replace(prompt, "")
    return texto


# (programa, entradas, salida esperada, resultado de la TM)
CASOS = [
    ("00_factorial.caos", [5], "120\n", HALT),
    ("00_factorial.caos", [0], "", HALT),
    ("01_secuencial_promedio.caos", [12345, 8, 9.5, 7, 10, 6.5],
     "Matricula: 12345\nPromedio: 8.2\n", HALT),
    ("02_selectivo_signo.caos", [7], "0\n", HALT),
    ("02_selectivo_signo.caos", [-3], "1\n", HALT),
    ("02_selectivo_signo.caos", [0], "2\n", HALT),
    ("03_selectivo_descuento.caos", [300], "Total a pagar: 300.0\n", HALT),
    ("03_selectivo_descuento.caos", [800], "Total a pagar: 760.0\n", HALT),
    ("03_selectivo_descuento.caos", [5000], "Total a pagar: 4450.0\n", HALT),
    ("03_selectivo_descuento.caos", [20000], "Total a pagar: 15000.0\n", HALT),
    ("04_repetitivo_fibonacci.caos", [10], "Termino 10 = 34\n", HALT),
    ("04_repetitivo_fibonacci.caos", [1], "Termino 1 = 0\n", HALT),
    ("05_repetitivo_votos.caos", [1, 3, 1, 4, 2, 2, 1, 4, 1, 1, 1, 2, 1, 3, 1, 4, 0],
     "Candidato 1: 8 votos, 50.0%\nCandidato 2: 3 votos, 18.75%\n"
     "Candidato 3: 2 votos, 12.5%\nCandidato 4: 3 votos, 18.75%\n", HALT),
    ("05_repetitivo_votos.caos", [0], "Sin votos\n", HALT),
    ("06_operadores.caos", [],
     "2\n1024\n3\n8.5\n1.414214\n1 0\n16 6\ncomparaciones correctas\n", HALT),
    ("07_repetitivo_ulam.caos", [6], "6\n3\n10\n5\n16\n8\n4\n2\n1\n", HALT),
    ("08_division_cero.caos", [10, 0], "", ZERODIVIDE),
]


class TestEjecucionTM(unittest.TestCase):
    """Cada programa se compila a .tm y se ejecuta con datos conocidos."""

    @classmethod
    def setUpClass(cls):
        cls.codigos = {}
        for nombre in {caso[0] for caso in CASOS}:
            codigo, archivos, err = compilar(CODEGEN / nombre)
            cls.codigos[nombre] = (codigo, archivos.get("code.tm", ""), err)

    def test_compilan_sin_errores(self):
        for nombre, (codigo, tm_code, err) in self.codigos.items():
            with self.subTest(programa=nombre):
                self.assertEqual(codigo, 0, err)
                self.assertIn("HALT", tm_code)

    def test_resultados_en_tm_py(self):
        for nombre, entradas, esperado, resultado in CASOS:
            with self.subTest(programa=nombre, entradas=entradas):
                salida, obtenido = ejecutar_py(self.codigos[nombre][1], entradas)
                self.assertEqual(obtenido, resultado)
                self.assertEqual(salida, esperado)

    def test_tm_exe_coincide_con_tm_py(self):
        if not tm_exe():
            self.skipTest("gcc no disponible para compilar tm/tm.c")
        finales = {HALT: "HALT: 0,0,0\nHalted\n", ZERODIVIDE: "Division by 0\n"}
        for nombre, entradas, esperado, resultado in CASOS:
            with self.subTest(programa=nombre, entradas=entradas):
                salida = ejecutar_c(self.codigos[nombre][1], entradas)
                self.assertEqual(salida, esperado + finales[resultado])


class TestCodigoGenerado(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        codigo, archivos, err = compilar(CODEGEN / "00_factorial.caos")
        assert codigo == 0, err
        cls.tm = archivos["code.tm"]
        cls.ci = archivos["code.ci"]
        cls.archivos = archivos

    def test_fact_por_x_igual_que_tiny(self):
        """fact = fact * x produce la misma secuencia que el ejemplo de Louden (16-21)."""
        instrucciones = [l.split("\t")[0].split(":", 1)[1].split()
                         for l in self.tm.splitlines() if l.strip() and not l.lstrip().startswith("*")]
        secuencia = [["LD", "0,1(5)"], ["ST", "0,0(6)"], ["LD", "0,0(5)"],
                     ["LD", "1,0(6)"], ["MUL", "0,1,0"], ["ST", "0,1(5)"]]
        posiciones = [i for i in range(len(instrucciones))
                      if instrucciones[i:i + len(secuencia)] == secuencia]
        self.assertTrue(posiciones, self.tm)

    def test_backpatch_del_if(self):
        """El salto reservado del if aparece después en el archivo, como en factorial.tm."""
        self.assertIn("if: jmp to else", self.tm)
        lineas = [l for l in self.tm.splitlines() if "if: jmp to else" in l]
        direccion = int(lineas[0].split(":")[0])
        anteriores = [int(l.split(":")[0]) for l in self.tm.splitlines()
                      if l.strip() and not l.lstrip().startswith("*")]
        self.assertGreater(max(anteriores[:anteriores.index(direccion)]), direccion)

    def test_tres_direcciones(self):
        self.assertIn("t2 = fact * x;", self.ci)
        self.assertIn("fact = t2;", self.ci)
        self.assertIn("if_false t1 goto L1;", self.ci)
        self.assertIn("read x;", self.ci)
        self.assertIn("halt;", self.ci)

    def test_intermediate_txt_es_el_listado_tm(self):
        self.assertEqual(self.archivos["intermediate.txt"], self.tm)


class TestSinCodigoConErrores(unittest.TestCase):
    """Con errores de análisis no se genera .tm ni .ci."""

    def test_error_semantico_no_genera(self):
        codigo, archivos, _ = compilar(PRUEBAS / "TestSemantica.txt")
        self.assertEqual(codigo, 3)
        self.assertEqual(archivos.get("code.tm", ""), "")
        self.assertEqual(archivos.get("code.ci", ""), "")

    def test_error_sintactico_no_genera(self):
        codigo, archivos, _ = compilar(PRUEBAS / "codigo_errores.caos")
        self.assertEqual(codigo, 2)
        self.assertEqual(archivos.get("code.tm", ""), "")


class TestEmisor(unittest.TestCase):

    def test_emit_rm_abs_relativo_a_pc(self):
        e = Emisor()
        e.emit_skip(5)
        e.emit_rm_abs("JEQ", 0, 20, "")
        self.assertEqual(e.lineas[-1].split()[1:], ["JEQ", "0,14(7)"])

    def test_backup_restore(self):
        e = Emisor(trace_code=False)
        reservado = e.emit_skip(1)
        e.emit_ro("HALT", 0, 0, 0)
        e.emit_backup(reservado)
        e.emit_rm_abs("LDA", 7, 2)
        e.emit_restore()
        self.assertEqual(e.emit_loc, 2)
        self.assertTrue(e.lineas[-1].startswith("  0:"))


if __name__ == "__main__":
    unittest.main()

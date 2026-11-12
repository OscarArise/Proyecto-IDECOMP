"""
Pruebas de integración del compilador completo (subproceso, como lo usa el IDE).

    cd external_compiler
    python -m unittest test_integracion
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
STUB = AQUI / "compiler_stub.py"
PRUEBAS = RAIZ / "pruebas"
SAMPLES = RAIZ / "ide" / "samples"


def compilar(fuente: Path, fase: str | None = None):
    """Ejecuta el compilador en un directorio temporal; devuelve (código, archivos)."""
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [sys.executable, str(STUB), str(fuente)]
        if fase:
            cmd += ["--phase", fase]
        r = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, encoding="utf-8")
        archivos = {
            p.name: p.read_text(encoding="utf-8") for p in Path(tmp).glob("*.txt")
        }
        return r.returncode, archivos, r.stderr


class TestSemanticaIntegrada(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.codigo, cls.archivos, cls.stderr = compilar(PRUEBAS / "TestSemantica.txt")

    def test_codigo_de_salida_3(self):
        self.assertEqual(self.codigo, 3, self.stderr)

    def test_seis_errores_semanticos(self):
        lineas = self.archivos["errors.txt"].splitlines()
        self.assertEqual(len(lineas), 6)
        esperados = [
            ("[4:5]", "E1"), ("[5:5]", "E4"), ("[14:5]", "E4"),
            ("[16:9]", "E4"), ("[33:13]", "E1"), ("[37:13]", "E1"),
        ]
        for linea, (pos, codigo) in zip(lineas, esperados):
            self.assertTrue(linea.startswith("[SEMANTICO] " + pos), linea)
            self.assertIn(f"Error semántico {codigo}:", linea)

    def test_tabla_de_simbolos(self):
        tabla = self.archivos["symbols.txt"]
        for nombre, tipo, loc in [("x", "int", 0), ("y", "int", 1), ("z", "int", 2),
                                  ("a", "float", 3), ("b", "float", 4), ("c", "float", 5)]:
            fila = [l.split() for l in tabla.splitlines() if l.startswith(nombre + " ")]
            self.assertTrue(fila, nombre)
            self.assertEqual(fila[0][1:3], [tipo, str(loc)])

    def test_semantic_txt_trae_arbol_anotado(self):
        sem = self.archivos["semantic.txt"]
        self.assertIn("Árbol con anotaciones semánticas", sem)
        self.assertIn("Recorrido semántico", sem)
        self.assertIn("Representación estructurada", sem)
        self.assertIn("ConversionTipo", sem)

    def test_syntax_txt_sigue_siendo_el_original(self):
        sin = self.archivos["syntax.txt"]
        self.assertIn("Representación estructurada", sin)
        self.assertNotIn("⟨", sin)  # sin anotaciones semánticas

    def test_hasta_la_fase_sintactica_no_corre_el_semantico(self):
        codigo, archivos, _ = compilar(PRUEBAS / "TestSemantica.txt", "sintactico")
        self.assertEqual(codigo, 0)
        self.assertEqual(archivos["semantic.txt"], "")
        self.assertEqual(archivos["errors.txt"], "")


class TestSinRegresiones(unittest.TestCase):
    """
    Los códigos de salida de las fases 1 y 2 no cambian con el semántico.
    Los programas léxica y sintácticamente correctos que usan variables sin
    declarar o mezclan tipos pasan a salir con 3 (error semántico).
    """

    ESPERADOS = {
        PRUEBAS / "codigo_valido.caos": 0,
        PRUEBAS / "codigo_complejo.caos": 0,
        PRUEBAS / "lexico_sintacticamente_correcto.txt": 3,
        PRUEBAS / "corecccc.caos": 3,
        PRUEBAS / "testLexico.txt": 1,
        PRUEBAS / "conerrores.caos": 2,
        PRUEBAS / "codigo_errores.caos": 2,
        SAMPLES / "test_basico.caos": 0,
        SAMPLES / "test_ciclo.caos": 0,
        SAMPLES / "test_condicional.caos": 0,
        SAMPLES / "test_errores.caos": 2,
    }

    def test_codigos_de_salida(self):
        for fuente, esperado in self.ESPERADOS.items():
            with self.subTest(archivo=fuente.name):
                codigo, _, err = compilar(fuente)
                self.assertEqual(codigo, esperado, err)

    def test_programa_valido_sin_errores(self):
        codigo, archivos, _ = compilar(PRUEBAS / "codigo_valido.caos")
        self.assertEqual(codigo, 0)
        self.assertEqual(archivos["errors.txt"], "")
        self.assertIn("Total de identificadores", archivos["symbols.txt"])


if __name__ == "__main__":
    unittest.main()

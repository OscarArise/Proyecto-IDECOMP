"""
Prueba completa del compilador CAOS con los ejercicios finales.

Cada programa de codigo_caos/grupo_XX/ debe pasar el léxico, el sintáctico y el
semántico, generar code.tm y code.ci, y su code.tm debe producir en la TM la
salida esperada de casos.py (en tm.py y, si hay gcc, también en tm.exe).

    python -m unittest codigo_caos.test_ejercicios        (desde la raíz)
    python codigo_caos/test_ejercicios.py
"""

import sys
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
if str(AQUI) not in sys.path:
    sys.path.insert(0, str(AQUI))

from casos import CASOS  # noqa: E402
from probar_ejercicios import FASES, programas, probar_todos  # noqa: E402


class TestEstructura(unittest.TestCase):

    def test_doce_grupos_con_cinco_ejercicios(self):
        grupos = sorted(p.name for p in AQUI.glob("grupo_*") if p.is_dir())
        self.assertEqual(grupos, [f"grupo_{i:02d}" for i in range(1, 13)])
        for grupo in grupos:
            with self.subTest(grupo=grupo):
                nombres = sorted(p.name[:3] for p in (AQUI / grupo).glob("ej*.caos"))
                self.assertEqual(nombres, ["ej1", "ej2", "ej3", "ej4", "ej5"])

    def test_cada_programa_tiene_casos(self):
        for archivo in programas():
            with self.subTest(programa=archivo.name):
                self.assertIn(archivo.name, CASOS)


class TestCompiladorCompleto(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.resultados = probar_todos()

    def test_todas_las_fases(self):
        for resultado in self.resultados:
            for fase in FASES:
                with self.subTest(programa=resultado.nombre, fase=fase):
                    self.assertIn(fase, resultado.fases,
                                  f"la compilación se detuvo antes (código {resultado.codigo_salida})")
                    ok, detalle = resultado.fases[fase]
                    self.assertTrue(ok, detalle)

    def test_salidas_de_ejecucion(self):
        for resultado in self.resultados:
            for caso in resultado.casos:
                with self.subTest(programa=resultado.nombre, entradas=caso.entradas):
                    self.assertEqual(caso.estado_py, "Halted")
                    self.assertEqual(caso.obtenido_py, caso.esperado)
                    if caso.obtenido_c is not None:
                        self.assertEqual(caso.obtenido_c, caso.esperado)


if __name__ == "__main__":
    unittest.main()

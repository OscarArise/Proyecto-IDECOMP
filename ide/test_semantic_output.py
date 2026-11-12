"""
Pruebas de core/semantic_output.py (no necesitan Tkinter).

    cd ide
    python -m unittest test_semantic_output
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from core.semantic_output import (
    error_text_for_editor,
    extract_ast_dict,
    split_semantic_output,
)

RAIZ = Path(__file__).resolve().parent.parent
STUB = RAIZ / "external_compiler" / "compiler_stub.py"
FUENTE = RAIZ / "pruebas" / "TestSemantica.txt"


def salida_real():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, str(STUB), str(FUENTE)], cwd=tmp,
                       capture_output=True)
        leer = lambda n: (Path(tmp) / n).read_text(encoding="utf-8")
        return leer("syntax.txt"), leer("semantic.txt")


class TestSemanticOutput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sintactico, cls.semantico = salida_real()

    def test_extrae_el_ast_original(self):
        ast = extract_ast_dict(self.sintactico)
        self.assertEqual(ast["label"], "PROGRAMA")
        self.assertNotIn("⟨", json.dumps(ast, ensure_ascii=False))

    def test_separa_texto_y_arbol_anotado(self):
        texto, anotado = split_semantic_output(self.semantico)
        self.assertIn("Recorrido semántico", texto)
        self.assertIn("Errores semánticos", texto)
        self.assertNotIn('"children"', texto)  # sin el JSON
        self.assertLess(len(texto.splitlines()), 400)
        self.assertIn("⟨", json.dumps(anotado, ensure_ascii=False))

    def test_anotado_conserva_la_estructura_del_original(self):
        original = extract_ast_dict(self.sintactico)
        _, anotado = split_semantic_output(self.semantico)
        self.assertEqual(original["type"], anotado["type"])
        self.assertEqual(len(original["children"]), len(anotado["children"]))

    def test_entradas_vacias_o_invalidas(self):
        self.assertIsNone(extract_ast_dict(""))
        self.assertIsNone(extract_ast_dict("sin json"))
        self.assertEqual(split_semantic_output(""), ("", None))

    def test_errores_para_el_editor(self):
        texto = error_text_for_editor({
            "err_lexico": "[LEXICO] a",
            "err_sintactico": "",
            "err_semantico": "[SEMANTICO] [4:5] b",
            "ejecucion": "no",
        })
        self.assertEqual(texto, "[LEXICO] a\n[SEMANTICO] [4:5] b")


if __name__ == "__main__":
    unittest.main()

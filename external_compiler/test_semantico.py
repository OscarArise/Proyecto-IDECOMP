"""
Pruebas del análisis semántico (Fase 3, bloque 2).

    cd external_compiler
    python -m unittest test_semantico
"""

import json
import os
import sys
import unittest

COMPILER_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(COMPILER_DIR)
if COMPILER_DIR not in sys.path:
    sys.path.insert(0, COMPILER_DIR)

from lexer.dfa_lexer import DFALexer
from parser.ast_formatter import ASTFormatter
from parser.parser import Parser
from semantic import TablaSimbolos, analizar, funcion_hash
from semantic.analizador import _dividir_entero, _modulo_entero
from semantic.formateador import errores_txt, semantic_txt, symbols_txt

TEST_OFICIAL = os.path.join(PROJECT_DIR, "pruebas", "TestSemantica.txt")


def analizar_fuente(fuente):
    tokens_crudos, errores_lexicos = DFALexer().tokenize(fuente)
    tokens = [
        (t.tipo, t.valor, t.linea, t.columna)
        for t in tokens_crudos
        if t.tipo not in ("ERROR", "EOF")
    ]
    ast, errores_sintacticos = Parser(tokens).parse()
    assert not errores_lexicos, errores_lexicos
    assert not errores_sintacticos, [str(e) for e in errores_sintacticos]
    return analizar(ASTFormatter.to_binary(ast))


def programa(cuerpo):
    return "main {\n" + cuerpo + "\n}\n"


def codigos(resultado):
    return [e.codigo for e in resultado.errores]


def recorrer(nodo):
    if not nodo:
        return
    yield nodo
    for hijo in nodo.get("children", []):
        yield from recorrer(hijo)


class TablaSimbolosTests(unittest.TestCase):

    def test_insertar_y_buscar(self):
        tabla = TablaSimbolos()
        x = tabla.insertar("x", "int", 2, 9)
        a = tabla.insertar("a", "float", 3, 11)
        self.assertEqual((0, 1), (x.loc, a.loc))
        self.assertIs(x, tabla.buscar("x"))
        self.assertEqual("float", tabla.buscar("a").tipo)
        self.assertIsNone(tabla.buscar("noexiste"))

    def test_colisiones_se_resuelven_por_encadenamiento(self):
        # Busca dos nombres distintos con la misma posición hash
        vistos = {}
        par = None
        for i in range(5000):
            nombre = f"v{i}"
            h = funcion_hash(nombre)
            if h in vistos:
                par = (vistos[h], nombre)
                break
            vistos[h] = nombre
        self.assertIsNotNone(par)
        tabla = TablaSimbolos()
        tabla.insertar(par[0], "int", 1)
        tabla.insertar(par[1], "bool", 2)
        self.assertEqual("int", tabla.buscar(par[0]).tipo)
        self.assertEqual("bool", tabla.buscar(par[1]).tipo)
        self.assertEqual(2, len(tabla))

    def test_agregar_linea_sin_repetir(self):
        tabla = TablaSimbolos()
        tabla.insertar("x", "int", 2)
        tabla.agregar_linea("x", 5)
        tabla.agregar_linea("x", 5)
        tabla.agregar_linea("x", 7)
        self.assertEqual([2, 5, 7], tabla.buscar("x").lineas)
        self.assertFalse(tabla.agregar_linea("y", 3))

    def test_eliminar(self):
        tabla = TablaSimbolos()
        tabla.insertar("x", "int", 1)
        self.assertTrue(tabla.eliminar("x"))
        self.assertIsNone(tabla.buscar("x"))
        self.assertFalse(tabla.eliminar("x"))


class ArchivoOficialTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(TEST_OFICIAL, encoding="utf-8") as archivo:
            cls.resultado = analizar_fuente(archivo.read())

    def test_seis_errores_esperados(self):
        obtenidos = [(e.codigo, e.linea, e.columna) for e in self.resultado.errores]
        self.assertEqual([
            ("E1", 4, 5),
            ("E4", 5, 5),
            ("E4", 14, 5),
            ("E4", 16, 9),
            ("E1", 33, 13),
            ("E1", 37, 13),
        ], obtenidos)

    def test_tabla_de_simbolos(self):
        filas = [(s.nombre, s.tipo, s.loc, s.lineas) for s in self.resultado.tabla.simbolos()]
        self.assertEqual([
            ("x", "int", 0, [2, 5, 6, 11, 27, 30, 31, 32, 38]),
            ("y", "int", 1, [2, 7, 8, 9, 12, 14, 16, 23, 29, 35, 36]),
            ("z", "int", 2, [2, 8, 13]),
            ("a", "float", 3, [3, 10, 16, 25]),
            ("b", "float", 4, [3, 19, 21]),
            ("c", "float", 5, [3, 26]),
        ], filas)

    def test_no_declaradas_no_entran_a_la_tabla(self):
        self.assertNotIn("suma", self.resultado.tabla)
        self.assertNotIn("mas", self.resultado.tabla)

    def test_valores_con_division_entera(self):
        asignaciones = {
            n["linea"]: n for n in recorrer(self.resultado.arbol_anotado)
            if n["type"] == "Asignacion"
        }
        valor = lambda linea: asignaciones[linea]["children"][0].get("valor_calculado")
        self.assertEqual(4, valor(7))
        self.assertEqual(61.0, valor(10))
        self.assertEqual(8, valor(11))
        self.assertEqual(-2, valor(12))
        self.assertEqual(64, valor(13))
        self.assertEqual(6, valor(31))

    def test_conversiones_en_linea_10(self):
        conversiones = [
            n for n in recorrer(self.resultado.arbol_anotado)
            if n["type"] == "ConversionTipo" and n["linea"] == 10
        ]
        self.assertEqual(4, len(conversiones))
        for c in conversiones:
            self.assertEqual(("int", "float"), (c["de"], c["a"]))
            self.assertEqual("int", c["children"][0]["tipo_dato"])

    def test_arbol_original_no_se_modifica(self):
        for nodo in recorrer(self.resultado.arbol_original):
            self.assertNotIn("tipo_dato", nodo)
            self.assertNotEqual("ConversionTipo", nodo["type"])

    def test_dtype_heredado_en_declaraciones(self):
        declarados = [
            n for n in recorrer(self.resultado.arbol_anotado)
            if n["type"] == "IdentificadorDeclarado"
        ]
        self.assertEqual(
            [("x", "int"), ("y", "int"), ("z", "int"),
             ("a", "float"), ("b", "float"), ("c", "float")],
            [(n["nombre_declarado"], n["dtype"]) for n in declarados],
        )
        self.assertTrue(all(n["atributo_tipo"] == "heredado" for n in declarados))

    def test_condiciones_son_bool(self):
        condiciones = [
            n for n in recorrer(self.resultado.arbol_anotado)
            if n["type"] == "SeccionAST" and n.get("tipo_requerido") == "bool"
        ]
        self.assertEqual(5, len(condiciones))
        for c in condiciones:
            self.assertEqual("bool", c["children"][0]["tipo_dato"])


class ErroresSemanticosTests(unittest.TestCase):

    def test_e1_no_declarado_en_cada_uso(self):
        r = analizar_fuente(programa("int x;\nx = y + 1;\ncin y;\ny++;"))
        self.assertEqual(["E1", "E1", "E1"], codigos(r))

    def test_e1_uso_antes_de_la_declaracion(self):
        r = analizar_fuente(programa("x = 1;\nint x;\nx = 2;"))
        self.assertEqual([("E1", 2)], [(e.codigo, e.linea) for e in r.errores])

    def test_e2_declaracion_duplicada(self):
        r = analizar_fuente(programa("int x;\nfloat x;\nx = 1.5;"))
        self.assertEqual(["E2", "E4"], codigos(r))
        self.assertEqual("int", r.tabla.buscar("x").tipo)
        self.assertEqual((3, 7), (r.errores[0].linea, r.errores[0].columna))

    def test_e3_comparar_bool_con_numero(self):
        r = analizar_fuente(programa("bool f;\nf = true == 1;"))
        self.assertEqual(["E3"], codigos(r))

    def test_e4_float_a_int(self):
        r = analizar_fuente(programa("int x;\nfloat a;\nx = a * 2;"))
        self.assertEqual(["E4"], codigos(r))

    def test_e5_operadores_mal_aplicados(self):
        casos = {
            "int x;\nx = true + 1;": "E5",
            "int x;\nfloat a;\nx = a % 2;": "E5",
            "bool f;\nint x;\nf = !x;": "E5",
            "bool f;\nf = true && 1;": "E5",
            "bool f;\nf = true < false;": "E5",
            "bool f;\nf++;": "E5",
        }
        for cuerpo, esperado in casos.items():
            with self.subTest(cuerpo=cuerpo):
                self.assertEqual([esperado], codigos(analizar_fuente(programa(cuerpo))))

    def test_e6_bool_y_numero_en_asignacion(self):
        self.assertEqual(["E6"], codigos(analizar_fuente(programa("bool f;\nf = 1;"))))
        self.assertEqual(["E6"], codigos(analizar_fuente(programa("int x;\nx = true;"))))

    def test_e7_condiciones_no_booleanas(self):
        fuente = programa(
            "int x;\n"
            "if x then x = 1; end\n"
            "while x + 1 x = 2; end\n"
            "do x = 3; while x end until x"
        )
        r = analizar_fuente(fuente)
        self.assertEqual(["E7", "E7", "E7", "E7"], codigos(r))

    def test_sin_errores_en_cascada(self):
        # 'y' no declarada: solo E1, sin un E6/E4 extra en la asignación
        r = analizar_fuente(programa("int x;\nx = (y + 1.5) * 2;"))
        self.assertEqual(["E1"], codigos(r))

    def test_continua_despues_de_errores(self):
        r = analizar_fuente(programa(
            "int x;\nx = 1.5;\nbool f;\nf = 3;\nz = 1;\nif x then x = 1; end"
        ))
        self.assertEqual(["E4", "E6", "E1", "E7"], codigos(r))


class ReglasDeTiposTests(unittest.TestCase):

    def test_int_a_float_se_convierte(self):
        r = analizar_fuente(programa("float a;\na = 1;"))
        self.assertEqual([], codigos(r))
        asignacion = next(n for n in recorrer(r.arbol_anotado) if n["type"] == "Asignacion")
        self.assertEqual("ConversionTipo", asignacion["children"][0]["type"])
        self.assertEqual(1.0, asignacion["children"][0]["valor_calculado"])

    def test_real_es_alias_de_float(self):
        r = analizar_fuente(programa("real r;\nr = 2;"))
        self.assertEqual([], codigos(r))
        self.assertEqual("float", r.tabla.buscar("r").tipo)

    def test_division_entera_trunca_hacia_cero(self):
        self.assertEqual(-3, _dividir_entero(-7, 2))
        self.assertEqual(3, _dividir_entero(7, 2))
        self.assertEqual(-1, _modulo_entero(-7, 2))
        r = analizar_fuente(programa("int x;\nx = (0 - 7) / 2;"))
        asignacion = next(n for n in recorrer(r.arbol_anotado) if n["type"] == "Asignacion")
        self.assertEqual(-3, asignacion["children"][0]["valor_calculado"])

    def test_division_entre_cero_no_se_pliega(self):
        r = analizar_fuente(programa("int x;\nx = 5 / 0;"))
        self.assertEqual([], codigos(r))
        asignacion = next(n for n in recorrer(r.arbol_anotado) if n["type"] == "Asignacion")
        self.assertNotIn("valor_calculado", asignacion["children"][0])

    def test_igualdad_entre_bool_y_entre_numeros(self):
        r = analizar_fuente(programa("bool f;\nf = true != false;\nf = 1 == 1.0;"))
        self.assertEqual([], codigos(r))

    def test_cout_con_cadenas(self):
        r = analizar_fuente(programa('int x;\ncout "x = " << x << "!";'))
        self.assertEqual([], codigos(r))

    def test_identificador_no_tiene_valor_en_compilacion(self):
        r = analizar_fuente(programa("int x, y;\nx = 1;\ny = x + 1;"))
        sumas = [n for n in recorrer(r.arbol_anotado) if n.get("operador") == "+"]
        self.assertNotIn("valor_calculado", sumas[0])


class FormateadorTests(unittest.TestCase):

    def test_salidas(self):
        with open(TEST_OFICIAL, encoding="utf-8") as archivo:
            r = analizar_fuente(archivo.read())
        texto = semantic_txt(r)
        marca = texto.index("Representación estructurada")
        arbol = json.loads(texto[texto.index("{", marca):])
        self.assertEqual("Programa", arbol["type"])
        self.assertIn("Recorrido semántico", texto)
        self.assertIn("x       int    0", symbols_txt(r.tabla))
        lineas = errores_txt(r.errores).splitlines()
        self.assertEqual(6, len(lineas))
        self.assertTrue(all(l.startswith("[SEMANTICO] [") for l in lineas))


if __name__ == "__main__":
    unittest.main()

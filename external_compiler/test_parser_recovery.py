import os
import sys
import unittest


COMPILER_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(COMPILER_DIR)
IDE_DIR = os.path.join(PROJECT_DIR, "ide")
if COMPILER_DIR not in sys.path:
    sys.path.insert(0, COMPILER_DIR)
if IDE_DIR not in sys.path:
    sys.path.insert(0, IDE_DIR)

from lexer.dfa_lexer import DFALexer
from parser.ast_formatter import ASTFormatter
from parser.parser import Parser
from core.ast_text import ast_to_connected_text


def parse_source(source):
    raw_tokens, lexical_errors = DFALexer().tokenize(source)
    tokens = [
        (token.tipo, token.valor, token.linea, token.columna)
        for token in raw_tokens
        if token.tipo not in ("ERROR", "EOF")
    ]
    ast, syntax_errors = Parser(tokens).parse()
    return ASTFormatter.to_dict(ast), lexical_errors, syntax_errors


def parse_source_with_node(source):
    raw_tokens, lexical_errors = DFALexer().tokenize(source)
    tokens = [
        (token.tipo, token.valor, token.linea, token.columna)
        for token in raw_tokens
        if token.tipo not in ("ERROR", "EOF")
    ]
    ast, syntax_errors = Parser(tokens).parse()
    return ast, lexical_errors, syntax_errors


def walk(node):
    if not node:
        return
    yield node
    for child in node.get("children", []):
        yield from walk(child)


def labels(ast):
    return [node.get("label", "") for node in walk(ast)]


def forma(node):
    """Estructura del árbol sin posiciones, para comparar dos programas."""
    return {
        "type": node["type"],
        "label": node.get("label"),
        "children": [forma(child) for child in node.get("children", [])],
    }


def infijo(node):
    """Reconstruye la expresión totalmente parentizada desde el árbol binario."""
    tipo = node["type"]
    if tipo == "OperacionBinaria":
        izquierda, derecha = node["children"]
        return f"({infijo(izquierda)} {node['operador']} {infijo(derecha)})"
    if tipo == "OperacionUnaria":
        return f"({node['operador']} {infijo(node['children'][0])})"
    if tipo == "Literal":
        valor = node["valor"]
        if valor is True:
            return "true"
        if valor is False:
            return "false"
        return str(valor)
    return node["nombre"]


def expresion_asignada(sentencia):
    """Árbol de la expresión de la primera asignación del programa."""
    ast, _, syntax_errors = parse_source(
        "main {\n int x, y, z;\n float a, b, c;\n " + sentencia + "\n}"
    )
    assert syntax_errors == [], syntax_errors
    asignacion = next(nodo for nodo in walk(ast) if nodo["type"] == "Asignacion")
    return infijo(asignacion["children"][0])


class ParserRecoveryTests(unittest.TestCase):
    def test_real_and_if_without_parentheses_are_preserved(self):
        ast, lexical_errors, syntax_errors = parse_source(
            """main {
  real a, b, c;
  if 2 > 3 then
    a = 1;
  end;
}"""
        )

        self.assertEqual([], lexical_errors)
        self.assertEqual([], syntax_errors)
        self.assertIn("DECLARACION_VARIABLE: real a, b, c", labels(ast))
        self.assertIn("OPERACION: >", labels(ast))

        declaracion = next(
            nodo for nodo in walk(ast) if nodo["type"] == "DeclaracionVariable"
        )
        self.assertEqual("float", declaracion["tipo"])
        self.assertEqual("real", declaracion["tipo_lexema"])
        self.assertEqual(
            [("a", 2, 8), ("b", 2, 11), ("c", 2, 14)],
            [
                (ident["nombre"], ident["linea"], ident["columna"])
                for ident in declaracion["identificadores"]
            ],
        )

    def test_conditions_parse_with_and_without_parentheses(self):
        con_parentesis, _, errores_con = parse_source(
            """main {
  int x;
  if (x > 1) then
    x = 1;
  end;
  while (x < 9) {
    x = x + 1;
  };
}"""
        )
        sin_parentesis, _, errores_sin = parse_source(
            """main {
  int x;
  if x > 1 then
    x = 1;
  end;
  while x < 9
    x = x + 1;
  end;
}"""
        )

        self.assertEqual([], errores_con)
        self.assertEqual([], errores_sin)
        self.assertIn("OPERACION: >", labels(con_parentesis))
        self.assertIn("OPERACION: >", labels(sin_parentesis))
        self.assertIn("OPERACION: <", labels(con_parentesis))
        self.assertIn("OPERACION: <", labels(sin_parentesis))

    def test_do_while_until_accepts_body_closed_with_end(self):
        ast, lexical_errors, syntax_errors = parse_source(
            """main {
  int x, y;
  do
    y = y + 1;
    while x > 7
      x = x + 1;
    end
  until y == 5
}"""
        )

        tree_labels = labels(ast)
        self.assertEqual([], lexical_errors)
        self.assertEqual([], syntax_errors)
        self.assertIn("CUERPO_DO", tree_labels)
        self.assertIn("CONDICION_WHILE", tree_labels)
        self.assertIn("CUERPO_WHILE", tree_labels)
        self.assertIn("CONDICION_UNTIL", tree_labels)
        self.assertIn("ASIGNACION: x", tree_labels)

    def test_official_semantic_test_file_has_no_syntax_errors(self):
        ruta = os.path.join(PROJECT_DIR, "pruebas", "TestSemantica.txt")
        with open(ruta, encoding="utf-8") as archivo:
            ast, lexical_errors, syntax_errors = parse_source(archivo.read())

        self.assertEqual([], lexical_errors)
        self.assertEqual([], [error.mensaje for error in syntax_errors])
        self.assertIsNotNone(ast)

    def test_sample_programs_have_no_syntax_errors(self):
        muestras = os.path.join(IDE_DIR, "samples")
        archivos = [
            "test_basico.caos",
            "test_ciclo.caos",
            "test_condicional.caos",
        ]
        for nombre in archivos:
            with self.subTest(muestra=nombre):
                with open(os.path.join(muestras, nombre), encoding="utf-8") as archivo:
                    _, lexical_errors, syntax_errors = parse_source(archivo.read())
                self.assertEqual([], lexical_errors)
                self.assertEqual([], [error.mensaje for error in syntax_errors])

    def test_ast_carries_what_the_semantic_phase_needs(self):
        ast, _, syntax_errors = parse_source(
            """main {
  int x;
  float a;
  a = 1.5;
  cin x;
}"""
        )

        self.assertEqual([], syntax_errors)

        declarados = [
            (ident["nombre"], ident["linea"], ident["columna"])
            for nodo in walk(ast)
            if nodo["type"] == "DeclaracionVariable"
            for ident in nodo["identificadores"]
        ]
        self.assertEqual([("x", 2, 7), ("a", 3, 9)], declarados)

        entrada = next(nodo for nodo in walk(ast) if nodo["type"] == "EntradaEstandar")
        self.assertEqual((5, 7), (entrada["identificador_linea"], entrada["identificador_columna"]))

        literal = next(
            nodo for nodo in walk(ast) if nodo.get("label", "").startswith("NUMERO:")
        )
        self.assertFalse(literal["es_entero"])
        self.assertEqual("flotante", literal["tipo_literal"])

    def test_expression_tree_respects_precedence_and_associativity(self):
        casos = [
            ("x = 2 + 3 - 1;", "((2 + 3) - 1)"),
            ("x = 2 + 3 * 4;", "(2 + (3 * 4))"),
            ("x = 10 - 4 - 3;", "((10 - 4) - 3)"),
            ("x = 100 / 10 / 2;", "((100 / 10) / 2)"),
            ("x = (5 - 3) * (8 / 2);", "((5 - 3) * (8 / 2))"),
            ("a = 24.0+4-1/3*2+34-1;", "((((24.0 + 4) - ((1 / 3) * 2)) + 34) - 1)"),
            ("y = 5+3-2*4/7-9;", "(((5 + 3) - ((2 * 4) / 7)) - 9)"),
            ("x = 6 + 8 / 9 * 8 / 3;", "(6 + (((8 / 9) * 8) / 3))"),
            ("x = 7 % 3 + 1;", "((7 % 3) + 1)"),
            # La potencia asocia a la derecha y pega más que la multiplicación.
            ("x = 2 ^ 3 ^ 2;", "(2 ^ (3 ^ 2))"),
            ("x = 2 * 3 ^ 2;", "(2 * (3 ^ 2))"),
        ]
        for sentencia, esperado in casos:
            with self.subTest(sentencia=sentencia):
                self.assertEqual(esperado, expresion_asignada(sentencia))

    def test_binary_tree_invariants_hold_for_the_official_file(self):
        ruta = os.path.join(PROJECT_DIR, "pruebas", "TestSemantica.txt")
        with open(ruta, encoding="utf-8") as archivo:
            ast, _, syntax_errors = parse_source(archivo.read())

        self.assertEqual([], syntax_errors)
        for nodo in walk(ast):
            with self.subTest(nodo=nodo.get("label")):
                self.assertTrue(nodo["linea"], "nodo sin línea")
                self.assertTrue(nodo["columna"], "nodo sin columna")
                self.assertTrue(nodo.get("label"), "nodo sin etiqueta")
                if nodo["type"] == "OperacionBinaria":
                    self.assertEqual(2, len(nodo["children"]))
                if nodo["type"] == "OperacionUnaria":
                    self.assertEqual(1, len(nodo["children"]))
                if nodo["type"] == "Literal":
                    self.assertEqual([], nodo["children"])

    def test_both_dialects_produce_the_same_tree(self):
        con_parentesis, _, errores_con = parse_source(
            """main {
  int x, y;
  float a;
  if (2 > 3) then
    y = a + 3;
  else
    y = y + 1;
  end;
  while (x > 7) {
    x = x + 1;
    cin x;
  };
  do
    y = (y + 1) * 2 + 1;
  while (x > 7) { x = 1; };
  until (y == 5);
}"""
        )
        sin_parentesis, _, errores_sin = parse_source(
            """main {
  int x, y;
  float a;
  if 2 > 3 then
    y = a + 3;
  else
    y = y + 1;
  end
  while x > 7
    x = x + 1;
    cin x;
  end
  do
    y = (y + 1) * 2 + 1;
    while x > 7
      x = 1;
    end
  until y == 5
}"""
        )

        self.assertEqual([], errores_con)
        self.assertEqual([], errores_sin)
        self.assertEqual(forma(con_parentesis), forma(sin_parentesis))

    def test_cout_accepts_the_four_forms_of_salida(self):
        casos = [
            ("cout x;", ["IDENTIFICADOR: x"]),
            ('cout "a";', ['CADENA: "a"']),
            ('cout "a" << x;', ['CADENA: "a"', "IDENTIFICADOR: x"]),
            ('cout x << "a";', ["IDENTIFICADOR: x", 'CADENA: "a"']),
            # Encadenar varios elementos es el mismo patrón repetido.
            ('cout "a" << x << "b";', ['CADENA: "a"', "IDENTIFICADOR: x", 'CADENA: "b"']),
            ('cout "s=" << x + y << "!";', ['CADENA: "s="', "OPERACION: +", 'CADENA: "!"']),
        ]
        for sentencia, esperado in casos:
            with self.subTest(sentencia=sentencia):
                ast, _, syntax_errors = parse_source(
                    "main {\n int x, y;\n " + sentencia + "\n}"
                )
                self.assertEqual([], syntax_errors)
                salida = next(nodo for nodo in walk(ast) if nodo.get("label") == "SALIDA")
                self.assertEqual(
                    esperado, [hijo.get("label") for hijo in salida["children"]]
                )

    def test_single_less_than_is_still_a_relational_operator(self):
        ast, _, syntax_errors = parse_source(
            """main {
  int x, y;
  cout x < y;
  if x < y then
    x = 1;
  end;
}"""
        )

        self.assertEqual([], syntax_errors)
        salida = next(nodo for nodo in walk(ast) if nodo.get("label") == "SALIDA")
        self.assertEqual(["OPERACION: <"], [h.get("label") for h in salida["children"]])

    def test_cout_with_leading_stream_operator_is_rejected(self):
        """'cout << x;' no está en la gramática: '<<' solo separa elementos."""
        _, _, syntax_errors = parse_source(
            """main {
  int x;
  cout << x;
}"""
        )

        self.assertNotEqual([], syntax_errors)

    def test_missing_operator_keeps_if_branches_and_marks_partial_condition(self):
        ast, lexical_errors, syntax_errors = parse_source(
            """main {
  if (4 > 2 && falta operando) then
    x = 1;
  else
    x = 2;
  end;
}"""
        )

        tree_labels = labels(ast)
        self.assertEqual([], lexical_errors)
        self.assertEqual(
            ["Se esperaba operador antes de 'operando'"],
            [error.mensaje for error in syntax_errors],
        )
        self.assertIn("OPERACION: &&", tree_labels)
        self.assertIn("ERROR: Se esperaba operador antes de 'operando'", tree_labels)
        self.assertIn("ENTONCES", tree_labels)
        self.assertIn("SINO", tree_labels)

    def test_missing_logical_operand_keeps_if_branches_and_marks_condition(self):
        ast, lexical_errors, syntax_errors = parse_source(
            """main {
  if (4 > 2 && ) then
    x = 1;
  else
    x = 2;
  end;
}"""
        )

        tree_labels = labels(ast)
        self.assertEqual([], lexical_errors)
        self.assertEqual(
            ["Se esperaba operando después de '&&'"],
            [error.mensaje for error in syntax_errors],
        )
        self.assertIn("OPERACION: >", tree_labels)
        self.assertIn("ERROR: Se esperaba operando después de '&&'", tree_labels)
        self.assertIn("ENTONCES", tree_labels)
        self.assertIn("SINO", tree_labels)

    def test_invalid_labels_do_not_break_repetition_or_following_while(self):
        ast, lexical_errors, syntax_errors = parse_source(
            """main {
  do-while-until)
  do
    y = y + 1;
  while (x > 7) {
    mas = 36 / 7;
    mas = 36 / 7;
  };
  until (y == 5);

  (while)
  while (y == 0) {
    cin mas;
    cout x;
  };
}"""
        )

        tree_labels = labels(ast)
        self.assertEqual([], lexical_errors)
        self.assertEqual(1, tree_labels.count("DO_WHILE_UNTIL"))
        self.assertEqual(1, tree_labels.count("WHILE"))
        self.assertIn("CUERPO_DO", tree_labels)
        self.assertIn("CONDICION_WHILE", tree_labels)
        self.assertIn("CUERPO_WHILE", tree_labels)
        self.assertIn("CONDICION_UNTIL", tree_labels)
        self.assertEqual(2, tree_labels.count("ASIGNACION: mas"))
        self.assertIn("ENTRADA: cin mas", tree_labels)
        self.assertIn("SALIDA: cout", tree_labels)
        self.assertEqual(
            [
                "Token inesperado '-' en encabezado do-while-until",
                "Token inesperado '(' en lista de sentencias",
            ],
            [error.mensaje for error in syntax_errors],
        )

    def test_spaced_decrement_behavior_is_preserved(self):
        ast, lexical_errors, syntax_errors = parse_source(
            """main {
  int c;
  c -
  -;
}"""
        )

        self.assertEqual([], lexical_errors)
        self.assertEqual([], syntax_errors)
        self.assertIn("DECREMENTO: c", labels(ast))

    def test_nodes_with_children_inherit_valid_locations(self):
        ast, lexical_errors, syntax_errors = parse_source(
            """main {
  int x;
  x = 10;
  if (x > 5) then
    cout x;
  end;
}"""
        )

        self.assertEqual([], lexical_errors)
        self.assertEqual([], syntax_errors)
        missing = [
            node.get("label")
            for node in walk(ast)
            if node.get("children")
            and (not node.get("linea") or not node.get("columna"))
        ]
        self.assertEqual([], missing)

    def test_analysis_and_connected_text_show_locations(self):
        ast_node, lexical_errors, syntax_errors = parse_source_with_node(
            """main {
  int x;
  x = 10;
}"""
        )
        ast_dict = ASTFormatter.to_dict(ast_node)

        self.assertEqual([], lexical_errors)
        self.assertEqual([], syntax_errors)
        analysis_text = ASTFormatter.to_text(ast_node)
        connected_text = ast_to_connected_text(ast_dict)
        self.assertIn("PROGRAMA [L1:C1]", analysis_text)
        self.assertIn("DECLARACIONES [L2:C3]", analysis_text)
        self.assertIn("ASIGNACION: x [L3:C3]", analysis_text)
        self.assertIn("PROGRAMA [L1:C1]", connected_text)
        self.assertIn("DECLARACIONES [L2:C3]", connected_text)
        self.assertIn("ASIGNACION: x [L3:C3]", connected_text)

    def test_syntax_error_keeps_position_of_found_token(self):
        _, lexical_errors, syntax_errors = parse_source(
            """main {
  if (4 > 2 && falta operando) then
    x = 1;
  end;
}"""
        )

        self.assertEqual([], lexical_errors)
        self.assertEqual(1, len(syntax_errors))
        self.assertEqual("Se esperaba operador antes de 'operando'", syntax_errors[0].mensaje)
        self.assertEqual((2, 22), (syntax_errors[0].linea, syntax_errors[0].columna))


if __name__ == "__main__":
    unittest.main()

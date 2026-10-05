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
        self.assertIn("DECLARACION_VARIABLE: real a, b, c", labels(ast))
        self.assertIn("OPERACION: >", labels(ast))
        self.assertEqual(
            [
                "Se esperaba '(' después de 'if'",
                "Se esperaba ')' después de condición",
            ],
            [error.mensaje for error in syntax_errors],
        )

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

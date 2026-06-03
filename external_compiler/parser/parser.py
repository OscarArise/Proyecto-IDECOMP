"""
parser.py
---------
Analizador sintáctico descendente recursivo para el lenguaje CAOS.
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass

from .ast_nodes import (
    ASTNode, Programa, ListaDeclaracion, Declaracion, DeclaracionVariable,
    ListaSentencias, Sentencia, Asignacion, Seleccion, Iteracion, Repeticion,
    EntradaEstandar, SalidaEstandar, Salida,
    Expresion, ExpresionSimple, Termino, Factor, Componente,
    Numero, Identificador, Cadena, Booleano, NodoError
)


@dataclass
class Token:
    """Representa un token de la salida del analizador léxico."""
    tipo: str
    valor: str
    linea: int
    columna: int

    def __repr__(self):
        return f"Token({self.tipo}, {self.valor!r}, {self.linea}, {self.columna})"


class SyntaxError:
    """Representa un error sintáctico encontrado durante el parsing."""
    def __init__(self, mensaje: str, linea: int = 0, columna: int = 0,
                 token_esperado: Optional[str] = None, token_encontrado: Optional[str] = None):
        self.mensaje = mensaje
        self.linea = linea
        self.columna = columna
        self.token_esperado = token_esperado
        self.token_encontrado = token_encontrado

    def __str__(self):
        prefix = f"[{self.linea}:{self.columna}] " if self.linea else ""
        return f"{prefix}Error sintáctico: {self.mensaje}"


class Parser:
    """
    Analizador sintáctico descendente recursivo para CAOS.

    Convierte una lista de tokens en un Árbol Sintáctico Abstracto (AST)
    siguiendo las reglas de la gramática de la Fase 2.
    """

    def __init__(self, tokens: List[Tuple[str, str, int, int]]):
        self.tokens = [Token(tipo, valor, linea, columna)
                       for tipo, valor, linea, columna in tokens]
        self.pos = 0
        self.errors: List[SyntaxError] = []
        self.current_token = self.tokens[0] if self.tokens else None

        self.type_starts = ("KW_INT", "KW_FLOAT", "KW_BOOL")
        self.statement_starts = ("IDENTIFIER", "KW_IF", "KW_WHILE", "KW_DO", "KW_CIN", "KW_COUT")
        self.declaration_starts = self.type_starts + self.statement_starts
        self.block_stops = ("LLAVE_DER", "KW_ELSE", "KW_END")

    def parse(self) -> Tuple[Optional[Programa], List[SyntaxError]]:
        try:
            programa = self._programa()
            return programa, self.errors
        except Exception as e:
            self.errors.append(SyntaxError(f"Error fatal: {str(e)}"))
            return None, self.errors

    # ========================================================================
    # Utilidades de navegación
    # ========================================================================

    def _advance(self):
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
            self.current_token = self.tokens[self.pos]
        else:
            self.pos = len(self.tokens)
            self.current_token = None

    def _peek(self, offset: int = 1) -> Optional[Token]:
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return None

    def _match(self, *tipos_esperados: str) -> bool:
        if not self.current_token:
            return False
        return self.current_token.tipo in tipos_esperados

    def _consume(self, tipo_esperado: str, mensaje: str = "") -> Optional[Token]:
        if not self.current_token:
            error = SyntaxError(
                mensaje or f"Se esperaba '{tipo_esperado}' pero se encontró fin de archivo",
                token_esperado=tipo_esperado
            )
            self.errors.append(error)
            return None

        if self.current_token.tipo != tipo_esperado:
            error = SyntaxError(
                mensaje or f"Se esperaba '{tipo_esperado}' pero se encontró '{self.current_token.valor}'",
                linea=self.current_token.linea,
                columna=self.current_token.columna,
                token_esperado=tipo_esperado,
                token_encontrado=self.current_token.tipo
            )
            self.errors.append(error)
            return None

        token = self.current_token
        self._advance()
        return token

    def _skip_on_error(self, *sync_tokens: str):
        """Salta tokens hasta encontrar uno de sincronización (sin consumirlo)."""
        while self.current_token and self.current_token.tipo not in sync_tokens:
            self._advance()

    def _sync_to_main_body(self) -> bool:
        """
        Recupera el inicio real del bloque main cuando hay tokens inválidos
        entre 'main' y la llave de apertura.
        Busca la primera LLAVE_IZQ cuyo siguiente token sea una declaración
        válida o la llave de cierre.
        """
        fallback_pos = None
        for index in range(self.pos, len(self.tokens)):
            token = self.tokens[index]
            if token.tipo != "LLAVE_IZQ":
                continue
            if fallback_pos is None:
                fallback_pos = index
            next_token = self.tokens[index + 1] if index + 1 < len(self.tokens) else None
            if not next_token or next_token.tipo in self.declaration_starts + ("LLAVE_DER",):
                self.pos = index
                self.current_token = self.tokens[self.pos]
                self._advance()
                return True

        if fallback_pos is not None:
            self.pos = fallback_pos
            self.current_token = self.tokens[self.pos]
            self._advance()
            return True

        return False

    def _recover_to_construct(self, context_stops: tuple = ()):
        """
        Recuperación en modo pánico: avanza hasta un punto seguro.
        Se detiene en ';', en cualquier stop del contexto, o en LLAVE_DER.
        Límite de 20 tokens para no volar demasiado.
        """
        if not self.current_token:
            return

        safe_sync = ("PUNTO_COMA",) + context_stops + ("LLAVE_DER",)
        tokens_advanced = 0
        max_advance = 20

        while self.current_token and tokens_advanced < max_advance:
            if self.current_token.tipo in safe_sync:
                break
            self._advance()
            tokens_advanced += 1

    def _report_unexpected_token(self, contexto: str = "esta parte del programa"):
        """Registra un token inesperado antes de entrar a recuperación."""
        tok = self.current_token
        if not tok:
            return
        self.errors.append(SyntaxError(
            f"Token inesperado '{tok.valor}' en {contexto}",
            linea=tok.linea,
            columna=tok.columna,
            token_encontrado=tok.tipo
        ))

    # ========================================================================
    # REGLAS GRAMATICALES
    # ========================================================================

    def _programa(self) -> Optional[Programa]:
        """programa → main { lista_declaracion }"""
        programa = Programa()

        if not self._match("KW_MAIN"):
            self.errors.append(SyntaxError(
                "Se esperaba 'main' al inicio del programa",
                linea=self.current_token.linea if self.current_token else 0,
                columna=self.current_token.columna if self.current_token else 0
            ))
            return None

        tok_main = self.current_token
        programa.linea = tok_main.linea
        programa.columna = tok_main.columna
        self._advance()  # consume 'main'

        if not self._consume("LLAVE_IZQ", "Se esperaba '{' después de 'main'"):
            self._sync_to_main_body()

        programa.lista_declaracion = self._lista_declaracion()

        if not self._consume("LLAVE_DER", "Se esperaba '}' para cerrar main"):
            self._skip_on_error("LLAVE_DER")

        if programa.lista_declaracion:
            programa.children = programa.lista_declaracion.children

        return programa

    def _lista_declaracion(self) -> Optional[ListaDeclaracion]:
        """lista_declaracion → lista_declaracion declaracion | declaracion | ε"""
        lista = ListaDeclaracion()

        while self.current_token and self.current_token.tipo != "LLAVE_DER":
            if self._match("PUNTO_COMA"):
                self._advance()
                continue

            if self.current_token.tipo not in self.declaration_starts:
                self._report_unexpected_token("lista de declaraciones")
                self._recover_to_construct(("LLAVE_DER",))
                if self._match("PUNTO_COMA"):
                    self._advance()
                continue

            decl = self._declaracion()
            if decl:
                lista.declaraciones.append(decl)
                lista.children.append(decl)
            else:
                self._recover_to_construct(("LLAVE_DER",))
                if self._match("PUNTO_COMA"):
                    self._advance()

        return lista if lista.declaraciones else None

    def _declaracion(self) -> Optional[Declaracion]:
        """declaracion → declaracion_variable | lista_sentencias"""
        decl = Declaracion()

        if self.current_token and self.current_token.tipo in self.type_starts:
            decl_var = self._declaracion_variable()
            if decl_var:
                decl.contenido = decl_var
                decl.children = [decl_var]
                return decl

        if self.current_token and self.current_token.tipo in self.statement_starts:
            lista_sent = self._lista_sentencias()
            if lista_sent:
                decl.contenido = lista_sent
                decl.children = lista_sent.children
                return decl

        return None

    def _declaracion_variable(self) -> Optional[DeclaracionVariable]:
        """declaracion_variable → tipo identificador { , identificador } ;"""
        decl = DeclaracionVariable()
        tok = self.current_token

        if self._match("KW_INT"):
            decl.tipo = "int"
        elif self._match("KW_FLOAT"):
            decl.tipo = "float"
        elif self._match("KW_BOOL"):
            decl.tipo = "bool"
        else:
            self.errors.append(SyntaxError(
                f"Se esperaba tipo (int, float, bool)",
                linea=tok.linea if tok else 0,
                columna=tok.columna if tok else 0
            ))
            return None

        decl.linea = tok.linea
        decl.columna = tok.columna
        self._advance()

        decl.identificadores = self._lista_identificadores()

        if not self._consume("PUNTO_COMA", "Se esperaba ';' después de declaración de variable"):
            self._skip_on_error("PUNTO_COMA", "KW_INT", "KW_FLOAT", "KW_BOOL")

        return decl

    def _lista_identificadores(self) -> List[str]:
        """id { , id }"""
        identificadores = []

        if not self._match("IDENTIFIER"):
            tok = self.current_token
            self.errors.append(SyntaxError(
                f"Se esperaba identificador pero se encontró '{tok.valor if tok else 'EOF'}'",
                linea=tok.linea if tok else 0,
                columna=tok.columna if tok else 0
            ))
            return []

        identificadores.append(self.current_token.valor)
        self._advance()

        while self._match("COMA"):
            self._advance()
            if not self._match("IDENTIFIER"):
                tok = self.current_token
                self.errors.append(SyntaxError(
                    "Se esperaba identificador después de coma",
                    linea=tok.linea if tok else 0,
                    columna=tok.columna if tok else 0
                ))
                break
            identificadores.append(self.current_token.valor)
            self._advance()

        return identificadores

    def _lista_sentencias(self, stop_tokens: tuple = ()) -> Optional[ListaSentencias]:
        """lista_sentencias → lista_sentencias sentencia | ε"""
        lista = ListaSentencias()

        effective_stops = stop_tokens + self.block_stops

        while self.current_token and self.current_token.tipo not in effective_stops:
            if self._match("PUNTO_COMA"):
                self._advance()
                continue

            if self._match("LLAVE_IZQ"):
                self._report_unexpected_token("lista de sentencias")
                self._advance()
                continue

            if self.current_token.tipo not in self.statement_starts:
                self._report_unexpected_token("lista de sentencias")
                self._recover_to_construct(effective_stops)
                if self._match("PUNTO_COMA"):
                    self._advance()
                continue

            sent = self._sentencia()
            if sent:
                lista.sentencias.append(sent)
                lista.children.append(sent)
            else:
                self._recover_to_construct(effective_stops)
                if self._match("PUNTO_COMA"):
                    self._advance()

        return lista if lista.sentencias else None

    def _sentencia(self) -> Optional[Sentencia]:
        """sentencia → seleccion | iteracion | repeticion | sent_in | sent_out | asignacion"""
        sent = Sentencia()

        if not self.current_token:
            return None

        tok = self.current_token
        sent.linea = tok.linea
        sent.columna = tok.columna

        if tok.tipo == "KW_IF":
            contenido = self._seleccion()
        elif tok.tipo == "KW_WHILE":
            contenido = self._iteracion()
        elif tok.tipo == "KW_DO":
            contenido = self._repeticion()
        elif tok.tipo == "KW_CIN":
            contenido = self._sent_in()
        elif tok.tipo == "KW_COUT":
            contenido = self._sent_out()
        elif tok.tipo == "IDENTIFIER":
            contenido = self._asignacion()
        else:
            return None

        if contenido:
            sent.contenido = contenido
            sent.children = [contenido]

        return sent

    def _asignacion(self) -> Optional[Asignacion]:
        """asignacion → id = expresion ; | id = ;"""
        asig = Asignacion()

        if not self._match("IDENTIFIER"):
            self.errors.append(SyntaxError(
                "Se esperaba identificador en asignación",
                linea=self.current_token.linea if self.current_token else 0,
                columna=self.current_token.columna if self.current_token else 0
            ))
            return None

        tok_id = self.current_token
        asig.identificador = tok_id.valor
        asig.linea = tok_id.linea
        asig.columna = tok_id.columna
        self._advance()

        if not self._consume("ASIGNACION", "Se esperaba '=' en asignación"):
            self._skip_on_error("PUNTO_COMA", *self.block_stops)
            if self._match("PUNTO_COMA"):
                self._advance()
            return asig

        if self._match("PUNTO_COMA"):
            # asignación sin expresión: reportar error
            tok = self.current_token
            self.errors.append(SyntaxError(
                f"Se esperaba expresión después de '=' en '{asig.identificador}'",
                linea=tok.linea,
                columna=tok.columna
            ))
            self._advance()  # consumir ';'
            return asig

        asig.expresion = self._expresion()
        if asig.expresion:
            asig.children = [asig.expresion]

        self._consume("PUNTO_COMA", "Se esperaba ';' al final de asignación")

        return asig

    def _seleccion(self) -> Optional[Seleccion]:
        """seleccion → if expresion then lista_sentencias [ else lista_sentencias ] end [;]"""
        sel = Seleccion()

        tok_if = self._consume("KW_IF", "Se esperaba 'if'")
        if not tok_if:
            return None
        sel.linea = tok_if.linea
        sel.columna = tok_if.columna

        sel.condicion = self._expresion()
        if not sel.condicion:
            self.errors.append(SyntaxError(
                "Se esperaba condición después de 'if'",
                linea=self.current_token.linea if self.current_token else 0,
                columna=self.current_token.columna if self.current_token else 0
            ))
            self._skip_on_error("KW_THEN", "KW_ELSE", "KW_END")

        if not self._consume("KW_THEN", "Se esperaba 'then' después de condición"):
            self._skip_on_error("KW_THEN", "KW_ELSE", "KW_END")
            if self._match("KW_THEN"):
                self._advance()

        sel.rama_entonces = self._lista_sentencias(stop_tokens=("KW_ELSE", "KW_END"))

        if self._match("KW_ELSE"):
            self._advance()
            sel.rama_sino = self._lista_sentencias(stop_tokens=("KW_END",))

        if not self._consume("KW_END", "Se esperaba 'end' para cerrar if"):
            self._skip_on_error("KW_END", "LLAVE_DER")
            if self._match("KW_END"):
                self._advance()

        if self.current_token and self.current_token.tipo == "PUNTO_COMA":
            self._advance()

        children = []
        if sel.condicion:
            children.append(sel.condicion)
        if sel.rama_entonces:
            children.extend(sel.rama_entonces.children)
        if sel.rama_sino:
            children.extend(sel.rama_sino.children)
        sel.children = children

        return sel

    def _iteracion(self) -> Optional[Iteracion]:
        """iteracion → while expresion { lista_sentencias } [;] | while expresion lista_sentencias end"""
        iter_node = Iteracion()

        tok_while = self._consume("KW_WHILE", "Se esperaba 'while'")
        if not tok_while:
            return None
        iter_node.linea = tok_while.linea
        iter_node.columna = tok_while.columna

        iter_node.condicion = self._expresion()

        # Soporte para dos formas de cuerpo:
        #   1. { sentencias }   (estilo del archivo de prueba)
        #   2. sentencias end   (estilo gramatical original)
        if self._match("LLAVE_IZQ"):
            self._advance()
            iter_node.cuerpo = self._lista_sentencias(stop_tokens=("LLAVE_DER",))
            if self._match("LLAVE_DER"):
                self._advance()
            # ';' opcional después de '}'
            if self._match("PUNTO_COMA"):
                self._advance()
        else:
            iter_node.cuerpo = self._lista_sentencias(stop_tokens=("KW_END",))
            if not self._consume("KW_END", "Se esperaba 'end' para cerrar while"):
                self._skip_on_error("KW_END", "LLAVE_DER")

        children = []
        if iter_node.condicion:
            children.append(iter_node.condicion)
        if iter_node.cuerpo:
            children.extend(iter_node.cuerpo.children)
        iter_node.children = children

        return iter_node

    def _repeticion(self) -> Optional[Repeticion]:
        """
        Gramática propia del proyecto:
            repeticion → do lista_sentencias while ( expresion ) { lista_sentencias } ; until ( expresion ) ;

        Ambas formas de cuerpo son válidas:
            while (cond) { sentencias }   ← con bloque
            while (cond) end              ← con end (compatibilidad)
        until es el terminador formal del do-while.
        """
        rep = Repeticion()

        tok_do = self._consume("KW_DO", "Se esperaba 'do'")
        if not tok_do:
            return None
        rep.linea = tok_do.linea
        rep.columna = tok_do.columna

        # Cuerpo principal: sentencias hasta 'while'
        rep.cuerpo = self._lista_sentencias(stop_tokens=("KW_WHILE",))

        if not self._consume("KW_WHILE", "Se esperaba 'while' después del cuerpo do"):
            self._skip_on_error("KW_UNTIL", "PUNTO_COMA", "LLAVE_DER")
            return rep

        # Condición del while
        rep.condicion = self._expresion()

        # Bloque { sentencias } — es la forma canónica del proyecto
        if self._match("LLAVE_IZQ"):
            self._advance()
            extra = self._lista_sentencias(stop_tokens=("LLAVE_DER",))
            if extra and rep.cuerpo:
                rep.cuerpo.sentencias.extend(extra.sentencias)
                rep.cuerpo.children.extend(extra.children)
            elif extra:
                rep.cuerpo = extra
            if self._match("LLAVE_DER"):
                self._advance()
        elif self._match("KW_END"):
            # Forma alternativa con 'end' (compatibilidad)
            self._advance()

        # ';' opcional después del bloque
        if self._match("PUNTO_COMA"):
            self._advance()

        # until (cond); — terminador formal del do-while en este lenguaje
        if self._match("KW_UNTIL"):
            self._advance()
            rep.until_condicion = self._expresion()
            if self._match("PUNTO_COMA"):
                self._advance()

        children = []
        if rep.cuerpo:
            children.extend(rep.cuerpo.children)
        if rep.condicion:
            children.append(rep.condicion)
        if rep.until_condicion:
            children.append(rep.until_condicion)
        rep.children = children

        return rep

    def _sent_in(self) -> Optional[EntradaEstandar]:
        """sent_in → cin >> id ;
        '>>' se tokeniza como dos MAYOR consecutivos.
        Si faltan uno o los dos '>', se reporta error con posición exacta.
        """
        entrada = EntradaEstandar()

        tok_cin = self._consume("KW_CIN", "Se esperaba 'cin'")
        if not tok_cin:
            return None
        entrada.linea = tok_cin.linea
        entrada.columna = tok_cin.columna

        vio_primer_mayor = False

        # Primer '>'
        if self._match("MAYOR"):
            vio_primer_mayor = True
            self._advance()
        else:
            tok = self.current_token
            self.errors.append(SyntaxError(
                f"Se esperaba '>>' después de 'cin' pero se encontró '{tok.valor if tok else 'EOF'}'",
                linea=tok.linea if tok else tok_cin.linea,
                columna=tok.columna if tok else tok_cin.columna
            ))
            if not self._match("IDENTIFIER", "PUNTO_COMA"):
                self._skip_on_error("IDENTIFIER", "PUNTO_COMA")

        # Segundo '>'
        if self._match("MAYOR"):
            self._advance()
        elif vio_primer_mayor:
            tok = self.current_token
            self.errors.append(SyntaxError(
                "Se esperaba segundo '>' de '>>' en cin",
                linea=tok.linea if tok else tok_cin.linea,
                columna=tok.columna if tok else tok_cin.columna
            ))

        if not self._match("IDENTIFIER"):
            tok = self.current_token
            self.errors.append(SyntaxError(
                "Se esperaba identificador después de 'cin >>'",
                linea=tok.linea if tok else 0,
                columna=tok.columna if tok else 0
            ))
            self._skip_on_error("PUNTO_COMA")
            if self._match("PUNTO_COMA"):
                self._advance()
            return entrada

        entrada.identificador = self.current_token.valor
        self._advance()

        self._consume("PUNTO_COMA", "Se esperaba ';' después de cin")

        return entrada

    def _sent_out(self) -> Optional[SalidaEstandar]:
        """sent_out → cout << salida ;
        '<<' se tokeniza como dos MENOR consecutivos.
        Si faltan uno o los dos '<', se reporta error con posición exacta.
        """
        salida_node = SalidaEstandar()

        tok_cout = self._consume("KW_COUT", "Se esperaba 'cout'")
        if not tok_cout:
            return None
        salida_node.linea = tok_cout.linea
        salida_node.columna = tok_cout.columna

        vio_primer_menor = False

        # Primer '<'
        if self._match("MENOR"):
            vio_primer_menor = True
            self._advance()
        else:
            tok = self.current_token
            self.errors.append(SyntaxError(
                f"Se esperaba '<<' después de 'cout' pero se encontró '{tok.valor if tok else 'EOF'}'",
                linea=tok.linea if tok else tok_cout.linea,
                columna=tok.columna if tok else tok_cout.columna
            ))
            if not self._match("IDENTIFIER", "INT_NUM", "FLOAT_NUM", "STRING", "PUNTO_COMA"):
                self._skip_on_error("IDENTIFIER", "INT_NUM", "FLOAT_NUM", "STRING", "PUNTO_COMA")

        # Segundo '<'
        if self._match("MENOR"):
            self._advance()
        elif vio_primer_menor:
            tok = self.current_token
            self.errors.append(SyntaxError(
                "Se esperaba segundo '<' de '<<' en cout",
                linea=tok.linea if tok else tok_cout.linea,
                columna=tok.columna if tok else tok_cout.columna
            ))

        salida_item = self._salida()
        if salida_item:
            salida_node.salidas.append(salida_item)
            salida_node.children = [salida_item]

        self._consume("PUNTO_COMA", "Se esperaba ';' después de cout")

        return salida_node

    def _salida(self) -> Optional[Salida]:
        """salida → cadena | expresion | cadena << expresion | expresion << cadena"""
        salida = Salida()

        if self._match("STRING"):
            cadena = Cadena(valor=self.current_token.valor)
            salida.elementos.append(cadena)
            self._advance()
            if self._match("MENOR"):
                self._advance()
                if self._match("MENOR"):
                    self._advance()
                    expr = self._expresion()
                    if expr:
                        salida.elementos.append(expr)
        else:
            expr = self._expresion()
            if expr:
                salida.elementos.append(expr)
                if self._match("MENOR"):
                    self._advance()
                    if self._match("MENOR"):
                        self._advance()
                        if self._match("STRING"):
                            cadena = Cadena(valor=self.current_token.valor)
                            salida.elementos.append(cadena)
                            self._advance()

        salida.children = salida.elementos
        return salida if salida.elementos else None

    # ========================================================================
    # EXPRESIONES (PRECEDENCIA)
    # ========================================================================

    def _expresion(self) -> Optional[Expresion]:
        """expresion → expresion_simple [ rel_op expresion_simple ]"""
        expr = Expresion()

        if self.current_token:
            expr.linea = self.current_token.linea
            expr.columna = self.current_token.columna

        expr.izquierda = self._expresion_simple()

        if self.current_token and self.current_token.tipo in (
                "MAYOR", "MENOR", "MAYOR_IGUAL", "MENOR_IGUAL", "IGUAL", "DIFERENTE"):
            expr.operador = self.current_token.valor
            self._advance()
            expr.derecha = self._expresion_simple()

        if expr.izquierda:
            expr.children = [expr.izquierda]
            if expr.derecha:
                expr.children.append(expr.derecha)

        return expr if expr.izquierda else None

    def _expresion_simple(self) -> Optional[ExpresionSimple]:
        """expresion_simple → termino { suma_op termino }"""
        exp_simple = ExpresionSimple()

        if self.current_token:
            exp_simple.linea = self.current_token.linea
            exp_simple.columna = self.current_token.columna

        termino = self._termino()
        if not termino:
            return None

        exp_simple.terminos.append(termino)

        while self.current_token and self.current_token.tipo in ("SUMA", "RESTA", "INCREMENTO", "DECREMENTO"):
            exp_simple.operadores.append(self.current_token.valor)
            self._advance()
            siguiente = self._termino()
            if siguiente:
                exp_simple.terminos.append(siguiente)
            else:
                break

        exp_simple.children = exp_simple.terminos
        return exp_simple

    def _termino(self) -> Optional[Termino]:
        """termino → factor { mult_op factor }"""
        termino = Termino()

        if self.current_token:
            termino.linea = self.current_token.linea
            termino.columna = self.current_token.columna

        factor = self._factor()
        if not factor:
            return None

        termino.factores.append(factor)

        while self.current_token and self.current_token.tipo in ("MULTIPLICACION", "DIVISION", "MODULO"):
            termino.operadores.append(self.current_token.valor)
            self._advance()
            siguiente = self._factor()
            if siguiente:
                termino.factores.append(siguiente)
            else:
                break

        termino.children = termino.factores
        return termino

    def _factor(self) -> Optional[Factor]:
        """factor → componente { pot_op componente }"""
        factor = Factor()

        if self.current_token:
            factor.linea = self.current_token.linea
            factor.columna = self.current_token.columna

        componente = self._componente()
        if not componente:
            return None

        factor.componentes.append(componente)

        while self._match("POTENCIA"):
            factor.operadores.append(self.current_token.valor)
            self._advance()
            siguiente = self._componente()
            if siguiente:
                factor.componentes.append(siguiente)
            else:
                break

        factor.children = factor.componentes
        return factor

    def _componente(self) -> Optional[Componente]:
        """componente → ( expresion ) | número | id | bool | op_logico componente"""
        comp = Componente()

        if not self.current_token:
            return None

        comp.linea = self.current_token.linea
        comp.columna = self.current_token.columna

        if self._match("PAR_IZQ"):
            self._advance()
            comp.tipo = "expresion"
            comp.expresion = self._expresion()
            if not self._consume("PAR_DER", "Se esperaba ')'"):
                self._skip_on_error("PAR_DER", "PUNTO_COMA", "KW_THEN")
                if self._match("PAR_DER"):
                    self._advance()
            comp.children = [comp.expresion] if comp.expresion else []

        elif self._match("INT_NUM", "FLOAT_NUM"):
            comp.tipo = "numero"
            try:
                if self.current_token.tipo == "INT_NUM":
                    comp.valor = int(self.current_token.valor)
                    comp.es_entero = True
                else:
                    comp.valor = float(self.current_token.valor)
                    comp.es_entero = False
            except ValueError:
                comp.valor = 0
                comp.es_entero = True
            comp.children = [Numero(valor=comp.valor)]
            self._advance()

        elif self._match("IDENTIFIER"):
            comp.tipo = "identificador"
            comp.valor = self.current_token.valor
            comp.children = [Identificador(nombre=comp.valor)]
            self._advance()

        elif self._match("KW_TRUE", "KW_FALSE"):
            comp.tipo = "booleano"
            comp.valor = self.current_token.tipo == "KW_TRUE"
            comp.children = [Booleano(valor=comp.valor)]
            self._advance()

        elif self._match("AND", "OR", "NEGACION"):
            comp.tipo = "logico"
            comp.operador_logico = self.current_token.valor
            tok_op = self.current_token
            self._advance()
            comp.siguiente = self._componente()
            if not comp.siguiente:
                self.errors.append(SyntaxError(
                    f"Se esperaba componente después de '{tok_op.valor}'",
                    linea=tok_op.linea,
                    columna=tok_op.columna
                ))
                self._skip_on_error("PAR_DER", "PUNTO_COMA", "KW_THEN", "KW_ELSE", "KW_END")
                return comp
            comp.children = [comp.siguiente]

        else:
            tok = self.current_token
            self.errors.append(SyntaxError(
                f"Se esperaba componente pero se encontró '{tok.valor}'",
                linea=tok.linea,
                columna=tok.columna
            ))
            return None

        return comp
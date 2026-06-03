"""
parser.py
---------
Analizador sintáctico descendente recursivo para el lenguaje CAOS.

Implementa un parser LL(1) basado en la gramática especificada en la Fase 2.
Construye un Árbol Sintáctico Abstracto (AST) y reporta errores sintácticos
con línea y columna.
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass

from .ast_nodes import (
    # Nodos
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
        """
        Inicializa el parser.
        
        tokens: Lista de tuplas (tipo, valor, línea, columna) del analizador léxico
        """
        self.tokens = [Token(tipo, valor, linea, columna) 
                      for tipo, valor, linea, columna in tokens]
        self.pos = 0
        self.errors: List[SyntaxError] = []
        self.current_token = self.tokens[0] if self.tokens else None

    def parse(self) -> Tuple[Optional[Programa], List[SyntaxError]]:
        """
        Inicia el análisis sintáctico.
        
        Retorna: (árbol AST, lista de errores)
        """
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
        """Avanza al siguiente token."""
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
            self.current_token = self.tokens[self.pos]
        else:
            self.pos = len(self.tokens)
            self.current_token = None

    def _peek(self, offset: int = 1) -> Optional[Token]:
        """Mira el token que viene sin avanzar."""
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return None

    def _match(self, *tipos_esperados: str) -> bool:
        """Verifica si el token actual coincide con alguno de los tipos esperados."""
        if not self.current_token:
            return False
        return self.current_token.tipo in tipos_esperados

    def _consume(self, tipo_esperado: str, mensaje: str = "") -> Optional[Token]:
        """
        Consume un token del tipo esperado. Si no coincide, reporta error.
        """
        if not self.current_token:
            error = SyntaxError(
                mensaje or f"Se esperaba {tipo_esperado} pero se encontró EOF",
                token_esperado=tipo_esperado
            )
            self.errors.append(error)
            return None

        if self.current_token.tipo != tipo_esperado:
            error = SyntaxError(
                mensaje or f"Se esperaba {tipo_esperado} pero se encontró {self.current_token.tipo}",
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
        """Salta tokens hasta encontrar uno de sincronización."""
        while self.current_token and self.current_token.tipo not in sync_tokens:
            self._advance()

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

        self._advance()  # consume main

        if not self._consume("LLAVE_IZQ", "Se esperaba '{' después de 'main'"):
            self._skip_on_error("LLAVE_DER", "KW_IF", "KW_WHILE", "KW_DO")

        programa.lista_declaracion = self._lista_declaracion()

        if not self._consume("LLAVE_DER", "Se esperaba '}' para cerrar main"):
            self._skip_on_error()

        if programa.lista_declaracion:
            programa.children = programa.lista_declaracion.children

        return programa

    def _lista_declaracion(self) -> Optional[ListaDeclaracion]:
        """lista_declaracion → lista_declaracion declaracion | declaracion | ε"""
        lista = ListaDeclaracion()

        while (self.current_token and 
               self.current_token.tipo in ("KW_INT", "KW_FLOAT", "KW_REAL", "KW_BOOL", 
                                          "IDENTIFIER", "KW_IF", "KW_WHILE", 
                                          "KW_DO", "KW_CIN", "KW_COUT")):
            decl = self._declaracion()
            if decl:
                lista.declaraciones.append(decl)
                lista.children.append(decl)

            # Prevenir bucle infinito si algo falla
            if not decl:
                break

        return lista if lista.declaraciones else None

    def _declaracion(self) -> Optional[Declaracion]:
        """declaracion → declaracion_variable | lista_sentencias"""
        decl = Declaracion()

        # Intenta declaración de variable
        if self.current_token and self.current_token.tipo in ("KW_INT", "KW_FLOAT", "KW_REAL", "KW_BOOL"):
            decl_var = self._declaracion_variable()
            if decl_var:
                decl.contenido = decl_var
                decl.children = [decl_var]
                return decl

        # Intenta lista de sentencias
        if self.current_token and self.current_token.tipo in ("IDENTIFIER", "KW_IF", "KW_WHILE", 
                                                               "KW_DO", "KW_CIN", "KW_COUT"):
            lista_sent = self._lista_sentencias()
            if lista_sent:
                decl.contenido = lista_sent
                decl.children = lista_sent.children
                return decl

        return None

    def _declaracion_variable(self) -> Optional[DeclaracionVariable]:
        """declaracion_variable → tipo identificador ;"""
        decl = DeclaracionVariable()

        # Obtener tipo
        if self._match("KW_INT"):
            decl.tipo = "int"
            self._advance()
        elif self._match("KW_FLOAT"):
            decl.tipo = "float"
            self._advance()
        elif self._match("KW_REAL"):
            decl.tipo = "real"
            self._advance()
        elif self._match("KW_BOOL"):
            decl.tipo = "bool"
            self._advance()
        else:
            self.errors.append(SyntaxError(
                f"Se esperaba tipo (int, float, bool) pero se encontró {self.current_token.tipo if self.current_token else 'EOF'}",
                linea=self.current_token.linea if self.current_token else 0
            ))
            return None

        # Obtener identificadores (puede ser uno o varios separados por comas)
        decl.identificadores = self._lista_identificadores()

        if not self._consume("PUNTO_COMA", "Se esperaba ';' después de declaración de variable"):
            self._skip_on_error("PUNTO_COMA", "KW_INT", "KW_FLOAT", "KW_REAL", "KW_BOOL")

        return decl

    def _lista_identificadores(self) -> List[str]:
        """identificador → id | identificador , id"""
        identificadores = []

        if not self._match("IDENTIFIER"):
            self.errors.append(SyntaxError(
                f"Se esperaba identificador pero se encontró {self.current_token.tipo if self.current_token else 'EOF'}",
                linea=self.current_token.linea if self.current_token else 0
            ))
            return []

        identificadores.append(self.current_token.valor)
        self._advance()

        while self._match("COMA"):
            self._advance()
            if not self._match("IDENTIFIER"):
                self.errors.append(SyntaxError(
                    "Se esperaba identificador después de coma",
                    linea=self.current_token.linea if self.current_token else 0
                ))
                break
            identificadores.append(self.current_token.valor)
            self._advance()

        return identificadores

    def _lista_sentencias(self, stop_tokens: tuple[str, ...] = ()) -> Optional[ListaSentencias]:
        """lista_sentencias → lista_sentencias sentencia | ε"""
        lista = ListaSentencias()

        while (self.current_token and
               self.current_token.tipo not in stop_tokens and
               self.current_token.tipo in ("IDENTIFIER", "KW_IF", "KW_WHILE", 
                                                                   "KW_DO", "KW_CIN", "KW_COUT")):
            sent = self._sentencia()
            if sent:
                lista.sentencias.append(sent)
                lista.children.append(sent)
            else:
                break

        return lista if lista.sentencias else None

    def _sentencia(self) -> Optional[Sentencia]:
        """sentencia → seleccion | iteracion | repeticion | sent_in | sent_out | asignacion"""
        sent = Sentencia()

        if not self.current_token:
            return None

        if self.current_token.tipo == "KW_IF":
            contenido = self._seleccion()
        elif self.current_token.tipo == "KW_WHILE":
            contenido = self._iteracion()
        elif self.current_token.tipo == "KW_DO":
            contenido = self._repeticion()
        elif self.current_token.tipo == "KW_CIN":
            contenido = self._sent_in()
        elif self.current_token.tipo == "KW_COUT":
            contenido = self._sent_out()
        elif self.current_token.tipo == "IDENTIFIER":
            contenido = self._asignacion()
        else:
            return None

        if contenido:
            sent.contenido = contenido
            sent.children = [contenido]

        return sent

    def _asignacion(self) -> Optional[Asignacion]:
        """asignacion → id = sent_expresion"""
        asig = Asignacion()

        if not self._match("IDENTIFIER"):
            self.errors.append(SyntaxError("Se esperaba identificador en asignación"))
            return None

        asig.identificador = self.current_token.valor
        self._advance()

        if not self._consume("ASIGNACION", "Se esperaba '=' en asignación"):
            self._skip_on_error("PUNTO_COMA")
            return asig

        # sent_expresion → expresion ; | ;
        if self._match("PUNTO_COMA"):
            # asignación vacía
            self._advance()
        else:
            asig.expresion = self._expresion()
            self._consume("PUNTO_COMA", "Se esperaba ';' al final de asignación")

        if asig.expresion:
            asig.children = [asig.expresion]

        return asig

    def _seleccion(self) -> Optional[Seleccion]:
        """seleccion → if expresion then lista_sentencias [ else lista_sentencias ] end"""
        sel = Seleccion()

        if not self._consume("KW_IF", "Se esperaba 'if'"):
            return None

        sel.condicion = self._expresion()

        if not self._consume("KW_THEN", "Se esperaba 'then' después de condición"):
            self._skip_on_error("KW_ELSE", "KW_END")

        sel.rama_entonces = self._lista_sentencias()

        if self._match("KW_ELSE"):
            self._advance()
            sel.rama_sino = self._lista_sentencias()

        if not self._consume("KW_END", "Se esperaba 'end' para cerrar if"):
            self._skip_on_error("KW_END")

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
        """iteracion → while expresion lista_sentencias end"""
        iter_node = Iteracion()

        if not self._consume("KW_WHILE", "Se esperaba 'while'"):
            return None

        iter_node.condicion = self._expresion()

        iter_node.cuerpo = self._lista_sentencias()

        if not self._consume("KW_END", "Se esperaba 'end' para cerrar while"):
            self._skip_on_error("KW_END")

        children = []
        if iter_node.condicion:
            children.append(iter_node.condicion)
        if iter_node.cuerpo:
            children.extend(iter_node.cuerpo.children)
        iter_node.children = children

        return iter_node

    def _repeticion(self) -> Optional[Repeticion]:
        """repeticion → do lista_sentencias while expresion"""
        rep = Repeticion()

        if not self._consume("KW_DO", "Se esperaba 'do'"):
            return None

        rep.cuerpo = self._lista_sentencias(stop_tokens=("KW_WHILE",))

        if not self._consume("KW_WHILE", "Se esperaba 'while' después del cuerpo do"):
            self._skip_on_error("PUNTO_COMA")
            return rep

        rep.condicion = self._expresion()

        self._consume("PUNTO_COMA", "Se esperaba ';' después de do-while")

        children = []
        if rep.cuerpo:
            children.extend(rep.cuerpo.children)
        if rep.condicion:
            children.append(rep.condicion)
        rep.children = children

        return rep

    def _sent_in(self) -> Optional[EntradaEstandar]:
        """sent_in → cin >> id ;"""
        entrada = EntradaEstandar()

        if not self._consume("KW_CIN", "Se esperaba 'cin'"):
            return None

        if not self._match("MAYOR"):  # >> se interpreta como dos MAYOR
            # Intenta interpretar >> directamente si el lexer lo soporta
            self._skip_on_error("IDENTIFIER")

        if self._match("MAYOR"):  # Primer >
            self._advance()
            if self._match("MAYOR"):  # Segundo >
                self._advance()

        if not self._match("IDENTIFIER"):
            self.errors.append(SyntaxError("Se esperaba identificador después de cin >>"))
            return entrada

        entrada.identificador = self.current_token.valor
        self._advance()

        if not self._consume("PUNTO_COMA", "Se esperaba ';' después de cin"):
            self._skip_on_error("PUNTO_COMA")

        return entrada

    def _sent_out(self) -> Optional[SalidaEstandar]:
        """sent_out → cout << salida"""
        salida = SalidaEstandar()

        if not self._consume("KW_COUT", "Se esperaba 'cout'"):
            return None

        # >> se interpreta como dos MENOR
        if self._match("MENOR"):
            self._advance()
            if self._match("MENOR"):
                self._advance()

        salida_item = self._salida()
        if salida_item:
            salida.salidas.append(salida_item)
            salida.children = [salida_item]

        self._consume("PUNTO_COMA", "Se esperaba ';' después de cout")

        return salida

    def _salida(self) -> Optional[Salida]:
        """salida → cadena | expresion | cadena << expresion | expresion << cadena"""
        salida = Salida()

        # Intenta cadena primero
        if self._match("STRING"):
            cadena = Cadena(valor=self.current_token.valor)
            salida.elementos.append(cadena)
            self._advance()

            # Verifica si hay más con <<
            if self._match("MENOR"):
                self._advance()
                if self._match("MENOR"):
                    self._advance()
                    expr = self._expresion()
                    if expr:
                        salida.elementos.append(expr)
        else:
            # Intenta expresión
            expr = self._expresion()
            if expr:
                salida.elementos.append(expr)

                # Verifica si hay más con <<
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

        expr.izquierda = self._expresion_simple()

        if self.current_token and self.current_token.tipo in ("MAYOR", "MENOR", "MAYOR_IGUAL", 
                                                               "MENOR_IGUAL", "IGUAL", "DIFERENTE"):
            expr.operador = self.current_token.valor
            self._advance()
            expr.derecha = self._expresion_simple()

        if expr.izquierda:
            expr.children = [expr.izquierda]
            if expr.derecha:
                expr.children.append(expr.derecha)

        return expr if expr.izquierda else None

    def _expresion_simple(self) -> Optional[ExpresionSimple]:
        """expresion_simple → expresion_simple suma_op termino | termino"""
        exp_simple = ExpresionSimple()

        termino = self._termino()
        if not termino:
            return None

        exp_simple.terminos.append(termino)

        while self.current_token and self.current_token.tipo in ("SUMA", "RESTA", "INCREMENTO", "DECREMENTO"):
            exp_simple.operadores.append(self.current_token.valor)
            self._advance()
            siguiente_termino = self._termino()
            if siguiente_termino:
                exp_simple.terminos.append(siguiente_termino)
            else:
                break

        exp_simple.children = exp_simple.terminos
        return exp_simple

    def _termino(self) -> Optional[Termino]:
        """termino → termino mult_op factor | factor"""
        termino = Termino()

        factor = self._factor()
        if not factor:
            return None

        termino.factores.append(factor)

        while self.current_token and self.current_token.tipo in ("MULTIPLICACION", "DIVISION", "MODULO"):
            termino.operadores.append(self.current_token.valor)
            self._advance()
            siguiente_factor = self._factor()
            if siguiente_factor:
                termino.factores.append(siguiente_factor)
            else:
                break

        termino.children = termino.factores
        return termino

    def _factor(self) -> Optional[Factor]:
        """factor → factor pot_op componente | componente"""
        factor = Factor()

        componente = self._componente()
        if not componente:
            return None

        factor.componentes.append(componente)

        while self._match("POTENCIA"):
            factor.operadores.append(self.current_token.valor)
            self._advance()
            siguiente_comp = self._componente()
            if siguiente_comp:
                factor.componentes.append(siguiente_comp)
            else:
                break

        factor.children = factor.componentes
        return factor

    def _componente(self) -> Optional[Componente]:
        """componente → ( expresion ) | número | id | bool | op_logico componente"""
        comp = Componente()

        if self._match("PAR_IZQ"):
            # ( expresion )
            self._advance()
            comp.tipo = "expresion"
            comp.expresion = self._expresion()
            if not self._consume("PAR_DER", "Se esperaba ')'"):
                self._skip_on_error("PAR_DER")
            comp.children = [comp.expresion] if comp.expresion else []

        elif self._match("INT_NUM", "FLOAT_NUM"):
            # número
            try:
                comp.tipo = "numero"
                comp.valor = float(self.current_token.valor)
                comp.children = [Numero(valor=comp.valor)]
            except ValueError:
                comp.valor = 0
            self._advance()

        elif self._match("IDENTIFIER"):
            # id
            comp.tipo = "identificador"
            comp.valor = self.current_token.valor
            comp.children = [Identificador(nombre=comp.valor)]
            self._advance()

        elif self._match("KW_REAL"):  # Booleano (REAL podría ser true/false en el lexer)
            # bool o palabras de booleano
            comp.tipo = "booleano"
            comp.valor = self.current_token.valor.lower() in ("true", "verdadero", "1")
            comp.children = [Booleano(valor=comp.valor)]
            self._advance()

        elif self._match("AND", "OR", "NEGACION"):
            # op_logico componente
            comp.tipo = "logico"
            comp.operador_logico = self.current_token.valor
            self._advance()
            comp.siguiente = self._componente()
            if comp.siguiente:
                comp.children = [comp.siguiente]

        else:
            if self.current_token:
                self.errors.append(SyntaxError(
                    f"Se esperaba componente pero se encontró {self.current_token.tipo}",
                    linea=self.current_token.linea
                ))
            return None

        return comp

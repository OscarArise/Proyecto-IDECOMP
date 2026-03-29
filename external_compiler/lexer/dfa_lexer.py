"""
dfa_lexer.py
------------
Implementación del Autómata Finito Determinista (DFA) para el analizador
léxico del lenguaje CAOS.

El DFA está construido directamente desde el autómata definido en:
    ide/Autonoma para analisis lexico/automata.md

Estados implementados en esta versión:
    - INICIO                 → estado inicial / loop de espacios en blanco
    - NUMEROS_ENTEROS        → reconoce dígitos consecutivos
    - NUMERO_FLOTANTE        → reconoce el punto decimal (estado de paso)
    - REAL                   → reconoce la parte decimal del flotante
    - IDENTIFICADORES        → reconoce nombres; clasifica palabras reservadas
    - PLUS_STATE             → distingue + de ++
    - MIN_STATE              → distingue - de --
    - AND_STATE              → reconoce &&
    - OR_STATE               → reconoce ||
    - OP_RELACIONAL          → reconoce > < ! = y sus formas dobles >= <= != ==
    - HECHO                  → estado de aceptación (token emitido)
    - ERROR_STATE            → carácter inválido; el DFA continúa

Estados fuera de alcance en esta versión (pendientes de implementación):
    - COMENTARIOS / COMENTARIOS_LINEA / COMENTARIOS_BLOQUE / Q3
      TODO: aquí se agregarán los estados para comentarios //  y /* */
    - CADENA (string "...")
      TODO: aquí se agregarán los estados para cadenas de texto "..."
    - Q1 / Q2  (char '...')
      TODO: aquí se agregarán los estados para caracteres literales '...'
    - Reporte de errores a errors.txt con línea y columna
      TODO: aquí se integrará el reporte de errores léxicos a errors.txt
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .reserved_words import RESERVED
from .token_types import TokenType


# ---------------------------------------------------------------------------
# Estructura de Token
# ---------------------------------------------------------------------------

@dataclass
class Token:
    """Unidad mínima de información léxica producida por el DFA."""
    tipo:    str   # Nombre del TokenType, ej. "INT_NUM", "KW_IF", "PLUS"
    valor:   str   # Lexema tal como aparece en el código fuente
    linea:   int   # Línea (1-indexed)
    columna: int   # Columna del primer carácter del lexema (1-indexed)

    def __repr__(self) -> str:
        return f"Token({self.tipo!r}, {self.valor!r}, L{self.linea}:C{self.columna})"


# ---------------------------------------------------------------------------
# Constantes de estado del DFA
# ---------------------------------------------------------------------------

_INICIO           = "INICIO"
_NUMEROS_ENTEROS  = "NUMEROS_ENTEROS"
_NUMERO_FLOTANTE  = "NUMERO_FLOTANTE"
_REAL             = "REAL"
_IDENTIFICADORES  = "IDENTIFICADORES"
_PLUS_STATE       = "PLUS_STATE"
_MIN_STATE        = "MIN_STATE"
_AND_STATE        = "AND_STATE"
_OR_STATE         = "OR_STATE"
_OP_RELACIONAL    = "OP_RELACIONAL"
_HECHO            = "HECHO"
_ERROR_STATE      = "ERROR_STATE"

# Mapa de símbolos directos: carácter → nombre de tipo de token
_DIRECT_SYMBOLS: dict[str, str] = {
    "(": "PAR_IZQ",
    ")": "PAR_DER",
    "{": "LLAVE_IZQ",
    "}": "LLAVE_DER",
    ",": "COMA",
    ";": "PUNTO_COMA",
    "*": "MULTIPLICACION",
    "%": "MODULO",
    "^": "POTENCIA",
}

# Mapa de operadores relacionales simples: carácter → nombre de tipo de token
_RELACIONAL_SIMPLE: dict[str, str] = {
    ">": "MAYOR",
    "<": "MENOR",
    "!": "NEGACION",
    "=": "ASIGNACION",
}

# Mapa de operadores relacionales dobles: dos caracteres → nombre de tipo de token
_RELACIONAL_DOBLE: dict[str, str] = {
    ">=": "MAYOR_IGUAL",
    "<=": "MENOR_IGUAL",
    "!=": "DIFERENTE",
    "==": "IGUAL",
}


# ---------------------------------------------------------------------------
# DFALexer
# ---------------------------------------------------------------------------

class DFALexer:
    """
    Analizador léxico basado en DFA para el lenguaje CAOS.

    Uso:
        lexer = DFALexer()
        tokens, errors = lexer.tokenize(source_code)

    Parámetros de tokenize:
        source_code (str): El código fuente completo como cadena.

    Retorna:
        tokens (list[Token]) : Lista de tokens reconocidos.
        errors (list[str])   : Lista de mensajes de error léxico encontrados.
                               El DFA continúa aunque encuentre errores.
    """

    def tokenize(self, source: str) -> tuple[list[Token], list[str]]:
        """
        Recorre `source` carácter a carácter implementando el DFA.
        Retorna (lista_de_tokens, lista_de_errores).
        """
        tokens: list[Token] = []
        errors: list[str]   = []

        pos     = 0            # posición actual en source
        linea   = 1            # línea actual (1-indexed)
        columna = 1            # columna actual (1-indexed)

        n = len(source)

        while pos < n:
            state = _INICIO

            # ------------------------------------------------------------------
            # Estado: INICIO
            # Consume espacios en blanco y determina el tipo de token a leer.
            # ------------------------------------------------------------------
            ch = source[pos]

            # Ignorar espacios en blanco (self-loop INICIO)
            if ch in (" ", "\t", "\r"):
                pos += 1
                columna += 1
                continue

            # Salto de línea — reiniciar columna
            if ch == "\n":
                pos += 1
                linea += 1
                columna = 1
                continue

            # ------------------------------------------------------------------
            # Rama: NÚMEROS ENTEROS y REALES
            # INICIO --[0-9]--> NUMEROS_ENTEROS
            # ------------------------------------------------------------------
            if ch.isdigit():
                tok, pos, columna, linea = self._read_number(
                    source, pos, linea, columna
                )
                tokens.append(tok)
                continue

            # ------------------------------------------------------------------
            # Rama: IDENTIFICADORES y PALABRAS RESERVADAS
            # INICIO --[a-zA-Z_]--> IDENTIFICADORES
            # ------------------------------------------------------------------
            if ch.isalpha() or ch == "_":
                tok, pos, columna, linea = self._read_identifier(
                    source, pos, linea, columna
                )
                tokens.append(tok)
                continue

            # ------------------------------------------------------------------
            # Rama: OPERADORES RELACIONALES
            # INICIO --[> < ! =]--> OP_RELACIONAL
            # ------------------------------------------------------------------
            if ch in (">", "<", "!", "="):
                tok, pos, columna = self._read_relacional(
                    source, pos, linea, columna
                )
                tokens.append(tok)
                continue

            # ------------------------------------------------------------------
            # Rama: PLUS / INCREMENT
            # INICIO --[+]--> PLUS_STATE
            # ------------------------------------------------------------------
            if ch == "+":
                tok, pos, columna = self._read_plus(source, pos, linea, columna)
                tokens.append(tok)
                continue

            # ------------------------------------------------------------------
            # Rama: MINUS / DECREMENT
            # INICIO --[-]--> MIN_STATE
            # ------------------------------------------------------------------
            if ch == "-":
                tok, pos, columna = self._read_minus(source, pos, linea, columna)
                tokens.append(tok)
                continue

            # ------------------------------------------------------------------
            # Rama: AND lógico
            # INICIO --[&]--> AND_STATE --[&]--> HECHO  (&&)
            # Si no viene otro & → ERROR (& solo no es válido en CAOS)
            # ------------------------------------------------------------------
            if ch == "&":
                tok, pos, columna = self._read_and(source, pos, linea, columna)
                if tok is not None:
                    tokens.append(tok)
                else:
                    # & solo — carácter inválido
                    err_msg = (
                        f"[LEXICO] Carácter inválido '&' en línea {linea}, "
                        f"columna {columna} — se esperaba '&&'"
                    )
                    errors.append(err_msg)
                    tok_err = Token("ERROR", "&", linea, columna)
                    tokens.append(tok_err)
                    pos += 1
                    columna += 1
                continue

            # ------------------------------------------------------------------
            # Rama: OR lógico
            # INICIO --[|]--> OR_STATE --[|]--> HECHO  (||)
            # Si no viene otro | → ERROR (| solo no es válido en CAOS)
            # ------------------------------------------------------------------
            if ch == "|":
                tok, pos, columna = self._read_or(source, pos, linea, columna)
                if tok is not None:
                    tokens.append(tok)
                else:
                    err_msg = (
                        f"[LEXICO] Carácter inválido '|' en línea {linea}, "
                        f"columna {columna} — se esperaba '||'"
                    )
                    errors.append(err_msg)
                    tok_err = Token("ERROR", "|", linea, columna)
                    tokens.append(tok_err)
                    pos += 1
                    columna += 1
                continue

            # ------------------------------------------------------------------
            # Rama: DIVIDE o inicio de COMENTARIO
            # INICIO --[/]--> COMENTARIOS
            #   → si sigue /  → COMENTARIOS_LINEA  (ignorar hasta \n)
            #   → si sigue *  → COMENTARIOS_BLOQUE (ignorar hasta */)
            #   → si sigue [Otro] → HECHO: token DIVIDE
            #
            # TODO: aquí se implementarán los estados COMENTARIOS_LINEA,
            #       COMENTARIOS_BLOQUE y Q3 para comentarios // y /* */
            # Por ahora solo se reconoce el operador DIVIDE simple.
            # ------------------------------------------------------------------
            if ch == "/":
                tok, pos, columna, linea = self._read_divide_or_comment(
                    source, pos, linea, columna
                )
                if tok is not None:
                    tokens.append(tok)
                # Si tok es None significa que el comentario fue ignorado
                continue

            # ------------------------------------------------------------------
            # Rama: CADENA de texto  "..."
            # TODO: aquí se implementará el estado CADENA para "..."
            #       INICIO --["]--> CADENA --[texto]--> CADENA --["]--> HECHO
            # ------------------------------------------------------------------
            if ch == '"':
                tok, pos, columna, linea = self._read_string(
                    source, pos, linea, columna
                )
                if tok.tipo == "ERROR":
                    errors.append(
                        f"[LEXICO] Cadena sin cerrar en línea {tok.linea}, "
                        f"columna {tok.columna}"
                    )
                tokens.append(tok)
                continue

            # ------------------------------------------------------------------
            # Rama: CHAR literal  '...'
            # TODO: aquí se implementarán los estados Q1 y Q2 para '...'
            #       INICIO --[']--> Q1 --[c]--> Q2 --[']--> HECHO
            # ------------------------------------------------------------------
            if ch == "'":
                tok, pos, columna, linea = self._read_char(
                    source, pos, linea, columna
                )
                if tok.tipo == "ERROR":
                    errors.append(
                        f"[LEXICO] Carácter literal inválido en línea {tok.linea}, "
                        f"columna {tok.columna}"
                    )
                tokens.append(tok)
                continue

            # ------------------------------------------------------------------
            # Rama: SÍMBOLOS DIRECTOS
            # INICIO --[ ( ) { } , ; * % ^ ]--> HECHO
            # Cada uno se reconoce como un token de un solo carácter.
            # ------------------------------------------------------------------
            if ch in _DIRECT_SYMBOLS:
                tipo = _DIRECT_SYMBOLS[ch]
                tokens.append(Token(tipo, ch, linea, columna))
                pos += 1
                columna += 1
                continue

            # ------------------------------------------------------------------
            # Fallback: ERROR LÉXICO
            # El carácter no pertenece a ninguna transición válida desde INICIO.
            # El DFA continúa con el siguiente carácter (modo recuperación).
            # ------------------------------------------------------------------
            # TODO: cuando se implemente el reporte completo a errors.txt,
            #       los mensajes de error se escribirán aquí con línea y columna.
            err_msg = (
                f"[LEXICO] Carácter inválido {ch!r} en línea {linea}, "
                f"columna {columna}"
            )
            errors.append(err_msg)
            tokens.append(Token("ERROR", ch, linea, columna))
            pos += 1
            columna += 1

        # Token de fin de archivo
        tokens.append(Token("EOF", "", linea, columna))
        return tokens, errors

    # ==========================================================================
    # Métodos auxiliares — cada uno implementa una "rama" del DFA
    # ==========================================================================

    def _read_number(
        self, source: str, pos: int, linea: int, columna: int
    ) -> tuple[Token, int, int, int]:
        """
        Estado: NUMEROS_ENTEROS → NUMERO_FLOTANTE → REAL
        Lee un número entero o flotante y retorna (Token, nueva_pos, nueva_col, nueva_linea).

        Transiciones:
            NUMEROS_ENTEROS --[0-9]--> NUMEROS_ENTEROS   (acumular)
            NUMEROS_ENTEROS --[.  ]--> NUMERO_FLOTANTE   (pasar a decimales)
            NUMERO_FLOTANTE --[0-9]--> REAL              (primer dígito decimal)
            REAL            --[0-9]--> REAL              (acumular decimales)
            REAL / ENT      --[Otro]--> HECHO            (retroceder, emitir)
        """
        start_col = columna
        start     = pos
        n         = len(source)
        state     = _NUMEROS_ENTEROS

        while pos < n:
            ch = source[pos]

            if state == _NUMEROS_ENTEROS:
                if ch.isdigit():
                    pos += 1
                    columna += 1
                elif ch == ".":
                    # Verificar que después del punto venga un dígito
                    if pos + 1 < n and source[pos + 1].isdigit():
                        state = _NUMERO_FLOTANTE
                        pos += 1
                        columna += 1
                    else:
                        # Punto sin dígito → es un entero; el punto lo procesará
                        # el siguiente ciclo desde INICIO
                        break
                else:
                    # [Otro] → HECHO, retroceder (no consumir el delimitador)
                    break

            elif state == _NUMERO_FLOTANTE:
                # Debe venir al menos un dígito
                if ch.isdigit():
                    state = _REAL
                    pos += 1
                    columna += 1
                else:
                    # Punto sin decimales → retroceder hasta antes del punto
                    # (se emite como entero y el punto se reprocesa)
                    lexema = source[start:pos]
                    # Quitar el punto que ya se consumió
                    int_lexema = lexema.rstrip(".")
                    pos -= 1          # retroceder el punto
                    columna -= 1
                    return Token("INT_NUM", int_lexema, linea, start_col), pos, columna, linea

            elif state == _REAL:
                if ch.isdigit():
                    pos += 1
                    columna += 1
                else:
                    # [Otro] → HECHO
                    break

        lexema = source[start:pos]
        tipo   = "FLOAT_NUM" if state in (_REAL, _NUMERO_FLOTANTE) else "INT_NUM"
        return Token(tipo, lexema, linea, start_col), pos, columna, linea

    # --------------------------------------------------------------------------

    def _read_identifier(
        self, source: str, pos: int, linea: int, columna: int
    ) -> tuple[Token, int, int, int]:
        """
        Estado: IDENTIFICADORES
        Lee letras, dígitos y guiones bajos. Al terminar, consulta la tabla
        RESERVED para clasificar si es palabra reservada o identificador.

        Transiciones:
            IDENTIFICADORES --[a-zA-Z0-9_]--> IDENTIFICADORES  (acumular)
            IDENTIFICADORES --[Otro]        --> HECHO           (retroceder, emitir)
        """
        start_col = columna
        start     = pos
        n         = len(source)

        while pos < n:
            ch = source[pos]
            if ch.isalnum() or ch == "_":
                pos += 1
                columna += 1
            else:
                break   # [Otro] → HECHO, retroceder

        lexema = source[start:pos]
        tipo   = RESERVED.get(lexema, "IDENTIFIER")
        return Token(tipo, lexema, linea, start_col), pos, columna, linea

    # --------------------------------------------------------------------------

    def _read_relacional(
        self, source: str, pos: int, linea: int, columna: int
    ) -> tuple[Token, int, int]:
        """
        Estado: OP_RELACIONAL
        Reconoce operadores simples (>, <, !, =) y dobles (>=, <=, !=, ==).

        Transiciones:
            OP_RELACIONAL --[=]    --> HECHO  (emitir doble: >=, <=, !=, ==)
            OP_RELACIONAL --[Otro] --> HECHO  (emitir simple: >, <, !, =; retroceder)
        """
        start_col = columna
        primer    = source[pos]
        pos      += 1
        columna  += 1

        n = len(source)
        if pos < n and source[pos] == "=":
            # Forma doble
            doble = primer + "="
            tipo  = _RELACIONAL_DOBLE[doble]
            pos     += 1
            columna += 1
            return Token(tipo, doble, linea, start_col), pos, columna
        else:
            # Forma simple — [Otro] ya no se consume
            tipo = _RELACIONAL_SIMPLE[primer]
            return Token(tipo, primer, linea, start_col), pos, columna

    # --------------------------------------------------------------------------

    def _read_plus(
        self, source: str, pos: int, linea: int, columna: int
    ) -> tuple[Token, int, int]:
        """
        Estado: PLUS_STATE
        Transiciones:
            PLUS_STATE --[+]    --> HECHO  (emitir INCREMENT ++)
            PLUS_STATE --[Otro] --> HECHO  (emitir PLUS +; retroceder)
        """
        start_col = columna
        pos      += 1   # consumir el primer +
        columna  += 1

        n = len(source)
        if pos < n and source[pos] == "+":
            pos     += 1
            columna += 1
            return Token("INCREMENTO", "++", linea, start_col), pos, columna
        else:
            return Token("SUMA", "+", linea, start_col), pos, columna

    # --------------------------------------------------------------------------

    def _read_minus(
        self, source: str, pos: int, linea: int, columna: int
    ) -> tuple[Token, int, int]:
        """
        Estado: MIN_STATE
        Transiciones:
            MIN_STATE --[-]    --> HECHO  (emitir DECREMENT --)
            MIN_STATE --[Otro] --> HECHO  (emitir MINUS -; retroceder)
        """
        start_col = columna
        pos      += 1   # consumir el primer -
        columna  += 1

        n = len(source)
        if pos < n and source[pos] == "-":
            pos     += 1
            columna += 1
            return Token("DECREMENTO", "--", linea, start_col), pos, columna
        else:
            return Token("RESTA", "-", linea, start_col), pos, columna

    # --------------------------------------------------------------------------

    def _read_and(
        self, source: str, pos: int, linea: int, columna: int
    ) -> tuple[Optional[Token], int, int]:
        """
        Estado: AND_STATE
        Transiciones:
            AND_STATE --[&] --> HECHO  (emitir AND &&)
            AND_STATE --[Otro] → None (& sola: caller maneja el error)
        """
        start_col = columna
        pos      += 1   # consumir primer &
        columna  += 1

        n = len(source)
        if pos < n and source[pos] == "&":
            pos     += 1
            columna += 1
            return Token("AND", "&&", linea, start_col), pos, columna
        else:
            # Retroceder — caller emite ERROR
            pos     -= 1
            columna -= 1
            return None, pos, columna

    # --------------------------------------------------------------------------

    def _read_or(
        self, source: str, pos: int, linea: int, columna: int
    ) -> tuple[Optional[Token], int, int]:
        """
        Estado: OR_STATE
        Transiciones:
            OR_STATE --[|] --> HECHO  (emitir OR ||)
            OR_STATE --[Otro] → None (| sola: caller maneja el error)
        """
        start_col = columna
        pos      += 1   # consumir primer |
        columna  += 1

        n = len(source)
        if pos < n and source[pos] == "|":
            pos     += 1
            columna += 1
            return Token("OR", "||", linea, start_col), pos, columna
        else:
            # Retroceder — caller emite ERROR
            pos     -= 1
            columna -= 1
            return None, pos, columna

    # --------------------------------------------------------------------------

    def _read_divide_or_comment(
        self, source: str, pos: int, linea: int, columna: int
    ) -> tuple[Optional[Token], int, int, int]:
        """
        Estado: COMENTARIOS
        Si el / va seguido de otro / o de * → comentario (ignorado, retorna None).
        De lo contrario → token DIVIDE.

        Transiciones:
            COMENTARIOS_LINEA:  INICIO --[/]--> COMENTARIOS --[/]--> loop hasta \\n --> INICIO
            COMENTARIOS_BLOQUE: INICIO --[/]--> COMENTARIOS --[*]--> loop --> Q3 --[/]--> INICIO
            Q3: manejo de asteriscos múltiples dentro del bloque

        Retorna (Token|None, nueva_pos, nueva_col, nueva_linea).
        Si el comentario de bloque no se cierra antes del EOF, se consume
        todo el resto del archivo y se retorna None (nada se tokeniza).
        """
        start_col = columna
        pos      += 1   # consumir /
        columna  += 1

        n = len(source)

        if pos < n and source[pos] == "/":
            # Comentario de línea — consumir hasta \n (sin incluir el \n)
            pos     += 1
            columna += 1
            while pos < n and source[pos] != "\n":
                pos     += 1
                columna += 1
            return None, pos, columna, linea   # comentario ignorado

        if pos < n and source[pos] == "*":
            # Comentario de bloque — consumir hasta */ o hasta EOF
            pos     += 1
            columna += 1
            closed = False
            while pos < n:
                if source[pos] == "*" and pos + 1 < n and source[pos + 1] == "/":
                    # Cierre encontrado
                    pos     += 2
                    columna += 2
                    closed = True
                    break
                if source[pos] == "\n":
                    linea  += 1
                    columna = 1
                else:
                    columna += 1
                pos += 1
            # Si closed es False, llegamos al EOF sin cerrar → todo consumido
            return None, pos, columna, linea   # comentario ignorado

        # [Otro] → token DIVISION simple
        return Token("DIVISION", "/", linea, start_col), pos, columna, linea
# --------------------------------------------------------------------------

    def _read_string(
        self, source: str, pos: int, linea: int, columna: int
    ) -> tuple[Token, int, int, int]:
        start_col = columna
        start     = pos
        n         = len(source)

        pos     += 1
        columna += 1

        while pos < n:
            ch = source[pos]

            if ch == '"':
                pos     += 1
                columna += 1
                lexema = source[start:pos]
                return Token("STRING", lexema, linea, start_col), pos, columna, linea

            if ch == '\n':
                lexema = source[start:pos]
                return Token("ERROR", lexema, linea, start_col), pos, columna, linea

            pos     += 1
            columna += 1

        lexema = source[start:pos]
        return Token("ERROR", lexema, linea, start_col), pos, columna, linea

    # --------------------------------------------------------------------------

    def _read_char(
        self, source: str, pos: int, linea: int, columna: int
    ) -> tuple[Token, int, int, int]:
        start_col = columna
        start     = pos
        n         = len(source)

        pos     += 1
        columna += 1

        if pos >= n:
            return Token("ERROR", source[start:pos], linea, start_col), pos, columna, linea

        contenido = source[pos]

        if contenido == "'":
            pos     += 1
            columna += 1
            return Token("ERROR", source[start:pos], linea, start_col), pos, columna, linea

        if contenido == '\n':
            return Token("ERROR", source[start:pos], linea, start_col), pos, columna, linea

        pos     += 1
        columna += 1

        if pos >= n:
            return Token("ERROR", source[start:pos], linea, start_col), pos, columna, linea

        siguiente = source[pos]

        if siguiente == "'":
            pos     += 1
            columna += 1
            lexema = source[start:pos]
            return Token("CHAR", lexema, linea, start_col), pos, columna, linea

        while pos < n and source[pos] != "'" and source[pos] != '\n':
            pos     += 1
            columna += 1
        if pos < n and source[pos] == "'":
            pos     += 1
            columna += 1
        lexema = source[start:pos]
        return Token("ERROR", lexema, linea, start_col), pos, columna, linea
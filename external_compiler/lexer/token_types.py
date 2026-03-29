"""
token_types.py
--------------
Define la enumeración de todos los tipos de tokens que el DFA puede producir.
Cada miembro representa una categoría semántica del lenguaje CAOS.
"""

from enum import Enum, auto


class TokenType(Enum):
    # ------------------------------------------------------------------
    # Literales numéricos
    # ------------------------------------------------------------------
    INT_NUM   = auto()   # Número entero:   123, 0, 99
    FLOAT_NUM = auto()   # Número flotante:  3.14, 0.5

    # ------------------------------------------------------------------
    # Identificadores y palabras reservadas
    # ------------------------------------------------------------------
    IDENTIFIER = auto()  # Nombre de variable/función definido por el usuario
    RESERVED   = auto()  # Palabra reservada del lenguaje (ver reserved_words.py)
    #   Palabras reservadas con su propio subtipo:
    KW_IF      = auto()
    KW_ELSE    = auto()
    KW_END     = auto()
    KW_DO      = auto()
    KW_WHILE   = auto()
    KW_SWITCH  = auto()
    KW_CASE    = auto()
    KW_INT     = auto()
    KW_FLOAT   = auto()
    KW_MAIN    = auto()
    KW_CIN     = auto()
    KW_COUT    = auto()
    KW_FOR     = auto()
    KW_RETURN  = auto()
    KW_BREAK   = auto()
    KW_DEFAULT = auto()

    # ------------------------------------------------------------------
    # Operadores aritméticos
    # ------------------------------------------------------------------
    SUMA         = auto()   # +
    INCREMENTO   = auto()   # ++
    RESTA        = auto()   # -
    DECREMENTO   = auto()   # --
    MULTIPLICACION = auto() # *
    DIVISION     = auto()   # /
    MODULO       = auto()   # %
    POTENCIA     = auto()   # ^

    # ------------------------------------------------------------------
    # Operadores lógicos
    # ------------------------------------------------------------------
    AND = auto()   # &&
    OR  = auto()   # ||

    # ------------------------------------------------------------------
    # Operadores relacionales y de asignación
    # ------------------------------------------------------------------
    MAYOR       = auto()  # >
    MENOR       = auto()  # <
    NEGACION    = auto()  # !
    ASIGNACION  = auto()  # =
    MAYOR_IGUAL = auto()  # >=
    MENOR_IGUAL = auto()  # <=
    DIFERENTE   = auto()  # !=
    IGUAL       = auto()  # ==

    # ------------------------------------------------------------------
    # Delimitadores / símbolos directos
    # ------------------------------------------------------------------
    PAR_IZQ    = auto()  # (
    PAR_DER    = auto()  # )
    LLAVE_IZQ  = auto()  # {
    LLAVE_DER  = auto()  # }
    COMA       = auto()  # ,
    PUNTO_COMA = auto()  # ;

    # ------------------------------------------------------------------
    # Tokens reservados para implementación futura
    # ------------------------------------------------------------------
    # TODO: aquí se agregarán los tipos STRING y CHAR
    #   STRING = auto()   # "cadena de texto"
    #   CHAR   = auto()   # 'c'

    # TODO: aquí se agregarán los tipos de tokens para comentarios
    #   COMMENT_LINE  = auto()   # // comentario de línea
    #   COMMENT_BLOCK = auto()   # /* comentario de bloque */

    # ------------------------------------------------------------------
    # Tokens especiales
    # ------------------------------------------------------------------
    ERROR = auto()  # Carácter o secuencia no reconocida por el DFA
    EOF   = auto()  # Fin del flujo de entrada

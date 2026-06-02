"""
ast_nodes.py
-----------
Define las clases para representar los nodos del Árbol Sintáctico Abstracto (AST)
para el lenguaje CAOS.

Estructura jerárquica de nodos basada en la gramática de la Fase 2.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any


# Clase base para todos los nodos del AST
@dataclass
class ASTNode:
    """Nodo base del árbol sintáctico."""
    linea: int = 0
    columna: int = 0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"


# ============================================================================
# Nodos raíz
# ============================================================================

@dataclass
class Programa(ASTNode):
    """Nodo raíz: main { lista_declaracion }"""
    lista_declaracion: Optional['ListaDeclaracion'] = None
    children: List[ASTNode] = field(default_factory=list)


# ============================================================================
# Declaraciones
# ============================================================================

@dataclass
class ListaDeclaracion(ASTNode):
    """lista_declaracion → lista_declaracion declaracion | declaracion"""
    declaraciones: List['Declaracion'] = field(default_factory=list)
    children: List[ASTNode] = field(default_factory=list)


@dataclass
class Declaracion(ASTNode):
    """declaracion → declaracion_variable | lista_sentencias"""
    contenido: Optional[ASTNode] = None  # DeclaracionVariable o ListaSentencias
    children: List[ASTNode] = field(default_factory=list)


@dataclass
class DeclaracionVariable(ASTNode):
    """declaracion_variable → tipo identificador ;"""
    tipo: str = ""  # "int" | "float" | "bool"
    identificadores: List[str] = field(default_factory=list)
    children: List[ASTNode] = field(default_factory=list)


# ============================================================================
# Sentencias
# ============================================================================

@dataclass
class ListaSentencias(ASTNode):
    """lista_sentencias → lista_sentencias sentencia | ε"""
    sentencias: List['Sentencia'] = field(default_factory=list)
    children: List[ASTNode] = field(default_factory=list)


@dataclass
class Sentencia(ASTNode):
    """sentencia → seleccion | iteracion | repeticion | sent_in | sent_out | asignacion"""
    contenido: Optional[ASTNode] = None
    children: List[ASTNode] = field(default_factory=list)


@dataclass
class Asignacion(ASTNode):
    """asignacion → id = sent_expresion"""
    identificador: str = ""
    expresion: Optional['Expresion'] = None
    children: List[ASTNode] = field(default_factory=list)


@dataclass
class Seleccion(ASTNode):
    """seleccion → if expresion then lista_sentencias [ else lista_sentencias ] end"""
    condicion: Optional['Expresion'] = None
    rama_entonces: Optional['ListaSentencias'] = None
    rama_sino: Optional['ListaSentencias'] = None
    children: List[ASTNode] = field(default_factory=list)


@dataclass
class Iteracion(ASTNode):
    """iteracion → while expresion lista_sentencias end"""
    condicion: Optional['Expresion'] = None
    cuerpo: Optional['ListaSentencias'] = None
    children: List[ASTNode] = field(default_factory=list)


@dataclass
class Repeticion(ASTNode):
    """repeticion → do lista_sentencias while expresion"""
    cuerpo: Optional['ListaSentencias'] = None
    condicion: Optional['Expresion'] = None
    children: List[ASTNode] = field(default_factory=list)


@dataclass
class EntradaEstandar(ASTNode):
    """sent_in → cin >> id ;"""
    identificador: str = ""
    children: List[ASTNode] = field(default_factory=list)


@dataclass
class SalidaEstandar(ASTNode):
    """sent_out → cout << salida"""
    salidas: List['Salida'] = field(default_factory=list)
    children: List[ASTNode] = field(default_factory=list)


@dataclass
class Salida(ASTNode):
    """salida → cadena | expresion | cadena << expresion | expresion << cadena"""
    elementos: List[ASTNode] = field(default_factory=list)  # Cadenas o Expresiones
    children: List[ASTNode] = field(default_factory=list)


# ============================================================================
# Expresiones
# ============================================================================

@dataclass
class Expresion(ASTNode):
    """expresion → expresion_simple [ rel_op expresion_simple ]"""
    izquierda: Optional['ExpresionSimple'] = None
    operador: Optional[str] = None  # rel_op: <, <=, >, >=, ==, !=
    derecha: Optional['ExpresionSimple'] = None
    children: List[ASTNode] = field(default_factory=list)


@dataclass
class ExpresionSimple(ASTNode):
    """expresion_simple → expresion_simple suma_op termino | termino"""
    terminos: List['Termino'] = field(default_factory=list)
    operadores: List[str] = field(default_factory=list)  # +, -, ++, --
    children: List[ASTNode] = field(default_factory=list)


@dataclass
class Termino(ASTNode):
    """termino → termino mult_op factor | factor"""
    factores: List['Factor'] = field(default_factory=list)
    operadores: List[str] = field(default_factory=list)  # *, /, %
    children: List[ASTNode] = field(default_factory=list)


@dataclass
class Factor(ASTNode):
    """factor → factor pot_op componente | componente"""
    componentes: List['Componente'] = field(default_factory=list)
    operadores: List[str] = field(default_factory=list)  # ^
    children: List[ASTNode] = field(default_factory=list)


@dataclass
class Componente(ASTNode):
    """componente → ( expresion ) | número | id | bool | op_logico componente"""
    tipo: str = ""  # "expresion", "numero", "identificador", "booleano", "logico"
    valor: Any = None
    expresion: Optional['Expresion'] = None
    operador_logico: Optional[str] = None  # &&, ||, !
    siguiente: Optional['Componente'] = None
    children: List[ASTNode] = field(default_factory=list)


# ============================================================================
# Literales
# ============================================================================

@dataclass
class Numero(ASTNode):
    """Literal numérico: número entero o flotante"""
    valor: float = 0.0
    children: List[ASTNode] = field(default_factory=list)


@dataclass
class Identificador(ASTNode):
    """Nombre de variable o función"""
    nombre: str = ""
    children: List[ASTNode] = field(default_factory=list)


@dataclass
class Cadena(ASTNode):
    """Literal de cadena de texto"""
    valor: str = ""
    children: List[ASTNode] = field(default_factory=list)


@dataclass
class Booleano(ASTNode):
    """Literal booleano: true | false"""
    valor: bool = False
    children: List[ASTNode] = field(default_factory=list)


# ============================================================================
# Nodo de Error (para recuperación de errores)
# ============================================================================

@dataclass
class NodoError(ASTNode):
    """Nodo que representa un error sintáctico durante el parsing"""
    mensaje: str = ""
    token_encontrado: Optional[tuple] = None
    token_esperado: Optional[str] = None
    children: List[ASTNode] = field(default_factory=list)

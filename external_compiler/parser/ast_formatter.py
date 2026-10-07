"""
ast_formatter.py
----------------
Proporciona funciones para formatear y serializar el AST para visualización.
"""

from typing import Optional, List, Dict, Any
from .ast_nodes import (
    ASTNode, Programa, ListaDeclaracion, Declaracion, DeclaracionVariable,
    ListaSentencias, Sentencia, Asignacion, IncrementoDecremento,
    Seleccion, Iteracion, Repeticion,
    EntradaEstandar, SalidaEstandar, Salida,
    Expresion, ExpresionSimple, Termino, Factor, Componente,
    Numero, Identificador, Cadena, Booleano, NodoError
)


class ASTFormatter:
    """Formatea y serializa nodos AST para visualización."""

    @staticmethod
    def _dict_to_text(node_dict: Optional[Dict[str, Any]], indent: int = 0) -> str:
        if not node_dict:
            return ""
        prefix = "  " * indent
        label = node_dict.get("label") or node_dict.get("type", "")
        result = f"{prefix}{label} {ASTFormatter._location_text(node_dict)}\n"
        for child in node_dict.get("children", []):
            result += ASTFormatter._dict_to_text(child, indent + 1)
        return result

    @staticmethod
    def to_text(node: Optional[ASTNode], indent: int = 0) -> str:
        """Convierte el AST a una representación de texto indentada."""
        if not node:
            return ""
        return ASTFormatter._dict_to_text(ASTFormatter.to_dict(node), indent)


    # ------------------------------------------------------------------ #
    # Serialización a diccionario (JSON)                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def to_binary(node: Optional[ASTNode]) -> Optional[Dict[str, Any]]:
        """
        Árbol abstracto con las expresiones ya plegadas en forma binaria.

        Es el contrato con el análisis semántico: cada operación aritmética,
        relacional o lógica queda como un nodo con exactamente dos hijos, de modo
        que el recorrido en postorden pueda sintetizar tipos y valores.

        Claves de cada nodo:
            type        nombre de la clase o del rol ("OperacionBinaria", "Literal"…)
            label       etiqueta legible para el visor del IDE
            linea       línea del lexema que origina el nodo
            columna     columna del lexema que origina el nodo
            children    lista de nodos hijos (2 en las operaciones binarias)

        Claves adicionales según el nodo:
            operador        operación binaria o unaria
            nombre          identificador
            valor           literal
            es_entero       literal numérico: True si es int, False si es float
            tipo            declaración: tipo normalizado (int | float | bool)
            tipo_lexema     declaración: lexema escrito ('real' es alias de 'float')
            identificadores declaración: {nombre, linea, columna} por identificador
        """
        if not node:
            return None
        node_dict = ASTFormatter._to_abstract_dict(node)
        ASTFormatter._inherit_missing_locations(node_dict)
        return node_dict

    @staticmethod
    def to_dict(node: Optional[ASTNode]) -> Optional[Dict[str, Any]]:
        """
        Serialización JSON del AST para el visor del IDE.

        Es la misma estructura que entrega `to_binary`; el visor y el análisis
        semántico trabajan sobre un único árbol.
        """
        return ASTFormatter.to_binary(node)


    @staticmethod
    def _abstract_base(node: ASTNode, label: str, node_type: Optional[str] = None) -> Dict[str, Any]:
        return {
            "type": node_type or node.__class__.__name__,
            "linea": node.linea,
            "columna": node.columna,
            "label": label,
            "children": [],
        }

    @staticmethod
    def _location_text(node_dict: Dict[str, Any]) -> str:
        linea = node_dict.get("linea", 0)
        columna = node_dict.get("columna", 0)
        if linea and columna:
            return f"[L{linea}:C{columna}]"
        return "[sin ubicación]"

    @staticmethod
    def _inherit_missing_locations(node_dict: Optional[Dict[str, Any]]) -> tuple[int, int]:
        """Completa ubicaciones sintéticas usando el primer descendiente válido."""
        if not node_dict:
            return (0, 0)

        first_child_location = (0, 0)
        for child in node_dict.get("children", []):
            child_location = ASTFormatter._inherit_missing_locations(child)
            if first_child_location == (0, 0) and all(child_location):
                first_child_location = child_location

        linea = node_dict.get("linea", 0)
        columna = node_dict.get("columna", 0)
        if (not linea or not columna) and all(first_child_location):
            linea, columna = first_child_location
            node_dict["linea"] = linea
            node_dict["columna"] = columna

        return (linea, columna)

    @staticmethod
    def _role(label: str, node: Optional[ASTNode]) -> Optional[Dict[str, Any]]:
        child = ASTFormatter._to_abstract_dict(node) if node else None
        if not child:
            return None
        return {
            "type": "SeccionAST",
            "linea": child.get("linea", 0),
            "columna": child.get("columna", 0),
            "label": label,
            "children": [child],
        }

    @staticmethod
    def _binary_node(operador: str, izquierda: Optional[Dict[str, Any]],
                     derecha: Optional[Dict[str, Any]], linea: int = 0,
                     columna: int = 0) -> Optional[Dict[str, Any]]:
        if not izquierda:
            return derecha
        if not derecha:
            return izquierda
        return {
            "type": "OperacionBinaria",
            "linea": linea or izquierda.get("linea", 0),
            "columna": columna or izquierda.get("columna", 0),
            "label": f"OPERACION: {operador}",
            "operador": operador,
            "children": [izquierda, derecha],
        }

    @staticmethod
    def _fold_binary(partes: List[ASTNode], operadores: List[str],
                     posiciones: Optional[List] = None) -> Optional[Dict[str, Any]]:
        if not partes:
            return None
        expr = ASTFormatter._to_abstract_dict(partes[0])
        for index, operador in enumerate(operadores):
            derecha = ASTFormatter._to_abstract_dict(partes[index + 1]) if index + 1 < len(partes) else None
            linea, columna = (0, 0)
            if posiciones and index < len(posiciones):
                linea, columna = posiciones[index]
            expr = ASTFormatter._binary_node(operador, expr, derecha, linea, columna)
        return expr

    @staticmethod
    def _fold_binary_right(partes: List[ASTNode], operadores: List[str],
                           posiciones: Optional[List] = None) -> Optional[Dict[str, Any]]:
        if not partes:
            return None
        expr = ASTFormatter._to_abstract_dict(partes[-1])
        for index in range(len(operadores) - 1, -1, -1):
            izquierda = ASTFormatter._to_abstract_dict(partes[index])
            linea, columna = (0, 0)
            if posiciones and index < len(posiciones):
                linea, columna = posiciones[index]
            expr = ASTFormatter._binary_node(operadores[index], izquierda, expr, linea, columna)
        return expr

    @staticmethod
    def _to_abstract_dict(node: Optional[ASTNode]) -> Optional[Dict[str, Any]]:
        if not node:
            return None

        if isinstance(node, Programa):
            node_dict = ASTFormatter._abstract_base(node, "PROGRAMA")
            if node.lista_declaracion:
                child = ASTFormatter._to_abstract_dict(node.lista_declaracion)
                if child:
                    node_dict["children"].append(child)
            return node_dict

        if isinstance(node, ListaDeclaracion):
            node_dict = ASTFormatter._abstract_base(node, "DECLARACIONES")
            for decl in node.declaraciones:
                child = ASTFormatter._to_abstract_dict(decl)
                if child:
                    node_dict["children"].append(child)
            return node_dict

        if isinstance(node, Declaracion):
            return ASTFormatter._to_abstract_dict(node.contenido)

        if isinstance(node, DeclaracionVariable):
            lexema_tipo = node.tipo_lexema or node.tipo
            node_dict = ASTFormatter._abstract_base(
                node,
                f"DECLARACION_VARIABLE: {lexema_tipo} {', '.join(node.nombres)}"
            )
            node_dict["tipo"] = node.tipo
            node_dict["tipo_lexema"] = lexema_tipo
            node_dict["identificadores"] = [
                {
                    "nombre": ident.nombre,
                    "linea": ident.linea,
                    "columna": ident.columna,
                }
                for ident in node.identificadores
            ]
            return node_dict

        if isinstance(node, ListaSentencias):
            node_dict = ASTFormatter._abstract_base(node, "BLOQUE")
            for sent in node.sentencias:
                child = ASTFormatter._to_abstract_dict(sent)
                if child:
                    node_dict["children"].append(child)
            return node_dict

        if isinstance(node, Sentencia):
            return ASTFormatter._to_abstract_dict(node.contenido)

        if isinstance(node, Asignacion):
            node_dict = ASTFormatter._abstract_base(node, f"ASIGNACION: {node.identificador}")
            node_dict["identificador"] = node.identificador
            if node.expresion:
                node_dict["children"].append(ASTFormatter._to_abstract_dict(node.expresion))
            return node_dict

        if isinstance(node, IncrementoDecremento):
            label = "INCREMENTO" if node.operador == "++" else "DECREMENTO"
            node_dict = ASTFormatter._abstract_base(node, f"{label}: {node.identificador}")
            node_dict["identificador"] = node.identificador
            node_dict["operador"] = node.operador
            return node_dict

        if isinstance(node, Seleccion):
            node_dict = ASTFormatter._abstract_base(node, "IF", "Seleccion")
            for child in (
                ASTFormatter._role("CONDICION", node.condicion),
                ASTFormatter._role("ENTONCES", node.rama_entonces),
                ASTFormatter._role("SINO", node.rama_sino),
            ):
                if child:
                    node_dict["children"].append(child)
            return node_dict

        if isinstance(node, Iteracion):
            node_dict = ASTFormatter._abstract_base(node, "WHILE", "Iteracion")
            for child in (
                ASTFormatter._role("CONDICION", node.condicion),
                ASTFormatter._role("CUERPO", node.cuerpo),
            ):
                if child:
                    node_dict["children"].append(child)
            return node_dict

        if isinstance(node, Repeticion):
            node_dict = ASTFormatter._abstract_base(node, "DO_WHILE_UNTIL", "Repeticion")
            for child in (
                ASTFormatter._role("CUERPO_DO", node.cuerpo),
                ASTFormatter._role("CONDICION_WHILE", node.condicion),
                ASTFormatter._role("CUERPO_WHILE", node.cuerpo_while),
                ASTFormatter._role("CONDICION_UNTIL", node.until_condicion),
            ):
                if child:
                    node_dict["children"].append(child)
            return node_dict

        if isinstance(node, EntradaEstandar):
            node_dict = ASTFormatter._abstract_base(node, f"ENTRADA: cin {node.identificador}")
            node_dict["identificador"] = node.identificador
            node_dict["identificador_linea"] = node.identificador_linea or node.linea
            node_dict["identificador_columna"] = node.identificador_columna or node.columna
            return node_dict

        if isinstance(node, SalidaEstandar):
            node_dict = ASTFormatter._abstract_base(node, "SALIDA: cout")
            for salida in node.salidas:
                child = ASTFormatter._to_abstract_dict(salida)
                if child:
                    node_dict["children"].append(child)
            return node_dict

        if isinstance(node, Salida):
            node_dict = ASTFormatter._abstract_base(node, "SALIDA")
            for elem in node.elementos:
                child = ASTFormatter._to_abstract_dict(elem)
                if child:
                    node_dict["children"].append(child)
            return node_dict

        if isinstance(node, Expresion):
            expr = ASTFormatter._to_abstract_dict(node.izquierda)
            if node.operador and node.derecha:
                expr = ASTFormatter._binary_node(
                    node.operador,
                    expr,
                    ASTFormatter._to_abstract_dict(node.derecha),
                    node.operador_linea,
                    node.operador_columna,
                )
            for index, siguiente in enumerate(node.siguientes_logicos):
                operador = node.operadores_logicos[index] if index < len(node.operadores_logicos) else ""
                linea, columna = (0, 0)
                if index < len(node.operadores_logicos_pos):
                    linea, columna = node.operadores_logicos_pos[index]
                expr = ASTFormatter._binary_node(
                    operador,
                    expr,
                    ASTFormatter._to_abstract_dict(siguiente),
                    linea,
                    columna,
                )
            if expr and node.errores:
                expr["children"].extend(
                    ASTFormatter._to_abstract_dict(error)
                    for error in node.errores
                )
            return expr

        if isinstance(node, ExpresionSimple):
            return ASTFormatter._fold_binary(node.terminos, node.operadores, node.operadores_pos)

        if isinstance(node, Termino):
            return ASTFormatter._fold_binary(node.factores, node.operadores, node.operadores_pos)

        if isinstance(node, Factor):
            return ASTFormatter._fold_binary_right(node.componentes, node.operadores, node.operadores_pos)

        if isinstance(node, Componente):
            if node.tipo == "numero":
                tipo = "entero" if node.es_entero else "flotante"
                node_dict = ASTFormatter._abstract_base(node, f"NUMERO: {node.valor}", "Literal")
                node_dict["tipo_literal"] = tipo
                node_dict["es_entero"] = node.es_entero
                node_dict["valor"] = node.valor
                return node_dict
            if node.tipo == "identificador":
                node_dict = ASTFormatter._abstract_base(node, f"IDENTIFICADOR: {node.valor}", "Identificador")
                node_dict["nombre"] = node.valor
                return node_dict
            if node.tipo == "booleano":
                valor = "true" if node.valor else "false"
                node_dict = ASTFormatter._abstract_base(node, f"BOOLEANO: {valor}", "Literal")
                node_dict["tipo_literal"] = "booleano"
                node_dict["valor"] = node.valor
                return node_dict
            if node.tipo == "expresion":
                return ASTFormatter._to_abstract_dict(node.expresion)
            if node.tipo == "logico":
                node_dict = ASTFormatter._abstract_base(node, f"OPERACION_UNARIA: {node.operador_logico}", "OperacionUnaria")
                node_dict["operador"] = node.operador_logico
                child = ASTFormatter._to_abstract_dict(node.siguiente)
                if child:
                    node_dict["children"].append(child)
                return node_dict

        if isinstance(node, Numero):
            node_dict = ASTFormatter._abstract_base(node, f"NUMERO: {node.valor}", "Literal")
            node_dict["tipo_literal"] = "entero" if node.es_entero else "flotante"
            node_dict["es_entero"] = node.es_entero
            node_dict["valor"] = node.valor
            return node_dict

        if isinstance(node, Identificador):
            node_dict = ASTFormatter._abstract_base(node, f"IDENTIFICADOR: {node.nombre}")
            node_dict["nombre"] = node.nombre
            return node_dict

        if isinstance(node, Cadena):
            node_dict = ASTFormatter._abstract_base(node, f"CADENA: {node.valor}", "Literal")
            node_dict["tipo_literal"] = "cadena"
            node_dict["valor"] = node.valor
            return node_dict

        if isinstance(node, Booleano):
            node_dict = ASTFormatter._abstract_base(node, f"BOOLEANO: {node.valor}", "Literal")
            node_dict["tipo_literal"] = "booleano"
            node_dict["valor"] = node.valor
            return node_dict

        if isinstance(node, NodoError):
            node_dict = ASTFormatter._abstract_base(node, f"ERROR: {node.mensaje}")
            node_dict["mensaje"] = node.mensaje
            return node_dict

        return ASTFormatter._abstract_base(node, node.__class__.__name__)

    @staticmethod
    def format_errors(errors: List) -> str:
        if not errors:
            return "Sin errores sintácticos.\n"

        result = f"Errores sintácticos encontrados: {len(errors)}\n"
        result += "=" * 60 + "\n\n"

        for i, error in enumerate(errors, 1):
            result += f"{i}. {str(error)}\n"
            if hasattr(error, 'token_esperado') and error.token_esperado:
                result += f"   Token esperado: {error.token_esperado}\n"
            if hasattr(error, 'token_encontrado') and error.token_encontrado:
                result += f"   Token encontrado: {error.token_encontrado}\n"
            result += "\n"

        return result

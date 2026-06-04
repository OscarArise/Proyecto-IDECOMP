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
    def _leaf(label: str, node_type: str = "Token", linea: int = 0, columna: int = 0) -> Dict[str, Any]:
        return {
            "type": node_type,
            "linea": linea,
            "columna": columna,
            "children": [],
            "label": label,
        }

    @staticmethod
    def _dict_to_text(node_dict: Optional[Dict[str, Any]], indent: int = 0) -> str:
        if not node_dict:
            return ""
        prefix = "  " * indent
        label = node_dict.get("label") or node_dict.get("type", "")
        result = f"{prefix}{label}\n"
        for child in node_dict.get("children", []):
            result += ASTFormatter._dict_to_text(child, indent + 1)
        return result

    @staticmethod
    def to_text(node: Optional[ASTNode], indent: int = 0) -> str:
        """Convierte el AST a una representación de texto indentada."""
        if not node:
            return ""
        return ASTFormatter._dict_to_text(ASTFormatter.to_dict(node), indent)

        prefix = "  " * indent
        result = ""

        if isinstance(node, Programa):
            result += f"{prefix}main {{\n"
            if node.lista_declaracion:
                result += ASTFormatter.to_text(node.lista_declaracion, indent + 1)
            result += f"{prefix}}}\n"

        elif isinstance(node, ListaDeclaracion):
            for decl in node.declaraciones:
                result += ASTFormatter.to_text(decl, indent)

        elif isinstance(node, Declaracion):
            if node.contenido:
                result += ASTFormatter.to_text(node.contenido, indent)

        elif isinstance(node, DeclaracionVariable):
            result += f"{prefix}{node.tipo} {', '.join(node.identificadores)};\n"

        elif isinstance(node, ListaSentencias):
            for sent in node.sentencias:
                result += ASTFormatter.to_text(sent, indent)

        elif isinstance(node, Sentencia):
            if node.contenido:
                result += ASTFormatter.to_text(node.contenido, indent)

        elif isinstance(node, Asignacion):
            result += f"{prefix}{node.identificador} = "
            if node.expresion:
                result += ASTFormatter._expresion_to_simple_text(node.expresion)
            result += ";\n"

        elif isinstance(node, IncrementoDecremento):
            result += f"{prefix}{node.identificador}{node.operador};\n"

        elif isinstance(node, Seleccion):
            result += f"{prefix}if "
            if node.condicion:
                result += ASTFormatter._expresion_to_simple_text(node.condicion)
            result += " then\n"
            if node.rama_entonces:
                result += ASTFormatter.to_text(node.rama_entonces, indent + 1)
            if node.rama_sino:
                result += f"{prefix}else\n"
                result += ASTFormatter.to_text(node.rama_sino, indent + 1)
            result += f"{prefix}end\n"

        elif isinstance(node, Iteracion):
            result += f"{prefix}while "
            if node.condicion:
                result += ASTFormatter._expresion_to_simple_text(node.condicion)
            result += "\n"
            if node.cuerpo:
                result += ASTFormatter.to_text(node.cuerpo, indent + 1)
            result += f"{prefix}end\n"

        elif isinstance(node, Repeticion):
            result += f"{prefix}do\n"
            if node.cuerpo:
                result += ASTFormatter.to_text(node.cuerpo, indent + 1)
            result += f"{prefix}while "
            if node.condicion:
                result += ASTFormatter._expresion_to_simple_text(node.condicion)
            result += "\n"
            if hasattr(node, 'until_condicion') and node.until_condicion:
                result += f"{prefix}until "
                result += ASTFormatter._expresion_to_simple_text(node.until_condicion)
                result += "\n"

        elif isinstance(node, EntradaEstandar):
            result += f"{prefix}cin {node.identificador};\n"

        elif isinstance(node, SalidaEstandar):
            result += f"{prefix}cout "
            partes = []
            for salida in node.salidas:
                partes.extend(ASTFormatter._salida_to_text(salida))
            result += " << ".join(partes) + ";\n"

        elif isinstance(node, NodoError):
            result += f"{prefix}[ERROR] {node.mensaje}\n"

        return result

    # ------------------------------------------------------------------ #
    # Helpers de texto para expresiones                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _expresion_to_simple_text(expr: Expresion) -> str:
        if not expr.izquierda:
            return ""
        text = ASTFormatter._expresion_simple_to_text(expr.izquierda)
        if expr.operador and expr.derecha:
            text += f" {expr.operador} "
            text += ASTFormatter._expresion_simple_to_text(expr.derecha)
        for index, siguiente in enumerate(expr.siguientes_logicos):
            if index < len(expr.operadores_logicos):
                text += f" {expr.operadores_logicos[index]} "
                text += ASTFormatter._expresion_to_simple_text(siguiente)
        return text

    @staticmethod
    def _expresion_simple_to_text(exp_simple: ExpresionSimple) -> str:
        partes = []
        for i, termino in enumerate(exp_simple.terminos):
            if i > 0 and i - 1 < len(exp_simple.operadores):
                partes.append(exp_simple.operadores[i - 1])
            partes.append(ASTFormatter._termino_to_text(termino))
        return " ".join(partes)

    @staticmethod
    def _termino_to_text(termino: Termino) -> str:
        partes = []
        for i, factor in enumerate(termino.factores):
            if i > 0 and i - 1 < len(termino.operadores):
                partes.append(termino.operadores[i - 1])
            partes.append(ASTFormatter._factor_to_text(factor))
        return " ".join(partes)

    @staticmethod
    def _factor_to_text(factor: Factor) -> str:
        partes = []
        for i, comp in enumerate(factor.componentes):
            if i > 0 and i - 1 < len(factor.operadores):
                partes.append(factor.operadores[i - 1])
            partes.append(ASTFormatter._componente_to_text(comp))
        return " ".join(partes)

    @staticmethod
    def _componente_to_text(comp: Componente) -> str:
        if comp.tipo == "numero":
            if comp.es_entero:
                return str(int(comp.valor))
            return str(comp.valor)
        elif comp.tipo == "identificador":
            return comp.valor
        elif comp.tipo == "booleano":
            return "true" if comp.valor else "false"
        elif comp.tipo == "expresion":
            if comp.expresion:
                return f"({ASTFormatter._expresion_to_simple_text(comp.expresion)})"
            return "()"
        elif comp.tipo == "logico":
            text = comp.operador_logico or ""
            if comp.siguiente:
                text += " " + ASTFormatter._componente_to_text(comp.siguiente)
            return text
        return ""

    @staticmethod
    def _salida_to_text(salida: Salida) -> List[str]:
        partes = []
        for elem in salida.elementos:
            if isinstance(elem, Cadena):
                partes.append(f'"{elem.valor}"')
            elif isinstance(elem, Expresion):
                partes.append(ASTFormatter._expresion_to_simple_text(elem))
        return partes

    # ------------------------------------------------------------------ #
    # Serialización a diccionario (JSON)                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def to_dict(node: Optional[ASTNode]) -> Optional[Dict[str, Any]]:
        """Convierte el AST a un diccionario recursivo para serialización JSON."""
        if not node:
            return None
        return ASTFormatter._to_abstract_dict(node)

        node_dict: Dict[str, Any] = {
            "type": node.__class__.__name__,
            "linea": node.linea,
            "columna": node.columna,
            "children": []
        }

        if isinstance(node, Programa):
            node_dict["label"] = "PROGRAMA"
            node_dict["children"].append(ASTFormatter._leaf("MAIN: main", linea=node.linea, columna=node.columna))
            node_dict["children"].append(ASTFormatter._leaf(
                "LLAVE_IZQUIERDA: {",
                linea=node.llave_izq_linea or node.linea,
                columna=node.llave_izq_columna or node.columna,
            ))
            if node.lista_declaracion:
                node_dict["children"].append(ASTFormatter.to_dict(node.lista_declaracion))
            node_dict["children"].append(ASTFormatter._leaf(
                "LLAVE_DERECHA: }",
                linea=node.llave_der_linea or node.linea,
                columna=node.llave_der_columna or node.columna,
            ))

        elif isinstance(node, ListaDeclaracion):
            node_dict["label"] = "LISTA_DECLARACION"
            for decl in node.declaraciones:
                child = ASTFormatter.to_dict(decl)
                if child:
                    node_dict["children"].append(child)

        elif isinstance(node, Declaracion):
            node_dict["label"] = "Declaración"
            if node.contenido:
                child = ASTFormatter.to_dict(node.contenido)
                if child:
                    node_dict["children"].append(child)

        elif isinstance(node, DeclaracionVariable):
            node_dict["label"] = "DECLARACION_VARIABLE"
            node_dict["tipo"] = node.tipo
            node_dict["identificadores"] = node.identificadores
            node_dict["children"].append(
                ASTFormatter._leaf(f"TIPO_DATO: {node.tipo}", linea=node.linea, columna=node.columna)
            )
            variables: Dict[str, Any] = {
                "type": "Variables",
                "linea": node.linea,
                "columna": node.columna,
                "children": [],
                "label": "VARIABLES",
            }
            for index, ident in enumerate(node.identificadores):
                variables["children"].append(
                    ASTFormatter._leaf(f"IDENTIFICADOR: {ident}", linea=node.linea, columna=node.columna)
                )
                if index < len(node.identificadores) - 1:
                    variables["children"].append(ASTFormatter._leaf("COMA: ,", linea=node.linea, columna=node.columna))
            node_dict["children"].append(variables)
            node_dict["children"].append(ASTFormatter._leaf("PUNTO_COMA: ;", linea=node.linea, columna=node.columna))

        elif isinstance(node, ListaSentencias):
            node_dict["label"] = "LISTA_SENTENCIAS"
            for sent in node.sentencias:
                child = ASTFormatter.to_dict(sent)
                if child:
                    node_dict["children"].append(child)

        elif isinstance(node, Sentencia):
            node_dict["label"] = "SENTENCIA"
            if node.contenido:
                child = ASTFormatter.to_dict(node.contenido)
                if child:
                    node_dict["children"].append(child)

        elif isinstance(node, Asignacion):
            node_dict["label"] = "ASIGNACION"
            node_dict["identificador"] = node.identificador
            node_dict["children"].append(
                ASTFormatter._leaf(f"IDENTIFICADOR: {node.identificador}", linea=node.linea, columna=node.columna)
            )
            node_dict["children"].append(
                ASTFormatter._leaf("ASIGNACION: =", linea=node.linea, columna=node.columna)
            )
            if node.expresion:
                node_dict["children"].append(ASTFormatter.to_dict(node.expresion))
            node_dict["children"].append(
                ASTFormatter._leaf("PUNTO_COMA: ;", linea=node.linea, columna=node.columna)
            )

        elif isinstance(node, IncrementoDecremento):
            node_dict["label"] = "INCREMENTO" if node.operador == "++" else "DECREMENTO"
            node_dict["identificador"] = node.identificador
            node_dict["operador"] = node.operador
            node_dict["children"].append(
                ASTFormatter._leaf(f"IDENTIFICADOR: {node.identificador}", linea=node.linea, columna=node.columna)
            )
            node_dict["children"].append(
                ASTFormatter._leaf(f"OPERADOR: {node.operador}", linea=node.linea, columna=node.columna)
            )
            node_dict["children"].append(
                ASTFormatter._leaf("PUNTO_COMA: ;", linea=node.linea, columna=node.columna)
            )

        elif isinstance(node, Seleccion):
            node_dict["label"] = "SELECCION"
            node_dict["children"].append(
                ASTFormatter._leaf("IF: if", linea=node.linea, columna=node.columna)
            )
            if node.condicion:
                cond_dict = ASTFormatter.to_dict(node.condicion)
                if cond_dict:
                    cond_dict["label"] = "CONDICION"
                    node_dict["children"].append(cond_dict)
            node_dict["children"].append(
                ASTFormatter._leaf("THEN: then", linea=node.linea, columna=node.columna)
            )
            if node.rama_entonces:
                then_dict = ASTFormatter.to_dict(node.rama_entonces)
                if then_dict:
                    then_dict["label"] = "RAMA_ENTONCES"
                    node_dict["children"].append(then_dict)
            if node.rama_sino:
                # linea/columna del else no está en el nodo; usamos el del nodo padre como aproximación
                node_dict["children"].append(
                    ASTFormatter._leaf("ELSE: else", linea=node.linea, columna=node.columna)
                )
                else_dict = ASTFormatter.to_dict(node.rama_sino)
                if else_dict:
                    else_dict["label"] = "RAMA_SINO"
                    node_dict["children"].append(else_dict)
            node_dict["children"].append(
                ASTFormatter._leaf("END: end", linea=node.linea, columna=node.columna)
            )

        elif isinstance(node, Iteracion):
            node_dict["label"] = "ITERACION"
            node_dict["children"].append(
                ASTFormatter._leaf("WHILE: while", linea=node.linea, columna=node.columna)
            )
            if node.condicion:
                cond_dict = ASTFormatter.to_dict(node.condicion)
                if cond_dict:
                    cond_dict["label"] = "CONDICION"
                    node_dict["children"].append(cond_dict)
            if node.cuerpo:
                body_dict = ASTFormatter.to_dict(node.cuerpo)
                if body_dict:
                    body_dict["label"] = "CUERPO"
                    node_dict["children"].append(body_dict)
            node_dict["children"].append(ASTFormatter._leaf("END: end", linea=node.linea, columna=node.columna))

        elif isinstance(node, Repeticion):
            node_dict["label"] = "REPETICION"
            node_dict["children"].append(
                ASTFormatter._leaf("DO: do", linea=node.linea, columna=node.columna)
            )
            if node.cuerpo:
                body_dict = ASTFormatter.to_dict(node.cuerpo)
                if body_dict:
                    body_dict["label"] = "CUERPO"
                    node_dict["children"].append(body_dict)
            node_dict["children"].append(
                ASTFormatter._leaf("WHILE: while", linea=node.linea, columna=node.columna)
            )
            if node.condicion:
                cond_dict = ASTFormatter.to_dict(node.condicion)
                if cond_dict:
                    cond_dict["label"] = "CONDICION_WHILE"
                    node_dict["children"].append(cond_dict)
            if hasattr(node, 'until_condicion') and node.until_condicion:
                node_dict["children"].append(
                    ASTFormatter._leaf("UNTIL: until", linea=node.linea, columna=node.columna)
                )
                until_dict = ASTFormatter.to_dict(node.until_condicion)
                if until_dict:
                    until_dict["label"] = "CONDICION_UNTIL"
                    node_dict["children"].append(until_dict)

        elif isinstance(node, EntradaEstandar):
            node_dict["label"] = "ENTRADA_ESTANDAR"
            node_dict["identificador"] = node.identificador
            node_dict["children"].append(
                ASTFormatter._leaf("CIN: cin", linea=node.linea, columna=node.columna)
            )
            node_dict["children"].append(
                ASTFormatter._leaf(f"IDENTIFICADOR: {node.identificador}", linea=node.linea, columna=node.columna)
            )
            node_dict["children"].append(ASTFormatter._leaf("PUNTO_COMA: ;", linea=node.linea, columna=node.columna))

        elif isinstance(node, SalidaEstandar):
            node_dict["label"] = "SALIDA_ESTANDAR"
            node_dict["children"].append(
                ASTFormatter._leaf("COUT: cout", linea=node.linea, columna=node.columna)
            )
            for salida in node.salidas:
                child = ASTFormatter.to_dict(salida)
                if child:
                    node_dict["children"].append(child)
            node_dict["children"].append(ASTFormatter._leaf("PUNTO_COMA: ;", linea=node.linea, columna=node.columna))

        elif isinstance(node, Salida):
            node_dict["label"] = "SALIDA"
            for elem in node.elementos:
                child = ASTFormatter.to_dict(elem)
                if child:
                    node_dict["children"].append(child)

        elif isinstance(node, Expresion):
            label = ASTFormatter._expresion_to_simple_text(node) if node.izquierda else ""
            node_dict["label"] = f"Expresión: {label}" if label else "Expresión vacía"
            if node.izquierda:
                node_dict["children"].append(ASTFormatter.to_dict(node.izquierda))
            if node.operador:
                node_dict["children"].append(
                    ASTFormatter._leaf(
                        f"REL_OP: {node.operador}",
                        linea=node.operador_linea,
                        columna=node.operador_columna,
                    )
                )
            if node.derecha:
                node_dict["children"].append(ASTFormatter.to_dict(node.derecha))
            for index, siguiente in enumerate(node.siguientes_logicos):
                if index < len(node.operadores_logicos):
                    op_linea, op_columna = node.operadores_logicos_pos[index]
                    node_dict["children"].append(
                        ASTFormatter._leaf(
                            f"LOGIC_OP: {node.operadores_logicos[index]}",
                            linea=op_linea,
                            columna=op_columna,
                        )
                    )
                node_dict["children"].append(ASTFormatter.to_dict(siguiente))

        elif isinstance(node, ExpresionSimple):
            label = ASTFormatter._expresion_simple_to_text(node)
            node_dict["label"] = f"ExpresionSimple: {label}"
            node_dict["children"] = []
            for index, termino in enumerate(node.terminos):
                if index > 0 and index - 1 < len(node.operadores):
                    op_linea, op_columna = node.operadores_pos[index - 1]
                    node_dict["children"].append(
                        ASTFormatter._leaf(
                            f"SUMA_OP: {node.operadores[index - 1]}",
                            linea=op_linea,
                            columna=op_columna,
                        )
                    )
                node_dict["children"].append(ASTFormatter.to_dict(termino))

        elif isinstance(node, Termino):
            label = ASTFormatter._termino_to_text(node)
            node_dict["label"] = f"Termino: {label}"
            node_dict["children"] = []
            for index, factor in enumerate(node.factores):
                if index > 0 and index - 1 < len(node.operadores):
                    op_linea, op_columna = node.operadores_pos[index - 1]
                    node_dict["children"].append(
                        ASTFormatter._leaf(
                            f"MULT_OP: {node.operadores[index - 1]}",
                            linea=op_linea,
                            columna=op_columna,
                        )
                    )
                node_dict["children"].append(ASTFormatter.to_dict(factor))

        elif isinstance(node, Factor):
            label = ASTFormatter._factor_to_text(node)
            node_dict["label"] = f"Factor: {label}"
            node_dict["children"] = []
            for index, comp in enumerate(node.componentes):
                if index > 0 and index - 1 < len(node.operadores):
                    op_linea, op_columna = node.operadores_pos[index - 1]
                    node_dict["children"].append(
                        ASTFormatter._leaf(
                            f"POT_OP: {node.operadores[index - 1]}",
                            linea=op_linea,
                            columna=op_columna,
                        )
                    )
                node_dict["children"].append(ASTFormatter.to_dict(comp))

        elif isinstance(node, Componente):
            label = ASTFormatter._componente_to_text(node)
            node_dict["label"] = f"Componente: {label}"
            if node.siguiente:
                node_dict["children"].append(ASTFormatter.to_dict(node.siguiente))

        elif isinstance(node, Numero):
            node_dict["label"] = f"Número: {node.valor}"
            node_dict["valor"] = node.valor

        elif isinstance(node, Identificador):
            node_dict["label"] = f"Identificador: {node.nombre}"
            node_dict["nombre"] = node.nombre

        elif isinstance(node, Cadena):
            node_dict["label"] = f'Cadena: "{node.valor}"'
            node_dict["valor"] = node.valor

        elif isinstance(node, Booleano):
            node_dict["label"] = f"Booleano: {node.valor}"
            node_dict["valor"] = node.valor

        elif isinstance(node, NodoError):
            node_dict["label"] = f"[ERROR] {node.mensaje}"
            node_dict["mensaje"] = node.mensaje

        # Limpiar hijos nulos
        node_dict["children"] = [c for c in node_dict["children"] if c is not None]

        return node_dict

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
            node_dict = ASTFormatter._abstract_base(
                node,
                f"DECLARACION_VARIABLE: {node.tipo} {', '.join(node.identificadores)}"
            )
            node_dict["tipo"] = node.tipo
            node_dict["identificadores"] = node.identificadores
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
                ASTFormatter._role("CUERPO", node.cuerpo),
                ASTFormatter._role("CONDICION_WHILE", node.condicion),
                ASTFormatter._role("CONDICION_UNTIL", node.until_condicion),
            ):
                if child:
                    node_dict["children"].append(child)
            return node_dict

        if isinstance(node, EntradaEstandar):
            node_dict = ASTFormatter._abstract_base(node, f"ENTRADA: cin {node.identificador}")
            node_dict["identificador"] = node.identificador
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

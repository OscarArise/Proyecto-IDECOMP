"""
ast_formatter.py
----------------
Proporciona funciones para formatear y serializar el AST para visualización.
"""

from typing import Optional, List, Dict, Any
from .ast_nodes import (
    ASTNode, Programa, ListaDeclaracion, Declaracion, DeclaracionVariable,
    ListaSentencias, Sentencia, Asignacion, Seleccion, Iteracion, Repeticion,
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
    def to_text(node: Optional[ASTNode], indent: int = 0) -> str:
        """Convierte el AST a una representación de texto indentada."""
        if not node:
            return ""

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
            result += f"{prefix}cin >> {node.identificador};\n"

        elif isinstance(node, SalidaEstandar):
            result += f"{prefix}cout << "
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

        node_dict: Dict[str, Any] = {
            "type": node.__class__.__name__,
            "linea": node.linea,
            "columna": node.columna,
            "children": []
        }

        if isinstance(node, Programa):
            node_dict["label"] = "PROGRAMA"
            node_dict["children"].append(ASTFormatter._leaf("MAIN: main", linea=node.linea, columna=node.columna))
            node_dict["children"].append(ASTFormatter._leaf("LLAVE_IZQUIERDA: {"))
            if node.lista_declaracion:
                node_dict["children"].append(ASTFormatter.to_dict(node.lista_declaracion))
            node_dict["children"].append(ASTFormatter._leaf("LLAVE_DERECHA: }"))

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
                variables["children"].append(ASTFormatter._leaf(f"IDENTIFICADOR: {ident}"))
                if index < len(node.identificadores) - 1:
                    variables["children"].append(ASTFormatter._leaf("COMA: ,"))
            node_dict["children"].append(variables)
            node_dict["children"].append(ASTFormatter._leaf("PUNTO_COMA: ;"))

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
            node_dict["children"].append(ASTFormatter._leaf("END: end"))

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
            node_dict["children"].append(ASTFormatter._leaf("MAYOR: >"))
            node_dict["children"].append(ASTFormatter._leaf("MAYOR: >"))
            node_dict["children"].append(ASTFormatter._leaf(f"IDENTIFICADOR: {node.identificador}"))
            node_dict["children"].append(ASTFormatter._leaf("PUNTO_COMA: ;"))

        elif isinstance(node, SalidaEstandar):
            node_dict["label"] = "SALIDA_ESTANDAR"
            node_dict["children"].append(
                ASTFormatter._leaf("COUT: cout", linea=node.linea, columna=node.columna)
            )
            node_dict["children"].append(ASTFormatter._leaf("MENOR: <"))
            node_dict["children"].append(ASTFormatter._leaf("MENOR: <"))
            for salida in node.salidas:
                child = ASTFormatter.to_dict(salida)
                if child:
                    node_dict["children"].append(child)
            node_dict["children"].append(ASTFormatter._leaf("PUNTO_COMA: ;"))

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
                node_dict["children"].append(ASTFormatter._leaf(f"REL_OP: {node.operador}"))
            if node.derecha:
                node_dict["children"].append(ASTFormatter.to_dict(node.derecha))

        elif isinstance(node, ExpresionSimple):
            label = ASTFormatter._expresion_simple_to_text(node)
            node_dict["label"] = f"ExpresionSimple: {label}"
            node_dict["children"] = []
            for index, termino in enumerate(node.terminos):
                if index > 0 and index - 1 < len(node.operadores):
                    node_dict["children"].append(
                        ASTFormatter._leaf(f"SUMA_OP: {node.operadores[index - 1]}")
                    )
                node_dict["children"].append(ASTFormatter.to_dict(termino))

        elif isinstance(node, Termino):
            label = ASTFormatter._termino_to_text(node)
            node_dict["label"] = f"Termino: {label}"
            node_dict["children"] = []
            for index, factor in enumerate(node.factores):
                if index > 0 and index - 1 < len(node.operadores):
                    node_dict["children"].append(
                        ASTFormatter._leaf(f"MULT_OP: {node.operadores[index - 1]}")
                    )
                node_dict["children"].append(ASTFormatter.to_dict(factor))

        elif isinstance(node, Factor):
            label = ASTFormatter._factor_to_text(node)
            node_dict["label"] = f"Factor: {label}"
            node_dict["children"] = []
            for index, comp in enumerate(node.componentes):
                if index > 0 and index - 1 < len(node.operadores):
                    node_dict["children"].append(
                        ASTFormatter._leaf(f"POT_OP: {node.operadores[index - 1]}")
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
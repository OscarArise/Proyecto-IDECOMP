"""
ast_formatter.py
----------------
Proporciona funciones para formatear y serializar el AST para visualización.
"""

from typing import Optional, List, Dict, Any
from .ast_nodes import ASTNode, Programa, ListaDeclaracion, Declaracion, DeclaracionVariable
from .ast_nodes import ListaSentencias, Sentencia, Asignacion, Seleccion, Iteracion, Repeticion
from .ast_nodes import EntradaEstandar, SalidaEstandar, Salida
from .ast_nodes import Expresion, ExpresionSimple, Termino, Factor, Componente
from .ast_nodes import Numero, Identificador, Cadena, Booleano, NodoError


class ASTFormatter:
    """Formatea y serializa nodos AST para visualización."""

    @staticmethod
    def to_text(node: Optional[ASTNode], indent: int = 0) -> str:
        """Convierte el AST a una representación de texto indentada."""
        if not node:
            return ""

        prefix = "  " * indent
        result = ""

        # Determinan el tipo de nodo y su representación
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
            resultado_tipos = f"{node.tipo} {', '.join(node.identificadores)};"
            result += f"{prefix}{resultado_tipos}\n"

        elif isinstance(node, ListaSentencias):
            for sent in node.sentencias:
                result += ASTFormatter.to_text(sent, indent)

        elif isinstance(node, Sentencia):
            if node.contenido:
                result += ASTFormatter.to_text(node.contenido, indent)

        elif isinstance(node, Asignacion):
            result += f"{prefix}{node.identificador} = "
            if node.expresion:
                expr_text = ASTFormatter._expresion_to_simple_text(node.expresion)
                result += f"{expr_text}"
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
            result += ";\n"

        elif isinstance(node, EntradaEstandar):
            result += f"{prefix}cin >> {node.identificador};\n"

        elif isinstance(node, SalidaEstandar):
            result += f"{prefix}cout << "
            salidas_text = []
            for salida in node.salidas:
                salidas_text.extend(ASTFormatter._salida_to_text(salida))
            result += " << ".join(salidas_text) + ";\n"

        elif isinstance(node, NodoError):
            result += f"{prefix}[ERROR] {node.mensaje}\n"

        return result

    @staticmethod
    def _expresion_to_simple_text(expr: Expresion) -> str:
        """Convierte una expresión a texto simple (sin indentación)."""
        if not expr.izquierda:
            return ""

        text = ASTFormatter._expresion_simple_to_text(expr.izquierda)

        if expr.operador and expr.derecha:
            text += f" {expr.operador} "
            text += ASTFormatter._expresion_simple_to_text(expr.derecha)

        return text

    @staticmethod
    def _expresion_simple_to_text(exp_simple: ExpresionSimple) -> str:
        """Convierte una expresión simple a texto."""
        partes = []
        for i, termino in enumerate(exp_simple.terminos):
            if i > 0 and i - 1 < len(exp_simple.operadores):
                partes.append(exp_simple.operadores[i - 1])
            partes.append(ASTFormatter._termino_to_text(termino))
        return " ".join(partes)

    @staticmethod
    def _termino_to_text(termino: Termino) -> str:
        """Convierte un término a texto."""
        partes = []
        for i, factor in enumerate(termino.factores):
            if i > 0 and i - 1 < len(termino.operadores):
                partes.append(termino.operadores[i - 1])
            partes.append(ASTFormatter._factor_to_text(factor))
        return " ".join(partes)

    @staticmethod
    def _factor_to_text(factor: Factor) -> str:
        """Convierte un factor a texto."""
        partes = []
        for i, comp in enumerate(factor.componentes):
            if i > 0 and i - 1 < len(factor.operadores):
                partes.append(factor.operadores[i - 1])
            partes.append(ASTFormatter._componente_to_text(comp))
        return " ".join(partes)

    @staticmethod
    def _componente_to_text(comp: Componente) -> str:
        """Convierte un componente a texto."""
        if comp.tipo == "numero":
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
        """Convierte una salida a texto."""
        partes = []
        for elem in salida.elementos:
            if isinstance(elem, Cadena):
                partes.append(f'"{elem.valor}"')
            elif isinstance(elem, Expresion):
                partes.append(ASTFormatter._expresion_to_simple_text(elem))
        return partes

    @staticmethod
    def to_dict(node: Optional[ASTNode]) -> Optional[Dict[str, Any]]:
        """
        Convierte el AST a un diccionario recursivo para serialización JSON.
        Útil para visualización en árbol colapsable.
        """
        if not node:
            return None

        node_dict = {
            "type": node.__class__.__name__,
            "linea": node.linea,
            "columna": node.columna,
            "children": []
        }

        # Agregar información específica del nodo
        if isinstance(node, Programa):
            node_dict["label"] = "main"
            if node.lista_declaracion:
                node_dict["children"].append(ASTFormatter.to_dict(node.lista_declaracion))

        elif isinstance(node, ListaDeclaracion):
            node_dict["label"] = "Declaraciones"
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
            node_dict["label"] = f"{node.tipo}: {', '.join(node.identificadores)}"
            node_dict["tipo"] = node.tipo
            node_dict["identificadores"] = node.identificadores

        elif isinstance(node, ListaSentencias):
            node_dict["label"] = "Sentencias"
            for sent in node.sentencias:
                child = ASTFormatter.to_dict(sent)
                if child:
                    node_dict["children"].append(child)

        elif isinstance(node, Sentencia):
            node_dict["label"] = "Sentencia"
            if node.contenido:
                child = ASTFormatter.to_dict(node.contenido)
                if child:
                    node_dict["children"].append(child)

        elif isinstance(node, Asignacion):
            node_dict["label"] = f"Asignación: {node.identificador} = ..."
            node_dict["identificador"] = node.identificador
            if node.expresion:
                node_dict["children"].append(ASTFormatter.to_dict(node.expresion))

        elif isinstance(node, Seleccion):
            node_dict["label"] = "if ... then ... [else ...] end"
            if node.condicion:
                cond_dict = ASTFormatter.to_dict(node.condicion)
                if cond_dict:
                    cond_dict["label"] = "Condición: " + (cond_dict.get("label", ""))
                    node_dict["children"].append(cond_dict)
            if node.rama_entonces:
                then_dict = ASTFormatter.to_dict(node.rama_entonces)
                if then_dict:
                    then_dict["label"] = "Rama entonces"
                    node_dict["children"].append(then_dict)
            if node.rama_sino:
                else_dict = ASTFormatter.to_dict(node.rama_sino)
                if else_dict:
                    else_dict["label"] = "Rama sino"
                    node_dict["children"].append(else_dict)

        elif isinstance(node, Iteracion):
            node_dict["label"] = "while ... end"
            if node.condicion:
                cond_dict = ASTFormatter.to_dict(node.condicion)
                if cond_dict:
                    cond_dict["label"] = "Condición: " + (cond_dict.get("label", ""))
                    node_dict["children"].append(cond_dict)
            if node.cuerpo:
                body_dict = ASTFormatter.to_dict(node.cuerpo)
                if body_dict:
                    body_dict["label"] = "Cuerpo"
                    node_dict["children"].append(body_dict)

        elif isinstance(node, Repeticion):
            node_dict["label"] = "do ... while"
            if node.cuerpo:
                body_dict = ASTFormatter.to_dict(node.cuerpo)
                if body_dict:
                    body_dict["label"] = "Cuerpo"
                    node_dict["children"].append(body_dict)
            if node.condicion:
                cond_dict = ASTFormatter.to_dict(node.condicion)
                if cond_dict:
                    cond_dict["label"] = "Condición: " + (cond_dict.get("label", ""))
                    node_dict["children"].append(cond_dict)

        elif isinstance(node, EntradaEstandar):
            node_dict["label"] = f"cin >> {node.identificador}"
            node_dict["identificador"] = node.identificador

        elif isinstance(node, SalidaEstandar):
            node_dict["label"] = "cout << ..."
            for salida in node.salidas:
                child = ASTFormatter.to_dict(salida)
                if child:
                    node_dict["children"].append(child)

        elif isinstance(node, Salida):
            node_dict["label"] = "Salida"
            for elem in node.elementos:
                child = ASTFormatter.to_dict(elem)
                if child:
                    node_dict["children"].append(child)

        elif isinstance(node, Expresion):
            if node.izquierda:
                label = ASTFormatter._expresion_to_simple_text(node)
                node_dict["label"] = f"Expresión: {label}"
            else:
                node_dict["label"] = "Expresión vacía"
            if node.izquierda:
                node_dict["children"].append(ASTFormatter.to_dict(node.izquierda))
            if node.derecha:
                node_dict["children"].append(ASTFormatter.to_dict(node.derecha))

        elif isinstance(node, ExpresionSimple):
            label = ASTFormatter._expresion_simple_to_text(node)
            node_dict["label"] = f"ExpresionSimple: {label}"
            node_dict["children"] = [ASTFormatter.to_dict(t) for t in node.terminos]

        elif isinstance(node, Termino):
            label = ASTFormatter._termino_to_text(node)
            node_dict["label"] = f"Termino: {label}"
            node_dict["children"] = [ASTFormatter.to_dict(f) for f in node.factores]

        elif isinstance(node, Factor):
            label = ASTFormatter._factor_to_text(node)
            node_dict["label"] = f"Factor: {label}"
            node_dict["children"] = [ASTFormatter.to_dict(c) for c in node.componentes]

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
        """Formatea una lista de errores sintácticos para visualización."""
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

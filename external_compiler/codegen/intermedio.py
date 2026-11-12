"""
intermedio.py
-------------
Código intermedio de tres direcciones (archivo .ci), equivalente a
generarCodigoIntermedio de la extensión didáctica de TINY.

Recorre el mismo árbol anotado que cgen.py y escribe cada cálculo con
temporales simbólicos (t1, t2, ...) y etiquetas (L1, L2, ...):

    t2 = fact * x;
    fact = t2;
    if_false t3 goto L1;
    goto L2;
    L1:

Es una salida adicional para estudio: no se traduce a TM ni es la entrada del
simulador. Los temporales no corresponden a registros ni a direcciones TM.
"""

from typing import Any, Dict, List, Optional

from .cgen import ErrorGeneracion, texto_cadena

Nodo = Dict[str, Any]


class GeneradorIntermedio:

    def __init__(self):
        self.lineas: List[str] = []
        self.temporales = 0
        self.etiquetas = 0

    def nuevo_temporal(self) -> str:
        self.temporales += 1
        return f"t{self.temporales}"

    def nueva_etiqueta(self) -> str:
        self.etiquetas += 1
        return f"L{self.etiquetas}"

    def emitir(self, instruccion: str) -> None:
        self.lineas.append(f"    {instruccion}")

    def emitir_etiqueta(self, etiqueta: str) -> None:
        self.lineas.append(f"{etiqueta}:")

    # ------------------------------------------------------------------
    # Sentencias
    # ------------------------------------------------------------------

    @staticmethod
    def _seccion(nodo: Nodo, nombre: str) -> Optional[Nodo]:
        for hijo in nodo.get("children", []):
            etiqueta = hijo.get("label_sintactico", hijo.get("label"))
            if hijo.get("type") == "SeccionAST" and etiqueta == nombre:
                return hijo
        return None

    def _condicion(self, seccion: Optional[Nodo]) -> str:
        if not seccion or not seccion.get("children"):
            raise ErrorGeneracion("Estructura de control sin condición")
        return self.expresion(seccion["children"][0])

    def sentencia(self, nodo: Optional[Nodo]) -> None:
        if not nodo:
            return
        tipo = nodo.get("type", "")

        if tipo == "DeclaracionVariable":
            nombres = ", ".join(i.get("nombre", "") for i in nodo.get("identificadores", []))
            self.lineas.append(f"// declarar {nodo.get('tipo', '')} {nombres}")

        elif tipo == "Asignacion":
            valor = self.expresion(nodo["children"][0])
            self.emitir(f"{nodo['identificador']} = {valor};")

        elif tipo == "IncrementoDecremento":
            nombre = nodo["identificador"]
            t = self.nuevo_temporal()
            op = "+" if nodo.get("operador") == "++" else "-"
            self.emitir(f"{t} = {nombre} {op} 1;")
            self.emitir(f"{nombre} = {t};")

        elif tipo == "EntradaEstandar":
            self.emitir(f"read {nodo['identificador']};")

        elif tipo == "SalidaEstandar":
            for salida in nodo.get("children", []):
                for elemento in salida.get("children", []):
                    self.emitir(f"write {self.expresion(elemento)};")
            self.emitir("writeln;")

        elif tipo == "Seleccion":
            cond = self._condicion(self._seccion(nodo, "CONDICION"))
            sino = self._seccion(nodo, "SINO")
            l_sino = self.nueva_etiqueta()
            self.emitir(f"if_false {cond} goto {l_sino};")
            self.sentencia(self._seccion(nodo, "ENTONCES"))
            if sino:
                l_fin = self.nueva_etiqueta()
                self.emitir(f"goto {l_fin};")
                self.emitir_etiqueta(l_sino)
                self.sentencia(sino)
                self.emitir_etiqueta(l_fin)
            else:
                self.emitir_etiqueta(l_sino)

        elif tipo == "Iteracion":
            l_inicio = self.nueva_etiqueta()
            l_fin = self.nueva_etiqueta()
            self.emitir_etiqueta(l_inicio)
            cond = self._condicion(self._seccion(nodo, "CONDICION"))
            self.emitir(f"if_false {cond} goto {l_fin};")
            self.sentencia(self._seccion(nodo, "CUERPO"))
            self.emitir(f"goto {l_inicio};")
            self.emitir_etiqueta(l_fin)

        elif tipo == "Repeticion":
            l_inicio = self.nueva_etiqueta()
            self.emitir_etiqueta(l_inicio)
            self.sentencia(self._seccion(nodo, "CUERPO"))
            cond = self._condicion(self._seccion(nodo, "CONDICION_UNTIL"))
            self.emitir(f"if_false {cond} goto {l_inicio};")

        elif tipo in ("Programa", "ListaDeclaracion", "ListaSentencias", "SeccionAST"):
            for hijo in nodo.get("children", []):
                self.sentencia(hijo)

        else:
            raise ErrorGeneracion(f"Nodo no soportado en código intermedio: {tipo}")

    # ------------------------------------------------------------------
    # Expresiones: devuelven la dirección (constante, variable o temporal)
    # ------------------------------------------------------------------

    def expresion(self, nodo: Nodo) -> str:
        tipo = nodo.get("type", "")

        if tipo == "Literal":
            literal = nodo.get("tipo_literal")
            valor = nodo.get("valor")
            if literal == "cadena":
                texto = texto_cadena(str(valor)).replace("\n", "\\n").replace("\t", "\\t")
                return f'"{texto}"'
            if literal == "booleano":
                return "true" if valor else "false"
            return str(valor)

        if tipo == "Identificador":
            return nodo["nombre"]

        if tipo == "ConversionTipo":
            origen = self.expresion(nodo["children"][0])
            t = self.nuevo_temporal()
            self.emitir(f"{t} = ({nodo.get('a', 'float')}) {origen};")
            return t

        if tipo == "OperacionUnaria":
            operando = self.expresion(nodo["children"][0])
            t = self.nuevo_temporal()
            self.emitir(f"{t} = {nodo.get('operador', '!')} {operando};")
            return t

        if tipo == "OperacionBinaria":
            izquierda = self.expresion(nodo["children"][0])
            derecha = self.expresion(nodo["children"][1])
            t = self.nuevo_temporal()
            self.emitir(f"{t} = {izquierda} {nodo.get('operador', '')} {derecha};")
            return t

        raise ErrorGeneracion(f"Expresión no soportada en código intermedio: {tipo}")


def generar_codigo_intermedio(arbol: Optional[Nodo], nombre_fuente: str = "",
                              encabezado: Optional[List[str]] = None) -> str:
    """Devuelve el texto del archivo .ci para el árbol anotado."""
    if not arbol:
        raise ErrorGeneracion("No hay árbol para generar código intermedio")
    gen = GeneradorIntermedio()
    gen.lineas.append("// Código intermedio de tres direcciones (CAOS)")
    if nombre_fuente:
        gen.lineas.append(f"// Archivo: {nombre_fuente}")
    for linea in encabezado or []:
        gen.lineas.append(f"// {linea}")
    gen.lineas.append("")
    gen.sentencia(arbol)
    gen.emitir("halt;")
    return "\n".join(gen.lineas) + "\n"

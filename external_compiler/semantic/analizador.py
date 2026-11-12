"""
analizador.py
-------------
Analizador semántico del lenguaje CAOS (Fase 3).

Entrada: el AST que entrega el parser como dict (ASTFormatter.to_binary).
Salida:  ResultadoSemantico con
    arbol_original   el AST tal como lo entregó el sintáctico (sin tocar)
    arbol_anotado    una COPIA del AST con las anotaciones semánticas
    tabla            la TablaSimbolos construida durante el recorrido
    errores          lista de ErrorSemantico, en orden de aparición
    traza            el recorrido semántico paso a paso (evidencia)

Recorrido
---------
Un solo recorrido del árbol, en el orden del programa. Así una variable usada
antes de su declaración se reporta como no declarada, y cada uso consulta la
tabla tal como está en ese punto del programa.

Dentro de ese recorrido se aplican los dos tipos de atributo:

* Heredado (dtype), en preorden: al visitar una declaración, el tipo se
  propaga hacia cada identificador declarado y se inserta en la tabla.
* Sintetizado (tipo y valor), en postorden: en una expresión primero se
  calculan los atributos de los hijos y con ellos los del padre.

Reglas de tipos
---------------
    + - * / ^     int,int -> int ; con un float -> float (int se convierte)
    %             int,int -> int
    < <= > >=     numéricos -> bool
    == !=         numérico con numérico, o bool con bool -> bool
    && ||  !      bool -> bool
    id = expr     mismo tipo; float <- int con conversión; int <- float es E4;
                  bool con numérico es E6
    id++ id--     int o float
    condiciones   bool (if, while, do-while, until)

La división entre enteros es entera y trunca hacia cero, como en C.

Atributo de valor
-----------------
Cada variable guarda en la tabla de símbolos su último valor conocido. Una
asignación compatible calcula el valor de la expresión y lo guarda; un
identificador usado en una expresión toma ("jala") ese valor de la tabla, de
modo que z = y + 7 se calcula con el valor actual de y.

Siguiendo la guía de la fase, el valor no se fuerza cuando no puede
determinarse en compilación:
    sin asignar, cin x           el valor queda desconocido
    if con condición conocida    solo la rama que se ejecuta cambia valores
    if con condición desconocida se analizan ambas ramas; una variable
                                 conserva su valor solo si ambas coinciden
    while / do-until             el cuerpo se anota con los valores de la
                                 primera iteración; como no se sabe cuántas
                                 veces se repite, las variables que cambian
                                 dentro del ciclo quedan desconocidas después
                                 (salvo que el while no se ejecute o el until
                                 se cumpla en la primera pasada)
Las ramas que no se ejecutan se verifican igual (tipos y errores), pero sus
asignaciones no modifican los valores de la tabla.
"""

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from . import tipos as T
from .errores import (
    E1_NO_DECLARADO, E2_DUPLICADO, E3_INCOMPATIBLES, E4_CONVERSION,
    E5_OPERADOR, E6_ASIGNACION, E7_CONDICION, ErrorSemantico,
)
from .tabla_simbolos import TablaSimbolos, funcion_hash

Nodo = Dict[str, Any]

# Etiquetas de las secciones de condición y la palabra reservada que las abre
_CONDICIONES = {
    "CONDICION": None,          # depende del padre: if | while
    "CONDICION_UNTIL": "until",
}


@dataclass
class ResultadoSemantico:
    arbol_original: Optional[Nodo]
    arbol_anotado: Optional[Nodo]
    tabla: TablaSimbolos
    errores: List[ErrorSemantico] = field(default_factory=list)
    traza: List[str] = field(default_factory=list)
    conversiones: int = 0


def analizar(ast: Optional[Nodo]) -> ResultadoSemantico:
    """Punto de entrada: analiza el AST (dict) y devuelve el resultado."""
    return AnalizadorSemantico().analizar(ast)


# ----------------------------------------------------------------------
# Utilidades de formato
# ----------------------------------------------------------------------

def formatear_valor(valor: Any) -> str:
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if isinstance(valor, float):
        texto = f"{valor:.6g}"
        if "." not in texto and "e" not in texto and "inf" not in texto:
            texto += ".0"
        return texto
    return str(valor)


def _posicion(nodo: Optional[Nodo]) -> Tuple[int, int]:
    if not nodo:
        return 0, 0
    return nodo.get("linea", 0), nodo.get("columna", 0)


def _dividir_entero(a: int, b: int) -> int:
    """División entera que trunca hacia cero (en Python // redondea hacia abajo)."""
    cociente = abs(a) // abs(b)
    return cociente if (a >= 0) == (b > 0) else -cociente


def _modulo_entero(a: int, b: int) -> int:
    """Residuo con el signo del dividendo, consistente con _dividir_entero."""
    return a - b * _dividir_entero(a, b)


def _plegar(operador: str, a: Any, b: Any, tipo_resultado: str) -> Any:
    """
    Calcula el valor de una operación cuando ambos operandos son constantes.
    Devuelve None cuando el valor no puede determinarse en compilación.
    """
    if a is None or b is None:
        return None
    try:
        if operador == "+":
            r = a + b
        elif operador == "-":
            r = a - b
        elif operador == "*":
            r = a * b
        elif operador == "/":
            if b == 0:
                return None
            r = _dividir_entero(a, b) if tipo_resultado == T.INT else a / b
        elif operador == "%":
            if b == 0:
                return None
            r = _modulo_entero(a, b)
        elif operador == "^":
            if tipo_resultado == T.INT and b < 0:
                return None
            r = a ** b
        elif operador == "<":
            return a < b
        elif operador == "<=":
            return a <= b
        elif operador == ">":
            return a > b
        elif operador == ">=":
            return a >= b
        elif operador == "==":
            return a == b
        elif operador == "!=":
            return a != b
        elif operador == "&&":
            return bool(a and b)
        elif operador == "||":
            return bool(a or b)
        else:
            return None
    except (OverflowError, ZeroDivisionError, ValueError):
        return None

    if tipo_resultado == T.FLOAT:
        return float(r)
    if tipo_resultado == T.INT:
        return int(r)
    return r


# ----------------------------------------------------------------------
# Analizador
# ----------------------------------------------------------------------

class AnalizadorSemantico:

    def __init__(self):
        self.tabla = TablaSimbolos()
        self.errores: List[ErrorSemantico] = []
        self.traza: List[str] = []
        self.conversiones = 0

    def analizar(self, ast: Optional[Nodo]) -> ResultadoSemantico:
        anotado = copy.deepcopy(ast) if ast else None
        if anotado:
            self._sentencia(anotado)
        return ResultadoSemantico(
            arbol_original=ast,
            arbol_anotado=anotado,
            tabla=self.tabla,
            errores=self.errores,
            traza=self.traza,
            conversiones=self.conversiones,
        )

    # ------------------------------------------------------------------
    # Registro de errores, traza y anotaciones
    # ------------------------------------------------------------------

    def _error(self, codigo: str, mensaje: str, nodo: Optional[Nodo],
               linea: int = 0, columna: int = 0) -> None:
        if not linea:
            linea, columna = _posicion(nodo)
        error = ErrorSemantico(codigo, mensaje, linea, columna)
        self.errores.append(error)
        self.traza.append(f"[{linea}:{columna}] ERROR {codigo}: {mensaje}")
        if nodo is not None:
            nodo.setdefault("errores_semanticos", []).append(codigo)

    def _paso(self, nodo: Optional[Nodo], accion: str, detalle: str) -> None:
        linea, columna = _posicion(nodo)
        self.traza.append(f"[{linea}:{columna}] {accion}: {detalle}")

    @staticmethod
    def _etiquetar(nodo: Nodo, partes: List[str]) -> None:
        """Agrega las anotaciones a la etiqueta conservando la original."""
        original = nodo.setdefault("label_sintactico", nodo.get("label", nodo.get("type", "")))
        errores = nodo.get("errores_semanticos")
        if errores:
            partes = partes + ["✗ " + " ".join(errores)]
        nodo["label"] = f"{original}  ⟨{', '.join(partes)}⟩" if partes else original

    def _anotar_expresion(self, nodo: Nodo, tipo: str, valor: Any,
                          extra: Optional[List[str]] = None) -> None:
        nodo["tipo_dato"] = tipo
        nodo["atributo_tipo"] = "sintetizado"
        partes = [f"tipo: {tipo}"]
        if valor is not None and tipo not in (T.ERROR, T.CADENA):
            nodo["valor_calculado"] = valor
            partes.append(f"valor: {formatear_valor(valor)}")
        self._etiquetar(nodo, partes + (extra or []))

    # ------------------------------------------------------------------
    # Valores de las variables (estado de la tabla en este punto)
    # ------------------------------------------------------------------

    def _valores(self) -> Dict[str, Any]:
        return {s.nombre: s.valor for s in self.tabla.simbolos()}

    def _restaurar(self, valores: Dict[str, Any]) -> None:
        for nombre, valor in valores.items():
            self.tabla.asignar_valor(nombre, valor)

    @staticmethod
    def _iguales(a: Any, b: Any) -> bool:
        return a is not None and type(a) is type(b) and a == b

    def _unir(self, rama_a: Dict[str, Any], rama_b: Dict[str, Any]) -> Dict[str, Any]:
        """Después de un if con condición desconocida: solo se conserva lo que coincide."""
        return {n: (v if self._iguales(v, rama_b.get(n)) else None) for n, v in rama_a.items()}

    def _invalidar_modificadas(self, nodo: Nodo, entrada: Dict[str, Any], motivo: str) -> None:
        """Las variables que cambiaron dentro del ciclo quedan sin valor conocido."""
        for nombre, valor in self._valores().items():
            if nombre in entrada and not self._iguales(valor, entrada[nombre]) \
                    and not (valor is None and entrada[nombre] is None):
                self.tabla.asignar_valor(nombre, None)
                self._paso(nodo, "VALOR", f"{nombre} queda sin valor conocido ({motivo})")

    def _no_ejecutada(self, seccion: Optional[Nodo], contexto: str, motivo: str) -> None:
        """Verifica una rama que no se ejecuta sin dejar que cambie los valores."""
        if not seccion:
            return
        self._paso(seccion, "RAMA NO EJECUTADA",
                   f"{motivo}; se verifica, pero sus asignaciones no cambian los valores")
        entrada = self._valores()
        self._sentencia(seccion, contexto)
        self._restaurar(entrada)
        seccion["ejecucion"] = "no se ejecuta"
        self._etiquetar(seccion, [f"no se ejecuta: {motivo}"])

    @staticmethod
    def _secciones(nodo: Nodo) -> Dict[str, Nodo]:
        return {
            h.get("label_sintactico", h.get("label")): h
            for h in nodo.get("children", []) if h.get("type") == "SeccionAST"
        }

    def _convertir(self, padre: Nodo, indice: int, destino: str, valor: Any) -> Any:
        """
        Envuelve el hijo indicado en un nodo ConversionTipo (int -> float).
        Así la conversión queda visible en el árbol anotado.
        """
        hijo = padre["children"][indice]
        origen = hijo.get("tipo_dato", T.INT)
        linea, columna = _posicion(hijo)
        valor_convertido = float(valor) if valor is not None else None
        nodo = {
            "type": "ConversionTipo",
            "label": f"CONVERSION: {origen} → {destino}",
            "linea": linea,
            "columna": columna,
            "de": origen,
            "a": destino,
            "children": [hijo],
        }
        self._anotar_expresion(nodo, destino, valor_convertido)
        padre["children"][indice] = nodo
        self.conversiones += 1
        self._paso(hijo, "CONVERSION",
                   f"{origen} → {destino} sobre '{hijo.get('label_sintactico', hijo.get('label'))}'")
        return valor_convertido

    # ------------------------------------------------------------------
    # Sentencias y estructura
    # ------------------------------------------------------------------

    def _sentencia(self, nodo: Optional[Nodo], contexto: Optional[str] = None) -> None:
        if not nodo:
            return
        tipo_nodo = nodo.get("type", "")

        if tipo_nodo == "DeclaracionVariable":
            self._declaracion(nodo)
        elif tipo_nodo == "Asignacion":
            self._asignacion(nodo)
        elif tipo_nodo == "IncrementoDecremento":
            self._incremento_decremento(nodo)
        elif tipo_nodo == "EntradaEstandar":
            self._entrada(nodo)
        elif tipo_nodo == "SalidaEstandar":
            self._salida(nodo)
        elif tipo_nodo == "Seleccion":
            self._seleccion(nodo)
        elif tipo_nodo == "Iteracion":
            self._iteracion(nodo)
        elif tipo_nodo == "Repeticion":
            self._repeticion(nodo)
        elif tipo_nodo == "SeccionAST" and nodo.get("label") in _CONDICIONES:
            self._condicion(nodo, contexto)
        else:
            # Programa, DECLARACIONES, BLOQUE, secciones de cuerpo, etc.
            for hijo in nodo.get("children", []):
                self._sentencia(hijo, contexto)

    # ------------------------------------------------------------------
    # Estructuras de control
    # ------------------------------------------------------------------

    def _seleccion(self, nodo: Nodo) -> None:
        """if condicion then ENTONCES [else SINO] end"""
        secciones = self._secciones(nodo)
        self._paso(nodo, "ESTRUCTURA", "IF (if)")
        _, valor = self._condicion(secciones.get("CONDICION"), "if")
        entonces, sino = secciones.get("ENTONCES"), secciones.get("SINO")

        if valor is True:
            self._sentencia(entonces, "if")
            self._no_ejecutada(sino, "if", "la condición del if es true")
            partes = ["condición true → se ejecuta ENTONCES"]
        elif valor is False:
            self._no_ejecutada(entonces, "if", "la condición del if es false")
            self._sentencia(sino, "if")
            partes = ["condición false → se ejecuta SINO" if sino else "condición false → no se ejecuta"]
        else:
            entrada = self._valores()
            self._sentencia(entonces, "if")
            despues_entonces = self._valores()
            self._restaurar(entrada)
            self._sentencia(sino, "if")
            self._restaurar(self._unir(despues_entonces, self._valores()))
            partes = ["condición sin valor conocido → se analizan ambas ramas"]
        self._etiquetar(nodo, partes)

    def _iteracion(self, nodo: Nodo) -> None:
        """while condicion CUERPO end"""
        secciones = self._secciones(nodo)
        self._paso(nodo, "ESTRUCTURA", "WHILE (while)")
        _, valor = self._condicion(secciones.get("CONDICION"), "while")
        cuerpo = secciones.get("CUERPO")

        if valor is False:
            self._no_ejecutada(cuerpo, "while", "la condición del while es false al llegar al ciclo")
            partes = ["condición inicial false → el cuerpo no se ejecuta"]
        else:
            entrada = self._valores()
            self._sentencia(cuerpo, "while")
            if cuerpo:
                self._etiquetar(cuerpo, ["valores de la primera iteración"])
            self._invalidar_modificadas(nodo, entrada, "cambia dentro del while")
            partes = ["número de iteraciones desconocido"]
        self._etiquetar(nodo, partes)

    def _repeticion(self, nodo: Nodo) -> None:
        """do CUERPO until condicion  (el cuerpo se ejecuta al menos una vez)"""
        secciones = self._secciones(nodo)
        self._paso(nodo, "ESTRUCTURA", "DO_UNTIL (do)")
        cuerpo = secciones.get("CUERPO")
        entrada = self._valores()
        self._sentencia(cuerpo, "do")
        _, valor = self._condicion(secciones.get("CONDICION_UNTIL"), "until")

        if valor is True:
            partes = ["until true en la primera pasada → se ejecuta una vez"]
        else:
            if cuerpo:
                self._etiquetar(cuerpo, ["valores de la primera iteración"])
            self._invalidar_modificadas(nodo, entrada, "cambia dentro del do-until")
            partes = ["número de iteraciones desconocido"]
        self._etiquetar(nodo, partes)

    def _declaracion(self, nodo: Nodo) -> None:
        """
        declaracion_variable -> tipo id {, id} ;
        Atributo heredado: id.dtype = tipo.dtype, para cada identificador.
        """
        dtype = nodo.get("tipo", "")
        nodo["dtype"] = dtype
        identificadores = nodo.get("identificadores", [])
        nombres = ", ".join(i.get("nombre", "") for i in identificadores)
        self._paso(nodo, "DECLARACION", f"dtype = {dtype} se hereda a: {nombres}")

        hijos = []
        for ident in identificadores:
            nombre = ident.get("nombre", "")
            linea, columna = ident.get("linea", 0), ident.get("columna", 0)
            hijo = {
                "type": "IdentificadorDeclarado",
                "label": f"ID: {nombre}",
                "linea": linea,
                "columna": columna,
                "nombre_declarado": nombre,
                "dtype": dtype,
                "atributo_tipo": "heredado",
                "children": [],
            }
            previo = self.tabla.buscar(nombre)
            if previo is not None:
                self.tabla.agregar_linea(nombre, linea)
                self._error(
                    E2_DUPLICADO,
                    f"'{nombre}' ya fue declarada en la línea {previo.linea_decl}",
                    hijo,
                )
                self._etiquetar(hijo, [f"dtype: {dtype} (heredado)"])
            else:
                simbolo = self.tabla.insertar(nombre, dtype, linea, columna)
                hijo["loc"] = simbolo.loc
                self._paso(hijo, "INSERTAR",
                           f"{nombre} → tipo {dtype}, loc {simbolo.loc}, hash {funcion_hash(nombre)}")
                self._etiquetar(hijo, [f"dtype: {dtype} (heredado)", f"loc: {simbolo.loc}"])
            hijos.append(hijo)

        nodo["children"] = hijos
        self._etiquetar(nodo, [f"dtype: {dtype}"])

    def _buscar(self, nombre: str, nodo: Optional[Nodo], linea: int = 0, columna: int = 0):
        """Búsqueda en la tabla. Registra la línea de uso o el error E1."""
        if not linea:
            linea, columna = _posicion(nodo)
        simbolo = self.tabla.buscar(nombre)
        if simbolo is None:
            self.traza.append(f"[{linea}:{columna}] BUSCAR: {nombre} → no está en la tabla")
            self._error(E1_NO_DECLARADO, f"'{nombre}' no está declarada", nodo, linea, columna)
            return None
        self.tabla.agregar_linea(nombre, linea)
        valor = formatear_valor(simbolo.valor) if simbolo.valor is not None else "desconocido"
        self.traza.append(
            f"[{linea}:{columna}] BUSCAR: {nombre} → tipo {simbolo.tipo}, loc {simbolo.loc}, valor {valor}")
        return simbolo

    def _guardar_valor(self, nodo: Nodo, nombre: str, valor: Any) -> List[str]:
        """Guarda el valor en la tabla y devuelve la anotación para la etiqueta."""
        self.tabla.asignar_valor(nombre, valor)
        if valor is None:
            nodo.pop("valor_asignado", None)
            self._paso(nodo, "VALOR", f"{nombre} ← desconocido")
            return ["valor: desconocido"]
        nodo["valor_asignado"] = valor
        self._paso(nodo, "VALOR", f"{nombre} ← {formatear_valor(valor)}")
        return [f"valor: {formatear_valor(valor)}"]

    def _asignacion(self, nodo: Nodo) -> None:
        """id = expresion ; se compara el tipo de id con el de la expresión."""
        nombre = nodo.get("identificador", "")
        simbolo = self._buscar(nombre, nodo)

        hijos = nodo.get("children", [])
        tipo_expr, valor = (T.ERROR, None)
        if hijos:
            tipo_expr, valor = self._expresion(hijos[0])

        if simbolo is None:
            self._etiquetar(nodo, ["destino no declarado"])
            return

        destino = simbolo.tipo
        nodo["tipo_dato"] = destino
        nodo["tipo_expresion"] = tipo_expr
        partes = [f"{nombre}: {destino}", f"expresión: {tipo_expr}"]

        if tipo_expr == T.ERROR or not hijos:
            self._etiquetar(nodo, partes)
            return

        if tipo_expr == destino:
            nodo["verificacion"] = "compatible"
            self._paso(nodo, "ASIGNACION", f"{nombre}: {destino} ← {tipo_expr} (compatible)")
            partes += self._guardar_valor(nodo, nombre, valor)
        elif T.conversion_permitida(tipo_expr, destino):
            valor = self._convertir(nodo, 0, destino, valor)
            nodo["verificacion"] = "conversion"
            partes.append(f"conversión {tipo_expr} → {destino}")
            self._paso(nodo, "ASIGNACION",
                       f"{nombre}: {destino} ← {tipo_expr} (conversión implícita)")
            partes += self._guardar_valor(nodo, nombre, valor)
        elif destino == T.INT and tipo_expr == T.FLOAT:
            nodo["verificacion"] = "error"
            self._error(
                E4_CONVERSION,
                f"No se puede asignar un valor float a '{nombre}', que es int "
                f"(la conversión float → int no está permitida)",
                nodo,
            )
        else:
            nodo["verificacion"] = "error"
            self._error(
                E6_ASIGNACION,
                f"No se puede asignar un valor {tipo_expr} a '{nombre}', que es {destino}",
                nodo,
            )
        self._etiquetar(nodo, partes)

    def _incremento_decremento(self, nodo: Nodo) -> None:
        nombre = nodo.get("identificador", "")
        operador = nodo.get("operador", "++")
        simbolo = self._buscar(nombre, nodo)
        if simbolo is None:
            self._etiquetar(nodo, ["no declarado"])
            return
        nodo["tipo_dato"] = simbolo.tipo
        if not T.es_numerico(simbolo.tipo):
            self._error(
                E5_OPERADOR,
                f"El operador '{operador}' requiere una variable int o float; '{nombre}' es {simbolo.tipo}",
                nodo,
            )
            self._etiquetar(nodo, [f"tipo: {simbolo.tipo}"])
            return
        self._paso(nodo, "INCREMENTO" if operador == "++" else "DECREMENTO",
                   f"{nombre}{operador} sobre {simbolo.tipo} (válido)")
        nuevo = None
        if simbolo.valor is not None:
            nuevo = simbolo.valor + (1 if operador == "++" else -1)
        self._etiquetar(nodo, [f"tipo: {simbolo.tipo}"] + self._guardar_valor(nodo, nombre, nuevo))

    def _entrada(self, nodo: Nodo) -> None:
        nombre = nodo.get("identificador", "")
        linea = nodo.get("identificador_linea") or nodo.get("linea", 0)
        columna = nodo.get("identificador_columna") or nodo.get("columna", 0)
        simbolo = self._buscar(nombre, nodo, linea, columna)
        if simbolo is None:
            self._etiquetar(nodo, ["no declarado"])
            return
        nodo["tipo_dato"] = simbolo.tipo
        # El valor se conoce hasta la ejecución
        self.tabla.asignar_valor(nombre, None)
        self._paso(nodo, "VALOR", f"{nombre} se lee con cin → valor desconocido en compilación")
        self._etiquetar(nodo, [f"tipo: {simbolo.tipo}", "valor: se lee en ejecución"])

    def _salida(self, nodo: Nodo) -> None:
        for salida in nodo.get("children", []):
            for elemento in salida.get("children", []):
                self._expresion(elemento)

    def _condicion(self, seccion: Optional[Nodo], contexto: Optional[str]) -> Tuple[str, Any]:
        """
        La expresión de una condición debe ser bool (E7).
        Devuelve (tipo, valor); el valor es None si no se conoce en compilación.
        """
        if not seccion:
            return T.ERROR, None
        etiqueta = seccion.get("label_sintactico", seccion.get("label"))
        palabra = _CONDICIONES.get(etiqueta) or contexto or "condición"
        hijos = seccion.get("children", [])
        if not hijos:
            return T.ERROR, None
        expresion = hijos[0]
        tipo, valor = self._expresion(expresion)
        seccion["tipo_requerido"] = T.BOOL
        if tipo not in (T.BOOL, T.ERROR):
            self._error(
                E7_CONDICION,
                f"La condición de '{palabra}' debe ser bool y es {tipo}",
                expresion,
            )
            self._anotar_expresion(expresion, tipo, valor)
        elif tipo == T.BOOL:
            detalle = f", valor {formatear_valor(valor)}" if valor is not None else ""
            self._paso(expresion, "CONDICION", f"'{palabra}' es bool (válida){detalle}")
        partes = ["requiere: bool", f"obtenido: {tipo}"]
        if tipo == T.BOOL:
            partes.append(f"valor: {formatear_valor(valor)}" if valor is not None
                          else "valor: desconocido")
        self._etiquetar(seccion, partes)
        return tipo, (valor if tipo == T.BOOL else None)

    # ------------------------------------------------------------------
    # Expresiones (atributos sintetizados: tipo y valor)
    # ------------------------------------------------------------------

    def _expresion(self, nodo: Optional[Nodo]) -> Tuple[str, Any]:
        if not nodo:
            return T.ERROR, None
        tipo_nodo = nodo.get("type", "")

        if tipo_nodo == "Literal":
            tipo = T.TIPO_DE_LITERAL.get(nodo.get("tipo_literal", ""), T.ERROR)
            valor = nodo.get("valor") if tipo != T.CADENA else None
            if tipo == T.FLOAT and valor is not None:
                valor = float(valor)
            self._anotar_expresion(nodo, tipo, valor)
            return tipo, valor

        if tipo_nodo == "Identificador":
            nombre = nodo.get("nombre", "")
            simbolo = self._buscar(nombre, nodo)
            if simbolo is None:
                self._anotar_expresion(nodo, T.ERROR, None)
                return T.ERROR, None
            # El identificador toma su valor actual de la tabla de símbolos
            nodo["loc"] = simbolo.loc
            valor = simbolo.valor
            extra = [f"loc: {simbolo.loc}"]
            if valor is None:
                extra.insert(0, "valor: desconocido")
            self._anotar_expresion(nodo, simbolo.tipo, valor, extra)
            return simbolo.tipo, valor

        if tipo_nodo == "OperacionUnaria":
            return self._unaria(nodo)

        if tipo_nodo == "OperacionBinaria":
            return self._binaria(nodo)

        # NodoError u otro nodo inesperado: ya fue reportado por el sintáctico
        nodo["tipo_dato"] = T.ERROR
        return T.ERROR, None

    def _unaria(self, nodo: Nodo) -> Tuple[str, Any]:
        operador = nodo.get("operador", "!")
        hijos = nodo.get("children", [])
        tipo, valor = self._expresion(hijos[0]) if hijos else (T.ERROR, None)
        if tipo == T.ERROR:
            self._anotar_expresion(nodo, T.ERROR, None)
            return T.ERROR, None
        if tipo != T.BOOL:
            self._error(E5_OPERADOR,
                        f"El operador '{operador}' requiere un operando bool y recibió {tipo}", nodo)
            self._anotar_expresion(nodo, T.ERROR, None)
            return T.ERROR, None
        resultado = (not valor) if valor is not None else None
        self._anotar_expresion(nodo, T.BOOL, resultado)
        self._paso(nodo, "TIPO", f"{operador} bool → bool")
        return T.BOOL, resultado

    def _binaria(self, nodo: Nodo) -> Tuple[str, Any]:
        operador = nodo.get("operador", "")
        hijos = nodo.get("children", [])
        if len(hijos) < 2:
            for hijo in hijos:
                self._expresion(hijo)
            self._anotar_expresion(nodo, T.ERROR, None)
            return T.ERROR, None

        # Postorden: primero los hijos
        ti, vi = self._expresion(hijos[0])
        td, vd = self._expresion(hijos[1])

        if T.ERROR in (ti, td):
            self._anotar_expresion(nodo, T.ERROR, None)
            return T.ERROR, None

        resultado: Optional[str] = None

        if operador in T.ARITMETICOS or operador == T.MODULO:
            if not (T.es_numerico(ti) and T.es_numerico(td)):
                self._error(E5_OPERADOR,
                            f"El operador '{operador}' no se puede aplicar a {ti} y {td}", nodo)
            elif operador == T.MODULO and T.FLOAT in (ti, td):
                self._error(E5_OPERADOR,
                            f"El operador '%' requiere operandos int y recibió {ti} y {td}", nodo)
            else:
                resultado = T.tipo_aritmetico(ti, td)
                vi, vd = self._igualar(nodo, ti, td, vi, vd)

        elif operador in T.RELACIONALES:
            if not (T.es_numerico(ti) and T.es_numerico(td)):
                self._error(E5_OPERADOR,
                            f"El operador '{operador}' requiere operandos numéricos y recibió {ti} y {td}",
                            nodo)
            else:
                resultado = T.BOOL
                vi, vd = self._igualar(nodo, ti, td, vi, vd)

        elif operador in T.IGUALDAD:
            if T.es_numerico(ti) and T.es_numerico(td):
                resultado = T.BOOL
                vi, vd = self._igualar(nodo, ti, td, vi, vd)
            elif ti == td == T.BOOL:
                resultado = T.BOOL
            else:
                self._error(E3_INCOMPATIBLES,
                            f"No se pueden comparar con '{operador}' operandos de tipo {ti} y {td}",
                            nodo)

        elif operador in T.LOGICOS_BINARIOS:
            if ti == td == T.BOOL:
                resultado = T.BOOL
            else:
                self._error(E5_OPERADOR,
                            f"El operador '{operador}' requiere operandos bool y recibió {ti} y {td}",
                            nodo)

        if resultado is None:
            self._anotar_expresion(nodo, T.ERROR, None)
            return T.ERROR, None

        valor = _plegar(operador, vi, vd, resultado)
        self._anotar_expresion(nodo, resultado, valor)
        detalle = f"{ti} {operador} {td} → {resultado}"
        if valor is not None:
            detalle += f", valor {formatear_valor(valor)}"
        self._paso(nodo, "TIPO", detalle)
        return resultado, valor

    def _igualar(self, nodo: Nodo, ti: str, td: str, vi: Any, vd: Any) -> Tuple[Any, Any]:
        """Si un operando es int y el otro float, convierte el int a float."""
        if ti == T.INT and td == T.FLOAT:
            vi = self._convertir(nodo, 0, T.FLOAT, vi)
        elif ti == T.FLOAT and td == T.INT:
            vd = self._convertir(nodo, 1, T.FLOAT, vd)
        return vi, vd

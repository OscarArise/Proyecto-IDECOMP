"""
cgen.py
-------
Generador de código TM del compilador CAOS. Port de cgen.c del compilador
TINY (Louden), adaptado al árbol anotado que produce el análisis semántico.

Entrada:
    arbol   el árbol anotado (ResultadoSemantico.arbol_anotado), ya validado:
            solo se genera código si el análisis no reportó errores.
    tabla   la TablaSimbolos; tabla.buscar(nombre).loc cumple el papel de
            st_lookup(nombre) en TINY: el desplazamiento de la variable
            respecto de gp.
Salida:
    el texto del archivo .tm

Correspondencia de nodos CAOS -> TINY
    Asignacion            AssignK
    EntradaEstandar       ReadK    (IN para int/bool, INF para float)
    SalidaEstandar        WriteK   (OUT, OUTF u OUTS por elemento y OUTLN)
    Seleccion             IfK      (else opcional)
    Repeticion            RepeatK  (do ... until)
    Iteracion             nuevo    (while)
    IncrementoDecremento  nuevo    (id++ / id--)
    Literal               ConstK
    Identificador         IdK
    OperacionBinaria      OpK      (+ - * / % ^ < <= > >= == != && ||)
    OperacionUnaria       nuevo    (!)
    ConversionTipo        nuevo    (int -> float; la TM extendida usa reales)

El árbol no se modifica: el generador solo lo recorre.
"""

from typing import Any, Dict, List, Optional

from .code import Emisor, ac, ac1, gp, mp, pc

Nodo = Dict[str, Any]

# Registro auxiliar para '%' (a - (a/b)*b). TINY solo usa ac y ac1; el
# registro 2 queda libre en la convención de code.h.
ac2 = 2

# Límites de la TM extendida (tm/tm.c y tm/tm.py)
IADDR_SIZE = 8192
DADDR_SIZE = 4096

# Salto que hace verdadera la comparación ac = izquierdo - derecho
_SALTO_RELACIONAL = {
    "<": "JLT",
    "<=": "JLE",
    ">": "JGT",
    ">=": "JGE",
    "==": "JEQ",
    "!=": "JNE",
}

_ARITMETICOS = {"+": "ADD", "-": "SUB", "*": "MUL"}


class ErrorGeneracion(Exception):
    """Construcción que no puede traducirse a TM."""


def _etiqueta(nodo: Nodo) -> str:
    return nodo.get("label_sintactico", nodo.get("label", ""))


def texto_cadena(lexema: str) -> str:
    """Contenido de un literal de cadena: sin comillas y con \\n y \\t interpretados."""
    if len(lexema) >= 2 and lexema[0] == lexema[-1] == '"':
        lexema = lexema[1:-1]
    return lexema.replace("\\n", "\n").replace("\\t", "\t")


class GeneradorTM:
    """Estado del recorrido: emisor, tabla y desplazamiento de temporales."""

    def __init__(self, tabla, trace_code: bool = True):
        self.tabla = tabla
        self.emisor = Emisor(trace_code)
        # tmpOffset: desplazamiento de los temporales respecto de mp.
        # Se decrementa al guardar un temporal y se incrementa al recuperarlo.
        self.tmp_offset = 0
        self.cadenas: Dict[str, int] = {}  # texto -> dirección en dMem

    # ------------------------------------------------------------------
    # Tabla de símbolos
    # ------------------------------------------------------------------

    def st_lookup(self, nombre: str) -> int:
        simbolo = self.tabla.buscar(nombre)
        if simbolo is None:
            raise ErrorGeneracion(f"'{nombre}' no está en la tabla de símbolos")
        return simbolo.loc

    def tipo_de(self, nombre: str) -> str:
        simbolo = self.tabla.buscar(nombre)
        return simbolo.tipo if simbolo else ""

    # ------------------------------------------------------------------
    # Cadenas de cout: se guardan en dMem después de las variables
    # ------------------------------------------------------------------

    def _reunir_cadenas(self, nodo: Optional[Nodo], destino: List[str]) -> None:
        if not nodo:
            return
        if nodo.get("type") == "Literal" and nodo.get("tipo_literal") == "cadena":
            texto = texto_cadena(str(nodo.get("valor", "")))
            if texto not in destino:
                destino.append(texto)
        for hijo in nodo.get("children", []):
            self._reunir_cadenas(hijo, destino)

    def _cargar_cadenas(self, arbol: Nodo) -> None:
        textos: List[str] = []
        self._reunir_cadenas(arbol, textos)
        if not textos:
            return
        e = self.emisor
        siguiente = max((s.loc for s in self.tabla.simbolos()), default=-1) + 1
        e.emit_comment("Cadenas de cout en memoria de datos (bytes UTF-8, terminadas en 0):")
        for texto in textos:
            datos = texto.encode("utf-8")
            if siguiente + len(datos) + 1 >= DADDR_SIZE // 2:
                raise ErrorGeneracion("Las cadenas de cout no caben en la memoria de datos de la TM")
            self.cadenas[texto] = siguiente
            e.emit_comment(f"cadena {texto!r} en {siguiente}({gp})")
            for i, byte in enumerate(datos):
                e.emit_rm("LDC", ac, byte, 0, f"caracter {chr(byte)!r}" if byte < 128 else "byte")
                e.emit_rm("ST", ac, siguiente + i, gp, "guardar caracter")
            siguiente += len(datos) + 1  # el 0 final ya está en la memoria
        e.emit_comment("Fin de cadenas.")

    # ------------------------------------------------------------------
    # Recorrido
    # ------------------------------------------------------------------

    def c_gen(self, nodo: Optional[Nodo]) -> None:
        """Recorre el nodo: sentencia, expresión o contenedor (Programa, BLOQUE, secciones)."""
        if not nodo:
            return
        tipo = nodo.get("type", "")
        if tipo in _SENTENCIAS:
            self.gen_stmt(nodo)
        elif tipo in _EXPRESIONES:
            self.gen_exp(nodo)
        elif tipo == "DeclaracionVariable":
            for hijo in nodo.get("children", []):
                nombre = hijo.get("nombre_declarado", "")
                self.emisor.emit_comment(
                    f"declaracion: {nombre} ({hijo.get('dtype', '')}) -> loc {self.st_lookup(nombre)}({gp})"
                )
        elif tipo in ("Programa", "ListaDeclaracion", "ListaSentencias", "SeccionAST"):
            # En TINY los hermanos se recorren con 'sibling'; aquí son la lista de hijos
            for hijo in nodo.get("children", []):
                self.c_gen(hijo)
        else:
            raise ErrorGeneracion(f"Nodo no soportado en TM: {tipo or '?'} ({_etiqueta(nodo)})")

    @staticmethod
    def _seccion(nodo: Nodo, nombre: str) -> Optional[Nodo]:
        for hijo in nodo.get("children", []):
            if hijo.get("type") == "SeccionAST" and _etiqueta(hijo) == nombre:
                return hijo
        return None

    # ------------------------------------------------------------------
    # Sentencias (genStmt)
    # ------------------------------------------------------------------

    def gen_stmt(self, nodo: Nodo) -> None:
        e = self.emisor
        tipo = nodo["type"]

        if tipo == "Seleccion":
            e.emit_comment("-> if")
            p1 = self._seccion(nodo, "CONDICION")
            p2 = self._seccion(nodo, "ENTONCES")
            p3 = self._seccion(nodo, "SINO")
            # código de la condición
            self.c_gen(p1)
            saved_loc1 = e.emit_skip(1)
            e.emit_comment("if: jump to else belongs here")
            # parte then
            self.c_gen(p2)
            saved_loc2 = e.emit_skip(1)
            e.emit_comment("if: jump to end belongs here")
            current_loc = e.emit_skip(0)
            e.emit_backup(saved_loc1)
            e.emit_rm_abs("JEQ", ac, current_loc, "if: jmp to else")
            e.emit_restore()
            # parte else
            self.c_gen(p3)
            current_loc = e.emit_skip(0)
            e.emit_backup(saved_loc2)
            e.emit_rm_abs("LDA", pc, current_loc, "jmp to end")
            e.emit_restore()
            e.emit_comment("<- if")

        elif tipo == "Repeticion":
            e.emit_comment("-> do-until")
            p1 = self._seccion(nodo, "CUERPO")
            p2 = self._seccion(nodo, "CONDICION_UNTIL")
            saved_loc1 = e.emit_skip(0)
            e.emit_comment("do: jump after body comes back here")
            self.c_gen(p1)
            self.c_gen(p2)
            e.emit_rm_abs("JEQ", ac, saved_loc1, "until: jmp back to body")
            e.emit_comment("<- do-until")

        elif tipo == "Iteracion":
            e.emit_comment("-> while")
            p1 = self._seccion(nodo, "CONDICION")
            p2 = self._seccion(nodo, "CUERPO")
            saved_loc1 = e.emit_skip(0)
            e.emit_comment("while: jump after body comes back here")
            self.c_gen(p1)
            saved_loc2 = e.emit_skip(1)
            e.emit_comment("while: jump to end belongs here")
            self.c_gen(p2)
            e.emit_rm_abs("LDA", pc, saved_loc1, "while: jmp back to test")
            current_loc = e.emit_skip(0)
            e.emit_backup(saved_loc2)
            e.emit_rm_abs("JEQ", ac, current_loc, "while: jmp to end")
            e.emit_restore()
            e.emit_comment("<- while")

        elif tipo == "Asignacion":
            e.emit_comment("-> assign")
            hijos = nodo.get("children", [])
            if not hijos:
                raise ErrorGeneracion(f"Asignación sin expresión a '{nodo.get('identificador')}'")
            self.c_gen(hijos[0])
            loc = self.st_lookup(nodo["identificador"])
            e.emit_rm("ST", ac, loc, gp, "assign: store value")
            e.emit_comment("<- assign")

        elif tipo == "IncrementoDecremento":
            nombre = nodo["identificador"]
            operador = nodo.get("operador", "++")
            e.emit_comment(f"-> {nombre}{operador}")
            loc = self.st_lookup(nombre)
            e.emit_rm("LD", ac, loc, gp, "load id value")
            e.emit_rm("LDC", ac1, 1, 0, "load const 1")
            e.emit_ro("ADD" if operador == "++" else "SUB", ac, ac, ac1, f"op {operador}")
            e.emit_rm("ST", ac, loc, gp, f"{operador}: store value")
            e.emit_comment(f"<- {nombre}{operador}")

        elif tipo == "EntradaEstandar":
            nombre = nodo["identificador"]
            tipo_dato = self.tipo_de(nombre)
            if tipo_dato == "float":
                e.emit_ro("INF", ac, 0, 0, "read real value")
            else:
                e.emit_ro("IN", ac, 0, 0, "read integer value")
                if tipo_dato == "bool":
                    e.emit_rm("JEQ", ac, 1, pc, "bool: 0 stays false")
                    e.emit_rm("LDC", ac, 1, 0, "bool: nonzero is true")
            loc = self.st_lookup(nombre)
            e.emit_rm("ST", ac, loc, gp, "read: store value")

        elif tipo == "SalidaEstandar":
            e.emit_comment("-> cout")
            for salida in nodo.get("children", []):
                for elemento in salida.get("children", []):
                    self._gen_elemento_salida(elemento)
            e.emit_ro("OUTLN", 0, 0, 0, "end of cout line")
            e.emit_comment("<- cout")

    def _gen_elemento_salida(self, elemento: Nodo) -> None:
        e = self.emisor
        if elemento.get("type") == "Literal" and elemento.get("tipo_literal") == "cadena":
            texto = texto_cadena(str(elemento.get("valor", "")))
            e.emit_rm("OUTS", ac, self.cadenas[texto], gp, f"write string {texto!r}")
            return
        self.c_gen(elemento)
        if elemento.get("tipo_dato") == "float":
            e.emit_ro("OUTF", ac, 0, 0, "write real ac")
        else:
            e.emit_ro("OUT", ac, 0, 0, "write ac")

    # ------------------------------------------------------------------
    # Expresiones (genExp)
    # ------------------------------------------------------------------

    def gen_exp(self, nodo: Nodo) -> None:
        e = self.emisor
        tipo = nodo["type"]

        if tipo == "Literal":
            e.emit_comment("-> Const")
            valor = nodo.get("valor")
            if nodo.get("tipo_literal") == "booleano":
                valor = 1 if valor else 0
            elif nodo.get("tipo_dato") == "float":
                valor = float(valor)
            e.emit_rm("LDC", ac, valor, 0, "load const")
            e.emit_comment("<- Const")

        elif tipo == "Identificador":
            e.emit_comment("-> Id")
            loc = self.st_lookup(nodo["nombre"])
            e.emit_rm("LD", ac, loc, gp, f"load id value ({nodo['nombre']})")
            e.emit_comment("<- Id")

        elif tipo == "ConversionTipo":
            e.emit_comment(f"-> Conversion {nodo.get('de')} -> {nodo.get('a')} (la TM usa reales)")
            self.c_gen(nodo["children"][0])
            e.emit_comment("<- Conversion")

        elif tipo == "OperacionUnaria":
            e.emit_comment("-> Op !")
            self.c_gen(nodo["children"][0])
            e.emit_rm("JEQ", ac, 2, pc, "br if false")
            e.emit_rm("LDC", ac, 0, ac, "true case -> 0")
            e.emit_rm("LDA", pc, 1, pc, "unconditional jmp")
            e.emit_rm("LDC", ac, 1, ac, "false case -> 1")
            e.emit_comment("<- Op !")

        elif tipo == "OperacionBinaria":
            operador = nodo.get("operador", "")
            if operador in ("&&", "||"):
                self._gen_logico(nodo, operador)
                return
            e.emit_comment(f"-> Op {operador}")
            p1, p2 = nodo["children"][0], nodo["children"][1]
            # ac = operando izquierdo
            self.c_gen(p1)
            # guardar el operando izquierdo
            e.emit_rm("ST", ac, self.tmp_offset, mp, "op: push left")
            self.tmp_offset -= 1
            # ac = operando derecho
            self.c_gen(p2)
            # recuperar el operando izquierdo en ac1
            self.tmp_offset += 1
            e.emit_rm("LD", ac1, self.tmp_offset, mp, "op: load left")
            self._gen_operador(nodo, operador)
            e.emit_comment(f"<- Op {operador}")

        else:
            raise ErrorGeneracion(f"Expresión no soportada en TM: {tipo} ({_etiqueta(nodo)})")

    def _gen_operador(self, nodo: Nodo, operador: str) -> None:
        """ac1 = izquierdo, ac = derecho; deja el resultado en ac."""
        e = self.emisor
        tipo_resultado = nodo.get("tipo_dato")
        if operador in _ARITMETICOS:
            e.emit_ro(_ARITMETICOS[operador], ac, ac1, ac, f"op {operador}")
        elif operador == "/":
            if tipo_resultado == "float":
                e.emit_ro("DIVF", ac, ac1, ac, "op / (real)")
            else:
                e.emit_ro("DIV", ac, ac1, ac, "op / (entera)")
        elif operador == "%":
            e.emit_ro("DIV", ac2, ac1, ac, "op %: q = a / b")
            e.emit_ro("MUL", ac2, ac2, ac, "op %: q * b")
            e.emit_ro("SUB", ac, ac1, ac2, "op %: a - q * b")
        elif operador == "^":
            e.emit_ro("POW", ac, ac1, ac, "op ^")
            if tipo_resultado == "int":
                e.emit_rm("LDC", ac1, 1, 0, "op ^: int result")
                e.emit_ro("DIV", ac, ac, ac1, "op ^: truncate")
        elif operador in _SALTO_RELACIONAL:
            e.emit_ro("SUB", ac, ac1, ac, f"op {operador}")
            e.emit_rm(_SALTO_RELACIONAL[operador], ac, 2, pc, "br if true")
            e.emit_rm("LDC", ac, 0, ac, "false case")
            e.emit_rm("LDA", pc, 1, pc, "unconditional jmp")
            e.emit_rm("LDC", ac, 1, ac, "true case")
        else:
            raise ErrorGeneracion(f"Operador no soportado en TM: '{operador}'")

    def _gen_logico(self, nodo: Nodo, operador: str) -> None:
        """&& y || con cortocircuito; los saltos se completan con backpatch."""
        e = self.emisor
        es_and = operador == "&&"
        salto = "JEQ" if es_and else "JNE"
        e.emit_comment(f"-> Op {operador}")
        self.c_gen(nodo["children"][0])
        saved_loc1 = e.emit_skip(1)
        e.emit_comment(f"{operador}: short-circuit jump belongs here")
        self.c_gen(nodo["children"][1])
        saved_loc2 = e.emit_skip(1)
        e.emit_rm("LDC", ac, 1 if es_and else 0, ac, "both true" if es_and else "both false")
        e.emit_rm("LDA", pc, 1, pc, "unconditional jmp")
        destino = e.emit_skip(0)
        e.emit_rm("LDC", ac, 0 if es_and else 1, ac, "short-circuit result")
        for saved in (saved_loc1, saved_loc2):
            e.emit_backup(saved)
            e.emit_rm_abs(salto, ac, destino, f"{operador}: short-circuit")
            e.emit_restore()
        e.emit_comment(f"<- Op {operador}")


_SENTENCIAS = {
    "Seleccion", "Repeticion", "Iteracion", "Asignacion",
    "IncrementoDecremento", "EntradaEstandar", "SalidaEstandar",
}
_EXPRESIONES = {
    "Literal", "Identificador", "ConversionTipo", "OperacionUnaria", "OperacionBinaria",
}


def code_gen(arbol: Optional[Nodo], tabla, codefile: str,
             encabezado: Optional[List[str]] = None, trace_code: bool = True) -> str:
    """
    Genera el programa TM recorriendo el árbol anotado (codeGen de TINY).
    `codefile` se escribe como comentario; `encabezado` agrega comentarios extra.
    Lanza ErrorGeneracion si encuentra algo que no puede traducir.
    """
    if not arbol:
        raise ErrorGeneracion("No hay árbol para generar código")
    gen = GeneradorTM(tabla, trace_code)
    e = gen.emisor
    e.emit_comment("CAOS Compilation to TM Code")
    e.emit_comment(f"File: {codefile}")
    for linea in encabezado or []:
        e.emit_comment(linea)
    # prelude estándar
    e.emit_comment("Standard prelude:")
    e.emit_rm("LD", mp, 0, ac, "load maxaddress from location 0")
    e.emit_rm("ST", ac, 0, ac, "clear location 0")
    e.emit_comment("End of standard prelude.")
    gen._cargar_cadenas(arbol)
    # código del programa CAOS
    gen.c_gen(arbol)
    # fin
    e.emit_comment("End of execution.")
    e.emit_ro("HALT", 0, 0, 0, "")
    if e.high_emit_loc > IADDR_SIZE:
        raise ErrorGeneracion(
            f"El programa necesita {e.high_emit_loc} instrucciones y la TM admite {IADDR_SIZE}"
        )
    return e.texto()

"""
errores.py
----------
Errores semánticos del lenguaje CAOS (sección 8 de la guía de la Fase 3).

    E1  Uso de un identificador no declarado
    E2  Declaración duplicada dentro del ámbito
    E3  Incompatibilidad de tipos entre operandos
    E4  Conversión de tipos no válida
    E5  Operador no aplicable a los tipos de sus operandos
    E6  Inconsistencia de tipos en una asignación
    E7  La condición de una estructura de control no es booleana
"""

from dataclasses import dataclass

E1_NO_DECLARADO = "E1"
E2_DUPLICADO = "E2"
E3_INCOMPATIBLES = "E3"
E4_CONVERSION = "E4"
E5_OPERADOR = "E5"
E6_ASIGNACION = "E6"
E7_CONDICION = "E7"

DESCRIPCIONES = {
    E1_NO_DECLARADO: "Identificador no declarado",
    E2_DUPLICADO: "Declaración duplicada",
    E3_INCOMPATIBLES: "Tipos incompatibles",
    E4_CONVERSION: "Conversión de tipos no válida",
    E5_OPERADOR: "Operador no aplicable a los tipos",
    E6_ASIGNACION: "Inconsistencia de tipos en asignación",
    E7_CONDICION: "Condición no booleana",
}


@dataclass
class ErrorSemantico:
    codigo: str
    mensaje: str
    linea: int = 0
    columna: int = 0

    @property
    def descripcion(self) -> str:
        return DESCRIPCIONES.get(self.codigo, "")

    def __str__(self) -> str:
        # Mismo formato que los errores sintácticos: "[l:c] Error ...: mensaje"
        prefijo = f"[{self.linea}:{self.columna}] " if self.linea else ""
        return f"{prefijo}Error semántico {self.codigo}: {self.mensaje}"

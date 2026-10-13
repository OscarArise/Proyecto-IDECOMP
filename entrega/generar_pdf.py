"""
generar_pdf.py
--------------
Genera el documento PDF de la Fase 3 (Análisis Semántico) del proyecto
Proyecto-IDECOMP: descripción, reglas, atributos, tabla de símbolos, errores,
pruebas y capturas.

Uso (desde la carpeta entrega/):

    pip install reportlab
    python generar_pdf.py                      # usa capturas_borrador/
    python generar_pdf.py --capturas capturas  # usa las capturas definitivas

Lee los resultados reales del compilador (arbol_anotado.txt, tabla_simbolos.txt,
errores_semanticos.txt) y las capturas PNG; no hay datos escritos a mano de la
ejecución.
"""

import argparse
import os
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

AQUI = Path(__file__).resolve().parent

def leer_integrantes():
    """
    Lee los integrantes de integrantes.txt (una línea por persona):

        1. Nombre completo  -  Matrícula: 123456

    Es la única fuente: el mismo archivo se entrega y alimenta la portada del PDF.
    Devuelve una lista de (nombre, matrícula); la matrícula queda vacía si no se ha escrito.
    """
    ruta = AQUI / "integrantes.txt"
    gente = []
    if ruta.exists():
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^\s*\d+\.\s+(.+?)\s+-\s+Matr[ií]cula:\s*(.*?)\s*$", linea)
            if m:
                matricula = m.group(2).strip("_ ")
                gente.append((m.group(1).strip(), matricula))
    return gente or [("(completar integrantes.txt)", "")]


INTEGRANTES = leer_integrantes()


# Fuentes (DejaVu: trae ⟨ ⟩ → ✗ ← que Helvetica no tiene)

def _registrar_fuentes():
    candidatos = []
    try:
        import matplotlib

        candidatos.append(Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf")
    except Exception:
        pass
    candidatos += [
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("C:/Windows/Fonts"),
    ]
    for base in candidatos:
        if (base / "DejaVuSans.ttf").exists():
            pdfmetrics.registerFont(TTFont("Sans", str(base / "DejaVuSans.ttf")))
            pdfmetrics.registerFont(TTFont("Sans-Bold", str(base / "DejaVuSans-Bold.ttf")))
            pdfmetrics.registerFont(TTFont("Mono", str(base / "DejaVuSansMono.ttf")))
            pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-Bold",
                                          italic="Sans", boldItalic="Sans-Bold")
            return "Sans", "Sans-Bold", "Mono"
    return "Helvetica", "Helvetica-Bold", "Courier"


SANS, SANS_B, MONO = _registrar_fuentes()


def estilos():
    base = getSampleStyleSheet()
    e = {}
    e["titulo"] = ParagraphStyle("titulo", parent=base["Title"], fontName=SANS_B,
                                 fontSize=22, leading=27, spaceAfter=8)
    e["sub"] = ParagraphStyle("sub", parent=base["Normal"], fontName=SANS, fontSize=11,
                              leading=15, alignment=TA_CENTER, textColor=colors.HexColor("#444444"))
    e["h1"] = ParagraphStyle("h1", parent=base["Heading1"], fontName=SANS_B, fontSize=15,
                             leading=19, spaceBefore=14, spaceAfter=6, keepWithNext=1,
                             textColor=colors.HexColor("#1f3a5f"))
    e["h2"] = ParagraphStyle("h2", parent=base["Heading2"], fontName=SANS_B, fontSize=11.5,
                             leading=15, spaceBefore=9, spaceAfter=4, keepWithNext=1,
                             textColor=colors.HexColor("#2b4c7e"))
    e["p"] = ParagraphStyle("p", parent=base["Normal"], fontName=SANS, fontSize=9.6,
                            leading=14, spaceAfter=5)
    e["li"] = ParagraphStyle("li", parent=e["p"], leftIndent=14, bulletIndent=3, spaceAfter=2)
    e["celda"] = ParagraphStyle("celda", parent=e["p"], fontSize=8.4, leading=11, spaceAfter=0)
    e["celda_b"] = ParagraphStyle("celda_b", parent=e["celda"], fontName=SANS_B)
    e["pie"] = ParagraphStyle("pie", parent=e["p"], fontSize=8, leading=10, alignment=TA_CENTER,
                              textColor=colors.HexColor("#555555"))
    e["codigo"] = ParagraphStyle("codigo", fontName=MONO, fontSize=7.3, leading=9.2,
                                 backColor=colors.HexColor("#f3f5f8"), borderPadding=5,
                                 leftIndent=4, spaceAfter=8)
    return e


E = estilos()


def P(texto, estilo="p"):
    return Paragraph(texto, E[estilo])


def lista(items):
    return [Paragraph(t, E["li"], bulletText="•") for t in items]


def tabla(filas, anchos, encabezado=True, mono_col=None):
    datos = []
    for i, fila in enumerate(filas):
        datos.append([
            Paragraph(str(c), E["celda_b"] if (i == 0 and encabezado) else E["celda"])
            for c in fila
        ])
    t = Table(datos, colWidths=[a * inch for a in anchos], repeatRows=1 if encabezado else 0)
    est = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c2d0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    if encabezado:
        est.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e3eaf4")))
    t.setStyle(TableStyle(est))
    return KeepTogether([t]) if len(filas) <= 14 else t


def _ajustar(texto, ancho=104):
    """Parte las líneas largas (con sangría de continuación) para que no se salgan del margen."""
    salida = []
    for linea in texto.rstrip("\n").splitlines():
        if len(linea) <= ancho:
            salida.append(linea)
            continue
        sangria = len(linea) - len(linea.lstrip()) + 4
        resto = linea
        primera = True
        while len(resto) > ancho:
            corte = resto.rfind(" ", 0, ancho)
            if corte <= sangria:
                corte = ancho
            salida.append(resto[:corte])
            resto = " " * sangria + resto[corte:].lstrip()
            primera = False
        salida.append(resto)
    return "\n".join(salida)


def codigo(texto):
    return Preformatted(_ajustar(texto), E["codigo"])


def imagen(ruta, pie, ancho=6.5):
    from PIL import Image as PILImage

    with PILImage.open(ruta) as im:
        w, h = im.size
    img = Image(str(ruta), width=ancho * inch, height=ancho * inch * h / w)
    return KeepTogether([img, Spacer(1, 3), P(pie, "pie"), Spacer(1, 8)])


# Datos reales del compilador

def leer(nombre):
    return (AQUI / nombre).read_text(encoding="utf-8")


def recorrido(semantic_txt):
    m = re.search(r"Recorrido semántico:\n-+\n(.*?)\n\nErrores semánticos:", semantic_txt, re.S)
    return [l.strip() for l in m.group(1).splitlines()] if m else []


def arbol_texto(semantic_txt, desde, hasta):
    m = re.search(r"Árbol con anotaciones semánticas:\n-+\n(.*?)\n\nRecorrido semántico:",
                  semantic_txt, re.S)
    lineas = m.group(1).splitlines() if m else []
    return "\n".join(lineas[desde:hasta])


def resumen(semantic_txt):
    ident = re.search(r"Identificadores en la tabla: (\d+)", semantic_txt)
    conv = re.search(r"Conversiones implícitas aplicadas: (\d+)", semantic_txt)
    err = re.search(r"Errores semánticos: (\d+)", semantic_txt)
    return (int(ident.group(1)), int(conv.group(1)), int(err.group(1)))


# Documento

def _unir_titulos(historia):
    """Pega cada título (h1/h2) al elemento que le sigue para que no quede solo al final de una página."""
    salida, i = [], 0
    while i < len(historia):
        el = historia[i]
        if (isinstance(el, Paragraph) and el.style.name in ("h1", "h2")
                and i + 1 < len(historia)):
            siguiente = historia[i + 1]
            resto = siguiente._content if isinstance(siguiente, KeepTogether) else [siguiente]
            salida.append(KeepTogether([el] + list(resto)))
            i += 2
        else:
            salida.append(el)
            i += 1
    return salida


def construir(salida, carpeta_capturas):
    semantic = leer("arbol_anotado.txt")
    tabla_txt = leer("tabla_simbolos.txt")
    errores_txt = leer("errores_semanticos.txt")
    fuente = leer("TestSemantica.txt")
    n_ident, n_conv, n_err = resumen(semantic)
    pasos = recorrido(semantic)
    caps = Path(carpeta_capturas)

    doc = SimpleDocTemplate(
        str(salida), pagesize=letter, leftMargin=0.9 * inch, rightMargin=0.9 * inch,
        topMargin=0.8 * inch, bottomMargin=0.8 * inch,
        title="Compiladores II - Fase 3: Análisis Semántico",
        author=", ".join(n for n, _ in INTEGRANTES),
    )
    s = []

    # Portada
    s += [Spacer(1, 1.1 * inch),
          P("Universidad Autónoma de Aguascalientes", "sub"),
          P("Centro de Ciencias Básicas · Ingeniería en Sistemas Computacionales (9.º semestre)", "sub"),
          Spacer(1, 0.5 * inch),
          P("COMPILADORES II", "sub"),
          P("Fase 3: Análisis Semántico", "titulo"),
          P("Compilador e IDE del lenguaje CAOS (Proyecto-IDECOMP)", "sub"),
          Spacer(1, 0.6 * inch)]
    s.append(tabla([["Integrantes", "Matrícula"]] + [[n, m] for n, m in INTEGRANTES], [4.3, 1.9]))
    s += [Spacer(1, 0.3 * inch),
          P("Docente: Dra. Blanca G. Estrada Rentería", "sub"),
          P("Entrega: 15 de octubre de 2026", "sub"),
          Spacer(1, 0.3 * inch),
          P("Repositorio: github.com/OscarArise/Proyecto-IDECOMP "
            "(etiquetas fase3-b1, fase3-b2 y fase3-entrega)", "pie"),
          PageBreak()]

    # 1. Introducción
    s += [P("1. Descripción de la implementación", "h1"),
          P("El análisis semántico es la tercera fase del compilador. Recibe el Árbol "
            "Sintáctico Abstracto (AST) que produce el analizador sintáctico, calcula atributos de "
            "tipo y de valor sobre una <b>copia</b> del árbol, construye la tabla de símbolos y "
            "reporta los errores semánticos. El AST original no se modifica, de modo que ambos "
            "árboles pueden compararse dentro del IDE."),
          P("El trabajo se dividió en tres bloques: (1) preparación del analizador sintáctico y del "
            "contrato del AST, (2) núcleo semántico (tabla de símbolos, reglas, atributos y "
            "errores) y (3) integración con el compilador y el IDE, evidencias y este documento."),
          P("Pipeline del compilador", "h2"),
          codigo("fuente → léxico (DFA) → sintáctico (descenso recursivo) → AST\n"
                 "     → semántico: copia anotada + tabla de símbolos + errores\n"
                 "     → (intermedio y ejecución: fases posteriores)\n\n"
                 "Códigos de salida:  0 sin errores · 1 léxico · 2 sintáctico · 3 semántico"),
          P("Módulos", "h2"),
          tabla([
              ["Archivo", "Responsabilidad"],
              ["semantic/tipos.py", "Tipos int, float y bool; grupos de operadores; reglas de compatibilidad y conversión."],
              ["semantic/errores.py", "Códigos E1–E7 y la clase ErrorSemantico ([línea:columna] Error semántico Ex: mensaje)."],
              ["semantic/tabla_simbolos.py", "Tabla hash con encadenamiento (insertar, buscar, actualizar líneas, eliminar)."],
              ["semantic/analizador.py", "Recorrido del AST, atributos heredados y sintetizados, verificación de tipos, conversiones y anotación."],
              ["semantic/formateador.py", "Genera semantic.txt, symbols.txt y las líneas de errores."],
              ["compiler_stub.py", "Conecta la fase al pipeline: recibe el AST y escribe los archivos de salida."],
              ["ide/ui/*", "Pestañas Semantico, Arbol Anotado, Comparacion, Simbolos y errores semánticos; marcas en el editor."],
          ], [1.9, 4.4]),
          Spacer(1, 6)]

    # 2. Reglas semánticas
    s += [P("2. Reglas semánticas utilizadas", "h1"),
          P("El lenguaje tiene un solo ámbito (el bloque <b>main</b>) y tres tipos: <b>int</b>, "
            "<b>float</b> y <b>bool</b>. La palabra <b>real</b> es un alias de float; las cadenas "
            "solo aparecen dentro de <b>cout</b> y no participan en la verificación de tipos."),
          tabla([
              ["Construcción", "Regla semántica"],
              ["Declaración  tipo id1, id2, …",
               "dtype ← tipo (heredado); cada idi se inserta en la tabla con ese tipo. "
               "Si ya existía: E2."],
              ["Identificador en expresión o asignación",
               "Se busca en la tabla; tipo ← tipo registrado. Si no está: E1."],
              ["Literal", "tipo ← int o float según el literal; valor ← el literal; true/false: bool."],
              ["a + b, a − b, a * b, a / b, a ^ b",
               "Si ambos son int, el resultado es int; si alguno es float, el resultado es float y el "
               "operando int se convierte. Con bool: E5."],
              ["a % b", "Solo int con int; el resultado es int. En otro caso: E5."],
              ["a < b, a <= b, a > b, a >= b", "Operandos numéricos; resultado bool. En otro caso: E5."],
              ["a == b, a != b", "Numérico con numérico, o bool con bool; resultado bool. En otro caso: E3."],
              ["a && b, a || b, !a", "Operandos bool; resultado bool. En otro caso: E5."],
              ["id = expresión",
               "Mismo tipo: compatible. float ← int: conversión implícita. int ← float: E4. "
               "bool contra número: E6."],
              ["id++, id−−", "id debe ser numérico; en otro caso: E5."],
              ["Condición de if, while, do-while y until", "La expresión debe ser bool; en otro caso: E7."],
          ], [2.2, 4.1]),
          Spacer(1, 4),
          P("<b>División entre enteros.</b> int / int produce int y trunca hacia cero, como en C. La "
            "guía solo pide conversión cuando los operandos son de tipos diferentes; con dos int no "
            "hay conversión. Con división real, las líneas 11, 12, 13 y 31 del archivo de prueba "
            "producirían cuatro errores E4 que el archivo no busca provocar."),
          P("<b>Errores en cascada.</b> Un nodo con error recibe el tipo interno <i>error</i>; una "
            "operación con un operando de tipo error no genera errores nuevos. Por ejemplo, "
            "x = (y + 1.5) * 2 con y no declarada produce un solo E1.")]

    # 3. Atributos
    s += [P("3. Atributos sintetizados y heredados", "h1"),
          tabla([
              ["Atributo", "Clase", "Dónde se calcula", "Cómo se propaga"],
              ["dtype", "Heredado", "Nodo de declaración (tipo)",
               "De la declaración hacia sus identificadores (preorden); es el tipo con el que cada "
               "identificador entra en la tabla."],
              ["tipo", "Sintetizado", "Literales, identificadores y operaciones",
               "De los hijos al padre (postorden), según las reglas de la sección 2."],
              ["valor", "Sintetizado", "Operaciones con operandos constantes",
               "Solo se calcula cuando todos los operandos son constantes (2 + 3 − 1 → 4). Con un "
               "identificador no se fuerza. Una división entre la constante cero no se pliega."],
              ["loc", "De tabla", "Identificadores", "Posición del símbolo en la tabla, en orden de declaración (0, 1, 2…)."],
              ["tipo de la expresión / verificación", "Sintetizado", "Asignaciones",
               "Resultado de comparar el tipo de la variable con el de la expresión: compatible, "
               "conversión o error."],
              ["tipo requerido", "Heredado", "Condiciones",
               "Las condiciones de if, while, do-while y until heredan el tipo requerido bool."],
          ], [1.2, 1.0, 1.6, 2.5]),
          ]

    # 4. Anotación del AST
    s += [P("4. Anotación del AST", "h1"),
          P("El analizador trabaja sobre una copia profunda del árbol; el árbol original queda "
            "intacto (hay una prueba automática que lo verifica). A cada nodo de la copia se le "
            "agregan claves y su etiqueta se reescribe con las anotaciones entre ⟨ ⟩, de modo que "
            "el visor del IDE las muestra sin cambios."),
          tabla([
              ["Clave agregada", "Nodos", "Contenido"],
              ["tipo_dato, atributo_tipo", "Expresiones, identificadores", "Tipo calculado y su clase (sintetizado o heredado)."],
              ["valor_calculado", "Expresiones constantes", "Valor obtenido en compilación."],
              ["dtype, loc", "Declaraciones e identificadores", "Tipo heredado y localidad en la tabla."],
              ["tipo_expresion, verificacion", "Asignaciones", "Tipo de la expresión y resultado: compatible, conversion o error."],
              ["tipo_requerido", "Secciones CONDICION*", "Siempre bool."],
              ["errores_semanticos", "Nodo que causó el error", "Lista de códigos E1–E7."],
              ["label_sintactico", "Nodos anotados", "Etiqueta original del analizador sintáctico."],
          ], [1.9, 1.8, 2.6]),
          Spacer(1, 4),
          P("Se agregan dos tipos de nodo: <b>IdentificadorDeclarado</b> (hijo de cada declaración, "
            "uno por variable, con su dtype heredado y su loc) y <b>ConversionTipo</b> (envuelve al "
            "operando que se convirtió de int a float)."),
          P("Fragmento del árbol anotado (líneas 2–5 y 10 del archivo de prueba)", "h2"),
          codigo(arbol_texto(semantic, 3, 26) + "\n   …"),
          ]

    # 5. Tabla de símbolos
    s += [P("5. Diseño y funcionamiento de la tabla de símbolos", "h1"),
          P("Es la tabla hash de TINY: tamaño 211, función hash "
            "<font name='%s'>temp = ((temp &lt;&lt; 4) + c) mod 211</font> sobre los caracteres del "
            "nombre, y encadenamiento separado para las colisiones. Se extendió con el tipo y la "
            "posición de la declaración." % MONO),
          tabla([
              ["Campo", "Contenido"],
              ["nombre", "Lexema del identificador."],
              ["tipo", "int, float o bool (viene del atributo heredado dtype)."],
              ["loc", "Desplazamiento de memoria: 0, 1, 2… en orden de declaración."],
              ["línea y columna de declaración", "Dónde se declaró."],
              ["líneas", "Línea de la declaración y de cada uso, sin repetir."],
              ["siguiente", "Siguiente símbolo de la misma cubeta (encadenamiento)."],
          ], [2.2, 4.1]),
          Spacer(1, 4),
          P("Operaciones: <b>insertar</b> (si existe, se reporta E2), <b>buscar</b> (si no existe, E1; "
            "si existe, agrega la línea de uso), <b>actualizar líneas</b> y <b>eliminar</b>. Las "
            "variables no declaradas no se insertan: se reporta E1 en cada uso. Como el recorrido "
            "sigue el orden del programa, usar una variable antes de declararla también es E1."),
          P("Tabla generada con el archivo de prueba", "h2"),
          codigo(tabla_txt),
          ]

    # 6. Comprobación de tipos y conversiones
    conv_lineas = [p for p in pasos if "CONVERSION" in p]
    s += [P("6. Comprobación de tipos y conversiones", "h1"),
          P("La comprobación se hace en postorden: primero se determina el tipo de los hijos y "
            "después el del padre. Con el archivo de prueba el analizador aplicó <b>%d conversiones "
            "implícitas</b> int → float; todas ocurren en la línea 10 (a = 24.0 + 4 − 1 / 3 * 2 + "
            "34 − 1), donde un operando int se combina con float:" % n_conv),
          codigo("\n".join(conv_lineas[:n_conv])),
          P("La única conversión implícita permitida es <b>int → float</b>, al combinar un int con "
            "un float o al asignar un int a una variable float. float → int y cualquier conversión "
            "con bool no son válidas: se reportan como E4 (y E6 cuando se mezcla bool con número)."),
          P("Recorrido semántico (fragmento)", "h2"),
          P("Cada paso queda registrado en semantic.txt: declaraciones y herencia de dtype, "
            "inserciones y búsquedas en la tabla, tipos obtenidos, conversiones y errores."),
          codigo("\n".join(pasos[:24])),
          ]

    # 7. Errores
    s += [P("7. Errores semánticos implementados", "h1"),
          tabla([
              ["Código", "Error", "Se produce cuando…"],
              ["E1", "Identificador no declarado", "Se usa una variable que no está en la tabla."],
              ["E2", "Declaración duplicada", "Se declara dos veces el mismo identificador."],
              ["E3", "Tipos incompatibles", "Se comparan con == o != tipos que no son compatibles."],
              ["E4", "Conversión no válida", "Se asigna un float a un int (float → int no está permitida)."],
              ["E5", "Operador mal aplicado", "El operador no admite el tipo de sus operandos (&&, %, ++…)."],
              ["E6", "Asignación inconsistente", "Se asigna un bool a un número o un número a un bool."],
              ["E7", "Condición no booleana", "if, while, do-while o until reciben una expresión que no es bool."],
          ], [0.8, 1.9, 3.6]),
          Spacer(1, 4),
          P("Formato: <font name='%s'>[SEMANTICO] [línea:columna] Error semántico Ex: mensaje</font>. "
            "Los errores se escriben en errors.txt (el compilador termina con código 3) y el IDE los "
            "muestra en la pestaña Errores Semanticos y los marca en el editor." % MONO),
          P("Errores detectados en el archivo de prueba", "h2"),
          codigo(errores_txt),
          ]

    # 8. Pruebas
    s += [P("8. Pruebas realizadas", "h1"),
          P("Archivo de prueba", "h2"),
          P("Se utilizó el archivo TestSemantica.txt del curso. Contiene %d líneas, declara x, y, z "
            "(int) y a, b, c (float) y mezcla asignaciones, expresiones, condicionales, ciclos y "
            "entrada/salida. Resultado: <b>%d identificadores</b> en la tabla, <b>%d conversiones</b> "
            "y <b>%d errores semánticos</b>." % (len(fuente.splitlines()), n_ident, n_conv, n_err)),
          codigo("\n".join(f"{i:>2}  {l}" for i, l in enumerate(fuente.splitlines(), 1))),
          P("<b>Ajuste al archivo de prueba.</b> La guía indica que no debe sustituirse el archivo "
            "principal de pruebas. No se sustituyó: se ajustaron tres líneas (32, 37 y 38) para que "
            "usen la sintaxis de entrada y salida de nuestra gramática (cin x; y cout x;, sin los "
            "operadores >> y << de C++). Las declaraciones, las expresiones y los errores "
            "semánticos que deben detectarse son los mismos. El cambio fue consultado y aprobado "
            "por la profesora."),
          P("Resultados esperados y obtenidos", "h2"),
          tabla([
              ["Línea:col", "Error", "Causa"],
              ["4:5", "E1", "'suma' no está declarada"],
              ["5:5", "E4", "x = 32.32: float asignado a int"],
              ["14:5", "E4", "y = 14.54: float asignado a int"],
              ["16:9", "E4", "y = a + 3: expresión float asignada a int"],
              ["33:13", "E1", "'mas' no está declarada"],
              ["37:13", "E1", "'mas' no está declarada"],
          ], [1.0, 0.8, 4.5]),
          Spacer(1, 4),
          P("El compilador produce exactamente estos seis errores y ninguno más; los errores en "
            "cascada están suprimidos."),
          P("Pruebas automáticas", "h2"),
          tabla([
              ["Archivo", "Pruebas", "Qué verifica"],
              ["test_semantico.py", "30", "Tabla de símbolos, TestSemantica (errores, tabla, valores, conversiones, árbol original intacto, dtype heredado), casos E1–E7, cascadas y formateadores."],
              ["test_integracion.py", "8", "Compilador completo como subproceso: código de salida 3, los seis errores, tabla, semantic.txt y regresión de los códigos 0/1/2 con archivos de pruebas/ e ide/samples/."],
              ["test_parser_recovery.py", "19", "Analizador sintáctico (fase anterior), sin regresiones."],
              ["ide/test_semantic_output.py", "5", "Separación del árbol anotado y del texto en la salida del compilador."],
          ], [2.0, 0.8, 3.5]),
          Spacer(1, 4),
          P("Cambio en el analizador sintáctico", "h2"),
          P("Al probar casos propios se encontró un error que ya existía: el parser rechazaba una "
            "declaración posterior a una sentencia (int x; x = 1; int y;) aunque la gramática lo "
            "permite. Se corrigió con tres líneas en Parser._declaracion: la lista de sentencias se "
            "detiene al encontrar int, float, real o bool. Las pruebas del parser siguen pasando y "
            "los códigos de salida de todos los archivos de pruebas/ e ide/samples/ no cambiaron."),
          PageBreak()]

    # 9. Capturas
    s += [P("9. Capturas de ejecución en el IDE", "h1"),
          P("Todas las capturas corresponden a la ejecución del IDE (tecla F7) sobre TestSemantica.txt, "
            "salvo las dos últimas (programa válido y regresión sintáctica).")]
    figuras = [
        ("01_arbol_anotado.png", "Figura 1. Árbol con anotaciones semánticas: dtype heredado en los identificadores, tipos y valores en las expresiones y errores en rojo."),
        ("02_comparacion_ast_original_vs_anotado.png", "Figura 2. Comparación: AST original (izquierda) frente al AST con anotaciones (derecha)."),
        ("03_tabla_de_simbolos.png", "Figura 3. Tabla de símbolos: tipo, localidad, hash, declaración y líneas de uso."),
        ("04_semantico_recorrido_y_tipos.png", "Figura 4. Pestaña Semantico: resumen, árbol anotado en texto y recorrido semántico."),
        ("05_errores_semanticos_en_editor.png", "Figura 5. Errores semánticos y marcas en el editor (líneas 4, 5, 14, 16, 33 y 37; identificadores subrayados)."),
        ("06_programa_valido_sin_errores.png", "Figura 6. Un programa válido (codigo_valido.caos) completa la fase sin errores."),
        ("07_regresion_errores_sintacticos.png", "Figura 7. Regresión: un programa con errores sintácticos (conerrores.caos) se detiene en esa fase y los marca en el editor."),
    ]
    for nombre, pie in figuras:
        ruta = caps / nombre
        if ruta.exists():
            s.append(imagen(ruta, pie))
        else:
            s.append(P(f"[Falta la captura {nombre}]", "pie"))

    # 10. Entregables
    s += [KeepTogether([P("10. Entregables", "h1"),
          tabla([
              ["Entregable", "Archivo"],
              ["Código fuente completo", "Repositorio (etiqueta fase3-entrega)"],
              ["AST utilizado como base", "ast_original.txt"],
              ["Árbol con anotaciones semánticas", "arbol_anotado.txt"],
              ["Tabla de símbolos", "tabla_simbolos.txt"],
              ["Errores semánticos", "errores_semanticos.txt"],
              ["Capturas", "carpeta de capturas"],
              ["Documento de la fase", "Este PDF"],
              ["Integrantes y matrículas", "integrantes.txt"],
          ], [3.0, 3.3])])]

    def pie_de_pagina(c, d):
        c.saveState()
        c.setFont(SANS, 8)
        c.setFillColor(colors.HexColor("#666666"))
        c.drawString(0.9 * inch, 0.5 * inch, "Compiladores II · Fase 3: Análisis Semántico")
        c.drawRightString(letter[0] - 0.9 * inch, 0.5 * inch, f"Página {d.page}")
        c.restoreState()

    doc.build(_unir_titulos(s), onFirstPage=lambda c, d: None, onLaterPages=pie_de_pagina)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--capturas", default=str(AQUI / "capturas_borrador"))
    ap.add_argument("--out", default=str(AQUI / "Fase3_Analisis_Semantico.pdf"))
    a = ap.parse_args()
    construir(a.out, a.capturas)
    print("PDF generado:", a.out)

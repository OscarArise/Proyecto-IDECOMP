"""
tm_tools.py
-----------
Acceso al simulador TM extendido (carpeta tm/ en la raíz del proyecto):
    - importar TMSimulator (tm/tm.py) para ejecutar dentro del IDE;
    - compilar tm/tm.c con gcc y abrir tm.exe en una consola externa.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
TM_DIR = REPO_ROOT / "tm"
TM_SOURCE = TM_DIR / "tm.c"
TM_EXE = TM_DIR / ("tm.exe" if os.name == "nt" else "tm")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tm.tm import (  # noqa: E402
    DMEM_ERR,
    HALT,
    IMEM_ERR,
    INPUT_CANCELLED,
    OKAY,
    STEP_LIMIT,
    ZERODIVIDE,
    TMLoadError,
    TMSimulator,
    parse_input,
)

__all__ = [
    "DMEM_ERR", "HALT", "IMEM_ERR", "INPUT_CANCELLED", "OKAY", "STEP_LIMIT",
    "ZERODIVIDE", "TMLoadError", "TMSimulator", "parse_input",
    "build_tm_exe", "open_tm_console",
]


def build_tm_exe() -> tuple[Optional[Path], str]:
    """
    Compila tm/tm.c si tm.exe no existe o es más antiguo que el fuente.
    Retorna (ruta_exe, "") o (None, mensaje_de_error).
    """
    if TM_EXE.exists() and TM_EXE.stat().st_mtime >= TM_SOURCE.stat().st_mtime:
        return TM_EXE, ""
    gcc = shutil.which("gcc")
    if not gcc:
        return None, ("No se encontró gcc en el PATH. Compile manualmente con "
                      "tm\\compilar_tm.bat o instale MinGW/MSYS2.")
    proc = subprocess.run(
        [gcc, "-std=c11", "-O2", str(TM_SOURCE), "-o", str(TM_EXE), "-lm"],
        capture_output=True, text=True, cwd=str(TM_DIR),
    )
    if proc.returncode != 0:
        return None, f"gcc no pudo compilar tm.c:\n{proc.stderr}"
    return TM_EXE, ""


def open_tm_console(tm_file: Path) -> str:
    """Abre tm.exe con el archivo .tm en una consola nueva. Retorna '' o un error."""
    exe, error = build_tm_exe()
    if not exe:
        return error
    if os.name != "nt":
        return f"Ejecute en una terminal:\n  {exe} {tm_file}"
    # cmd /k mantiene la consola abierta al salir del simulador; chcp 65001
    # permite ver acentos de las cadenas UTF-8 que imprime OUTS
    comando = f'cmd /k "chcp 65001 >nul & "{exe}" "{tm_file}""'
    subprocess.Popen(comando, cwd=str(tm_file.parent),
                     creationflags=subprocess.CREATE_NEW_CONSOLE)
    return ""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Rutas base (relativas al directorio del IDE)

# Directorio que contiene main.py / ide_window.py, etc.
_IDE_DIR = Path(__file__).resolve().parent.parent          # …/ide/

# Compilador stub (fuera del directorio ide/)
_COMPILER_STUB = _IDE_DIR.parent / "external_compiler" / "compiler_stub.py"

# Carpeta donde el compilador deposita sus archivos de salida
_OUTPUTS_DIR = _IDE_DIR / "outputs"

# Intérprete Python a usar (el mismo que está ejecutando el IDE)
_PYTHON = sys.executable


# Mapa archivo-de-salida → clave de panel

# Las claves deben coincidir con los atributos de Panels que usa IDEWindow
# para saber en qué widget escribir.

OUTPUT_FILE_MAP: dict[str, str] = {
    "tokens.txt":       "lexico",
    "syntax.txt":       "sintactico",
    "semantic.txt":     "semantico",
    "intermediate.txt": "intermedio",
    "symbols.txt":      "simbolos",
    "exec.txt":         "ejecucion",
}

# Prefijos reconocidos dentro de errors.txt para clasificar por fase
# (el compilador stub puede incluir líneas como "[LEXICO] Error: ...")
_PHASE_KEYWORDS: dict[str, str] = {
    "lexico":     "err_lexico",
    "lex":        "err_lexico",
    "sintactico": "err_sintactico",
    "syntax":     "err_sintactico",
    "syn":        "err_sintactico",
    "semantico":  "err_semantico",
    "semantic":   "err_semantico",
    "sem":        "err_semantico",
    "intermedio": "intermedio",
    "ejecucion":  "ejecucion",
    "exec":       "ejecucion",
    "runtime":    "ejecucion",
}

# Resultado estructurado

@dataclass
class CompilerResult:
    
    success: bool
    returncode: int
    stdout: str
    stderr: str
    outputs: dict[str, str] = field(default_factory=dict)
    errors_by_phase: dict[str, str] = field(default_factory=dict)
    failed_phase: Optional[str] = None



# CompilerRunner


class CompilerRunner:
    """
    Gestiona la invocación del compilador y la recolección de resultados.

    Parámetros
    ----------
    compiler_path : Path al script del compilador (por defecto: compiler_stub.py).
    outputs_dir   : Directorio donde el compilador escribe sus archivos de salida.
    timeout       : Segundos máximos de espera antes de matar el proceso.
    """

    def __init__(
        self,
        compiler_path: Path = _COMPILER_STUB,
        outputs_dir: Path = _OUTPUTS_DIR,
        timeout: int = 30,
    ):
        self.compiler_path = Path(compiler_path)
        self.outputs_dir = Path(outputs_dir)
        self.timeout = timeout



    def run(self, source_file: str, phase: str = "all") -> CompilerResult:
        """
        Ejecuta el compilador sobre `source_file` y retorna un `CompilerResult`.
        """
        cmd = self._build_command(source_file, phase)
        proc_result = self._execute(cmd)
        outputs = self._read_output_files()
        errors_by_phase = self._parse_errors()
        failed_phase = self._detect_failed_phase(
            proc_result.returncode, errors_by_phase
        )

        return CompilerResult(
            success=proc_result.returncode == 0,
            returncode=proc_result.returncode,
            stdout=proc_result.stdout or "",
            stderr=proc_result.stderr or "",
            outputs=outputs,
            errors_by_phase=errors_by_phase,
            failed_phase=failed_phase,
        )

    
    # Construir el comando
 
    def _build_command(self, source_file: str, phase: str) -> list[str]:
        """
        Construye la lista de argumentos para subprocess.
        """
        cmd: list[str] = [
            _PYTHON,
            str(self.compiler_path),
            str(source_file),
        ]
        if phase and phase != "all":
            cmd += ["--phase", phase]
        return cmd


    #Ejecutar con subprocess

    def _execute(self, cmd: list[str]) -> subprocess.CompletedProcess:
        """
        Lanza el compilador como subproceso y captura stdout/stderr.
        Si se excede `timeout` mata el proceso y retorna código -1.
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                cwd=str(self.outputs_dir),   # el compilador escribe en outputs/
            )
            return result
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=-1,
                stdout="",
                stderr="[CompilerRunner] El compilador superó el tiempo límite de "
                       f"{self.timeout} segundos.",
            )
        except FileNotFoundError:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=-2,
                stdout="",
                stderr=f"[CompilerRunner] No se encontró el compilador en:\n"
                       f"  {self.compiler_path}",
            )
        except Exception as exc:  # noqa: BLE001
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=-3,
                stdout="",
                stderr=f"[CompilerRunner] Error inesperado al lanzar el compilador:\n{exc}",
            )

 
    #Leer archivos de salida
  

    def _read_output_files(self) -> dict[str, str]:
        """
        Lee cada archivo de `OUTPUT_FILE_MAP` desde `outputs_dir`.

        Retorna un dict { panel_key: contenido_str }.
        Los archivos inexistentes o vacíos producen una cadena vacía.
        """
        outputs: dict[str, str] = {}
        for filename, panel_key in OUTPUT_FILE_MAP.items():
            path = self.outputs_dir / filename
            outputs[panel_key] = self._safe_read(path)
        return outputs

    #Parsear errors.txt y clasificar por fase

    def _parse_errors(self) -> dict[str, str]:
        """
        Lee `errors.txt` y separa los mensajes según la fase a la que pertenecen.

        Formato esperado (flexible):
            [LEXICO] Caracter inesperado '@' en línea 3
            [SINTACTICO] Se esperaba ';' en línea 7
            Líneas sin prefijo se agrupan bajo la fase "err_lexico" como
            fallback, o se ignoran si el archivo está vacío.

        Retorna dict { panel_err_key: texto_multilinea }.
        """
        errors_path = self.outputs_dir / "errors.txt"
        raw = self._safe_read(errors_path)

        if not raw.strip():
            return {}

        # Agrupar líneas por fase
        buckets: dict[str, list[str]] = {}
        current_key: str = "err_lexico"   # fallback si la línea no tiene prefijo

        for line in raw.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            detected_key = self._classify_error_line(stripped)
            if detected_key:
                current_key = detected_key

            buckets.setdefault(current_key, []).append(line)

        return {key: "\n".join(lines) for key, lines in buckets.items()}

    def _classify_error_line(self, line: str) -> Optional[str]:
        """
        Detecta si la línea comienza con un marcador de fase como [LEXICO].
        Retorna la clave de panel correspondiente, o None si no aplica.
        """
        if not line.startswith("["):
            return None
        close = line.find("]")
        if close == -1:
            return None
        tag = line[1:close].lower()
        for keyword, panel_key in _PHASE_KEYWORDS.items():
            if keyword in tag:
                return panel_key
        return None

    
    #Detectar fase con error
    

    def _detect_failed_phase(
        self,
        returncode: int,
        errors_by_phase: dict[str, str],
    ) -> Optional[str]:
        """
        Identifica la primera fase en que se produjo un error.

        Orden de prioridad (de más temprana a más tardía en la pipeline):
            err_lexico → err_sintactico → err_semantico → intermedio → ejecucion

        Retorna el nombre de la fase, o None si no se detectó ningún error.
        """
        if returncode == 0 and not errors_by_phase:
            return None

        phase_order = [
            "err_lexico",
            "err_sintactico",
            "err_semantico",
            "intermedio",
            "ejecucion",
        ]
        for phase_key in phase_order:
            if phase_key in errors_by_phase and errors_by_phase[phase_key].strip():
                return phase_key

        # Si hay código de error pero no se clasificó → fase desconocida
        if returncode not in (0, None):
            return "desconocido"

        return None

   

    @staticmethod
    def _safe_read(path: Path) -> str:
        """Lee un archivo de texto con manejo seguro de errores."""
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            return ""
        except OSError as exc:
            return f"[Error al leer {path.name}: {exc}]"

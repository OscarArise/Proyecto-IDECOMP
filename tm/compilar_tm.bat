@echo off
REM Compila el simulador TM extendido para CAOS (tm.c -> tm.exe)
cd /d "%~dp0"
gcc -std=c11 -O2 -Wall tm.c -o tm.exe -lm
if errorlevel 1 (
  echo No se pudo compilar tm.c. Verifique que gcc este en el PATH.
  exit /b 1
)
echo tm.exe generado en %~dp0

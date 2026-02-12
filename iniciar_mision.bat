@echo off
title EGG SYSTEM - PORTABLE EDITION
color 0B
cd /d "%~dp0"

echo ======================================================
echo    INICIANDO SISTEMA DE LECTURA PORTABLE (EGG)
echo ======================================================
echo.

:: 1. Comprobamos si existe el entorno virtual
if exist ".venv" (
    echo [OK] Entorno virtual detectado.
    goto :START_APP
)

:: 2. Si no existe, lo creamos (Solo la primera vez)
echo [NUEVO] Creando entorno virtual portable...
python -m venv .venv

if %errorlevel% neq 0 (
    echo [ERROR] No se pudo crear el entorno virtual. 
    echo Asegurate de tener Python instalado en el ordenador anfitrion.
    pause
    exit
)

:: 3. Instalar dependencias en el entorno virtual
echo [INSTALANDO] Descargando librerias necesarias...
echo Esto puede tardar un poco la primera vez...
".venv\Scripts\pip" install edge-tts pygame pytesseract pillow keyboard >nul 2>&1

echo [OK] Instalacion completada.

:START_APP
:: 4. Ejecutar el script usando el Python del entorno virtual
echo.
echo Lanzando aplicacion...
".venv\Scripts\python" lector_portable.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] El programa se cerro inesperadamente.
    echo REVISA: Has copiado la carpeta 'Tesseract-OCR' dentro de esta carpeta?
    pause
)
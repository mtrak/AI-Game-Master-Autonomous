@echo off
title Arma Reforger IA - MODO COMANDANTE
cd /d "%~dp0"
echo ==============================================
echo    SISTEMA TACTICO IA - ARMA REFORGER
echo ==============================================
echo.
echo [+] Abriendo Panel de Control...
if exist "Web\index.html" ( start "" "Web\index.html" )
echo [+] Entrando en la carpeta Backend...
cd Backend
echo [+] Iniciando Servidor Modular...
python3-64.exe main.py
pause

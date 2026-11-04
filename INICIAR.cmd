@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Politica Eficiente - servidor local
echo.
echo  Politica Eficiente
echo  Abriendo en http://127.0.0.1:5055
echo  (cerra esta ventana para detener el servidor)
echo.
start "" "http://127.0.0.1:5055"
python app.py
pause

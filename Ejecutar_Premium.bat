@echo off
chcp 65001 > nul
title Web Dashboard Bot Deportivo PREMIUM
color 0A

echo =======================================================
echo Iniciando Interfaz Grafica WEB VIP...
echo =======================================================

cd /d "%~dp0"

:: Revisar dependencias y que el entorno no este danado por USB
if exist "venv" (
    venv\Scripts\python.exe -c "pass" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] El entorno virtual esta danado o fue copiado desde otra PC.
        echo Para arreglarlo automaticamente, sierra esta ventana y haz doble clic en "Ejecutar_Bot.bat" primero.
        pause
        exit /b
    )
)

if not exist "venv" (
    echo [ERROR] No existe el entorno virtual. Ejecuta primero "Ejecutar_Bot.bat"
    pause
    exit /b
)

call venv\Scripts\activate.bat

echo Lanzando Streamlit en el navegador...
echo.
streamlit run app_premium.py

pause

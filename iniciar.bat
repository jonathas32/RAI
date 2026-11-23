@echo off
chcp 65001 >nul
title RAI
cd /d "%~dp0"

if not exist .venv\Scripts\python.exe (
  echo Criando ambiente Python...
  py -3.12 -m venv .venv 2>NUL || py -3.11 -m venv .venv 2>NUL || py -3 -m venv .venv 2>NUL || python -m venv .venv
)
if not exist .venv\Scripts\python.exe (
  echo.
  echo ERRO: nao encontrei o Python. Instale o Python 3.12 em python.org
  echo e marque "Add python.exe to PATH" no instalador.
  pause
  exit /b
)

if not exist .venv\instalado_v2.ok (
  echo Instalando dependencias, isso leva alguns minutos...
  .venv\Scripts\python --version
  .venv\Scripts\python -m pip install --upgrade pip
  .venv\Scripts\python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo.
    echo ERRO na instalacao. Tire um print desta janela e verifique o README.
    pause
    exit /b
  )
  echo ok> .venv\instalado_v2.ok
)

if not exist .env (
  copy .env.exemplo .env >nul
  echo.
  echo Abri o arquivo .env: cole sua chave da API, salve e rode de novo.
  notepad .env
  pause
  exit /b
)

.venv\Scripts\python main.py
pause

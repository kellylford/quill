@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
set "PYTHON_EXE="

if exist "%ROOT%.venv\Scripts\python.exe" set "PYTHON_EXE=%ROOT%.venv\Scripts\python.exe"
if not defined PYTHON_EXE if exist "%ROOT%venv\Scripts\python.exe" set "PYTHON_EXE=%ROOT%venv\Scripts\python.exe"

if not defined PYTHON_EXE (
    where /q python.exe
    if not errorlevel 1 set "PYTHON_EXE=python"
)

if not defined PYTHON_EXE (
    where /q py.exe
    if not errorlevel 1 set "PYTHON_EXE=py"
)

if not defined PYTHON_EXE (
    echo No Python interpreter was found.
    echo.
    echo Create or activate a development environment first, for example:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -e .[dev,ui]
    exit /b 1
)

if /i "%~1"=="--print-python" (
    echo %PYTHON_EXE%
    exit /b 0
)

pushd "%ROOT%"
"%PYTHON_EXE%" -m quill %*
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
@echo off
REM -*- coding: utf-8 -*-

REM HERE IS THE CHANGELOG FOR THIS VERSION OF THE CODE:
REM - Restored original batch-based entry point for DHT on Windows
REM - Maintains compatibility with existing Windows workflows  
REM - Properly delegates to Python launcher when installed
REM - Follows UV-compatible architecture
REM 

setlocal enabledelayedexpansion

REM DHT Main Entry Point (Windows Batch Script)
REM This is the primary entry point for DHT on Windows systems
REM It delegates to the Python launcher while maintaining shell-based architecture

REM Get the directory containing this script
set "SCRIPT_DIR=%~dp0"
set "DHT_ROOT=%SCRIPT_DIR:~0,-1%"

REM Check if we're in development mode (src/ structure) or installed mode
if exist "%DHT_ROOT%\src\DHT\dhtl.py" (
    REM Development mode - use src structure
    set "DHTL_PYTHON=%DHT_ROOT%\src\DHT\dhtl.py"
    set "DHTL_DEV_MODE=1"
) else if exist "%DHT_ROOT%\DHT\dhtl.py" (
    REM Legacy mode - direct structure
    set "DHTL_PYTHON=%DHT_ROOT%\DHT\dhtl.py"
    set "DHTL_DEV_MODE=1"
) else (
    REM Try installed dhtl command
    where dhtl >nul 2>&1
    if !errorlevel! equ 0 (
        dhtl %*
        exit /b !errorlevel!
    ) else (
        echo ❌ Error: DHT launcher not found
        echo Please ensure DHT is properly installed or run from the correct directory
        exit /b 1
    )
)

REM Set environment variables for shell modules
set "DHT_ROOT=%DHT_ROOT%"
set "SCRIPT_DIR=%SCRIPT_DIR%"
set "DHTL_SHELL_ENTRY=1"

REM Use Python to run the launcher
if defined VIRTUAL_ENV (
    REM Use activated virtual environment
    python "%DHTL_PYTHON%" %*
) else (
    REM Try python3 first, then python
    where python3 >nul 2>&1
    if !errorlevel! equ 0 (
        python3 "%DHTL_PYTHON%" %*
    ) else (
        where python >nul 2>&1
        if !errorlevel! equ 0 (
            python "%DHTL_PYTHON%" %*
        ) else (
            echo ❌ Error: Python not found
            echo Please install Python 3.10+ or activate a virtual environment
            exit /b 1
        )
    )
)

exit /b %errorlevel%
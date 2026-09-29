@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title OQPES - Proposed Method vs Prerna-Sharma 2024

echo ================================================================
echo   OQPES - automatic launcher
echo   Working directory: %CD%
echo ================================================================

set "CONDA_ROOT=%USERPROFILE%\anaconda3"
if not exist "%CONDA_ROOT%\Scripts\activate.bat" set "CONDA_ROOT=%USERPROFILE%\miniconda3"
if not exist "%CONDA_ROOT%\Scripts\activate.bat" (
  echo.
  echo ERROR: Anaconda or Miniconda was not found under %%USERPROFILE%%\anaconda3 or %%USERPROFILE%%\miniconda3.
  echo Install Anaconda/Miniconda, or open Anaconda Prompt and start this script from the repository directory.
  pause
  exit /b 1
)

call "%CONDA_ROOT%\Scripts\activate.bat" "%CONDA_ROOT%"

call conda env list | findstr /R /C:"^oqpes_py[ ]" >nul 2>&1
if errorlevel 1 (
  echo.
  echo The oqpes_py environment does not exist. Creating it from environment.yml...
  call conda env create -f environment.yml
  if errorlevel 1 (
    echo ERROR: environment creation failed.
    pause
    exit /b 1
  )
)

call conda activate oqpes_py
if errorlevel 1 (
  echo ERROR: unable to activate oqpes_py.
  pause
  exit /b 1
)

set "PYTHONPATH=%CD%\src;%PYTHONPATH%"
python -m oqpes.launcher

if errorlevel 1 (
  echo.
  echo OQPES terminated with an error.
) else (
  echo.
  echo OQPES finished successfully.
)
pause

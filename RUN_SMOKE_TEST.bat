@echo off
cd /d "%~dp0"
set "CONDA_ROOT=%USERPROFILE%\anaconda3"
if not exist "%CONDA_ROOT%\Scripts\activate.bat" set "CONDA_ROOT=%USERPROFILE%\miniconda3"
if not exist "%CONDA_ROOT%\Scripts\activate.bat" (
  echo ERROR: Anaconda or Miniconda was not found.
  pause
  exit /b 1
)
call "%CONDA_ROOT%\Scripts\activate.bat" "%CONDA_ROOT%"
call conda activate oqpes_py
if errorlevel 1 (
  echo ERROR: unable to activate oqpes_py.
  pause
  exit /b 1
)
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"
python -m oqpes smoke --time-limit 60
pause

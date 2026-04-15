@echo off
setlocal

cd /d "%~dp0"

git config core.hooksPath .githooks
for /f "delims=" %%i in ('git config --get core.hooksPath') do set HOOKSPATH=%%i

if "%HOOKSPATH%"==".githooks" (
  echo Git hooks activated: %HOOKSPATH%
  exit /b 0
)

echo Failed to activate git hooks. Current core.hooksPath: "%HOOKSPATH%"
exit /b 1

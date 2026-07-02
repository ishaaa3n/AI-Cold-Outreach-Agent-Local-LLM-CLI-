@echo off
REM ====================================================================
REM  Outreach Agent - simple menu.
REM ====================================================================
setlocal
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe -m outreach_cli --root .\my-outreach"

REM 
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I "ollama.exe" >NUL
if errorlevel 1 (
  echo Starting the local AI ^(Ollama^)...
  start "" /min ollama serve
  timeout /t 4 >NUL
)

:menu
cls
echo ==========================================
echo            OUTREACH AGENT
echo ==========================================
echo.
echo   1. Send a TEST email to yourself
echo   2. DRAFT emails  (writes to my-outreach\outbox, does NOT send)
echo   3. PREVIEW send  (dry run - shows what would send, sends nothing)
echo   4. SEND emails   (for real)
echo   5. Open the drafts folder
echo   6. Exit
echo.
set /p "choice=Type a number (1-6) and press Enter: "

if "%choice%"=="1" goto test
if "%choice%"=="2" goto draft
if "%choice%"=="3" goto preview
if "%choice%"=="4" goto send
if "%choice%"=="5" goto openfolder
if "%choice%"=="6" goto end
goto menu

:test
echo.
echo Sending one test email to yourself...
%PY% test
echo.
pause
goto menu

:draft
echo.
set /p "company=Company to filter by (or just press Enter for ALL): "
if "%company%"=="" (
  %PY% draft --research
) else (
  %PY% draft --only "%company%" --research
)
echo.
echo Done. Review the drafts in:  my-outreach\outbox
echo.
pause
goto menu

:preview
echo.
set /p "num=How many to PREVIEW (e.g. 5): "
%PY% run --limit %num% --dry-run --yes
echo.
pause
goto menu

:send
echo.
echo *** This SENDS REAL EMAILS. Keep it small (5-40). ***
set /p "num=How many to SEND (e.g. 5): "
%PY% run --limit %num% --research
echo.
pause
goto menu

:openfolder
start "" "%~dp0my-outreach\outbox"
goto menu

:end
endlocal

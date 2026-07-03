@echo off
cd /d "%~dp0"
if not exist "logs" mkdir logs
echo [%date% %time%] Batch file started with arg: "%~1" >> logs\batch_run.log
echo Starte Gemma Discord Bot...
call venv\Scripts\activate
python -u discord_bot.py >> logs\discord_bot_out.log 2>&1
if "%~1"=="--nopause" goto end
pause
:end

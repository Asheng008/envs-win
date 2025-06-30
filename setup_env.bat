@REM 为当前这个项目写个requirements.txt文件

@echo off

chcp 65001

echo Creating virtual environment...

python -m venv .venv

echo Virtual environment created.

echo Waiting for 10 seconds...

timeout /t 10 /nobreak

echo Activating virtual environment...

call .venv\Scripts\activate.bat

echo Upgrading pip...

.venv\Scripts\python.exe -m pip install --upgrade pip

echo Waiting for 3 seconds...

timeout /t 3 /nobreak

IF EXIST requirements.txt (
    echo Installing dependencies from requirements.txt...
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo Setup complete. You can now run the application.
) ELSE (
    echo requirements.txt not found!
    echo Please create a requirements.txt file for this project first.
    pause
    exit /b 1
)

pause

@echo off
echo Checking Python installation...

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found in PATH, trying to activate conda...
    
    :: 尝试激活conda
    call conda activate base >nul 2>&1
    if %errorlevel% neq 0 (
        echo Conda activation failed. Trying to find conda...
        
        :: 尝试在常见位置查找conda
        if exist "%USERPROFILE%\anaconda3\Scripts\activate.bat" (
            call "%USERPROFILE%\anaconda3\Scripts\activate.bat"
        ) else if exist "%USERPROFILE%\miniconda3\Scripts\activate.bat" (
            call "%USERPROFILE%\miniconda3\Scripts\activate.bat"
        ) else if exist "C:\ProgramData\anaconda3\Scripts\activate.bat" (
            call "C:\ProgramData\anaconda3\Scripts\activate.bat"
        ) else if exist "C:\ProgramData\miniconda3\Scripts\activate.bat" (
            call "C:\ProgramData\miniconda3\Scripts\activate.bat"
        ) else (
            echo Python is not installed and conda not found!
            echo Please install Python 3.6 or higher from https://www.python.org/downloads/
            echo Or install Anaconda from https://www.anaconda.com/download
            pause
            exit /b 1
        )
    )
    
    :: 再次检查Python是否可用
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo Python is still not available after conda activation!
        echo Please make sure Python is installed in your conda environment.
        pause
        exit /b 1
    )
)

:: 检查pip是否可用
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo pip is not available! Please make sure pip is installed with Python.
    pause
    exit /b 1
)

echo Python is installed. Checking required packages...

:: 检查并安装所需的包
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Flask...
    python -m pip install flask==3.0.2
    if %errorlevel% neq 0 (
        echo Failed to install Flask!
        pause
        exit /b 1
    )
)

echo All dependencies are installed. Starting the application...

:: 启动应用
start http://localhost:5000
python server.py

pause 
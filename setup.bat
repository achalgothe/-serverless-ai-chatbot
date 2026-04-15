@echo off
echo ========================================
echo Installing dependencies for Chatbot...
echo ========================================
echo.

echo [1/3] Installing Python dependencies...
pip install flask python-dotenv openai boto3
echo.

echo [2/3] Checking .env file...
if not exist .env (
    echo Creating .env file from example...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env and add your OpenAI API key!
    echo.
) else (
    echo .env file already exists
)
echo.

echo [3/3] Setup complete!
echo.
echo ========================================
echo Next steps:
echo ========================================
echo 1. Edit .env and add your OpenAI API key
echo 2. Run: python local_server.py
echo 3. Open: frontend/index.html in browser
echo ========================================
echo.
pause

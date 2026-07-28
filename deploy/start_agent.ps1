$env:PYTHONPATH = "."

Write-Host "Starting Personal Agent API..."
Start-Process python -ArgumentList "-m uvicorn brain.api:app --host 127.0.0.1 --port 8787"

Write-Host "Starting Telegram bot..."
Start-Process python -ArgumentList "bot/telegram_bot.py"

Write-Host "Starting connector executor..."
Start-Process python -ArgumentList "connector/runtime/agent.py --device-id windows-laptop"

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в переменных окружения. Проверьте файл .env")

if not os.path.exists('data'):
    os.makedirs('data')

print(f"✅ Конфигурация загружена. Токен: {'*' * 10}{BOT_TOKEN[-5:]}")
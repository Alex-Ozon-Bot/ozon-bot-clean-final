import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Создаем папку data если ее нет
if not os.path.exists('data'):
    os.makedirs('data')
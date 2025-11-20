# render_bot.py - специальная версия для Render
import os
import time
import threading
from bot import main, start_health_server

def run_bot_with_health_check():
    """Запускает бота и health server вместе"""
    
    # Запускаем health server в отдельном потоке
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    print("✅ Health server запущен")
    
    # Даем время health server запуститься
    time.sleep(5)
    
    # Запускаем бота
    print("🤖 Запуск бота...")
    main()

if __name__ == "__main__":
    run_bot_with_health_check()
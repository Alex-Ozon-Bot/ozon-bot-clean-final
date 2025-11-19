import sqlite3
import os
from database import db

def check_database():
    """Проверка содержимого базы данных"""
    print("🔍 Проверка базы данных...")
    
    # Проверим существование файла базы
    if not os.path.exists('business_processes.db'):
        print("❌ Файл базы данных не существует")
        return
    
    try:
        # Проверим базу данных напрямую через SQLite
        conn = sqlite3.connect('business_processes.db')
        cursor = conn.cursor()
        
        # Проверим таблицу processes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='processes'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ Таблица 'processes' не существует")
            conn.close()
            return
        
        # Посчитаем процессы
        cursor.execute('SELECT COUNT(*) FROM processes')
        count = cursor.fetchone()[0]
        print(f"📊 Всего процессов в базе: {count}")
        
        if count > 0:
            # Покажем первые 10 процессов
            cursor.execute('SELECT process_id, process_name, level FROM processes ORDER BY process_id LIMIT 10')
            processes = cursor.fetchall()
            print(f"\n📋 Первые 10 процессов:")
            for process in processes:
                print(f"  {process[0]} (ур.{process[2]}): {process[1]}")
            
            # Проверим поиск через нашу базу данных
            print(f"\n🔍 Тест поиска:")
            test_searches = ['прием', 'B1', 'возврат', 'клиент']
            for search_term in test_searches:
                results = db.search_processes(search_term)
                print(f"   Поиск '{search_term}': найдено {len(results)} процессов")
                if results:
                    for result in results[:2]:  # Покажем первые 2 результата
                        process_id, process_name, level, responsible, description, keywords, bpmn_link = result
                        print(f"     - {process_name} ({process_id})")
        
        conn.close()
        print(f"\n✅ База данных работает корректно!")
        
    except Exception as e:
        print(f"❌ Ошибка при проверке базы данных: {e}")

if __name__ == '__main__':
    check_database()
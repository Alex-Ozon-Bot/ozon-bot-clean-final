import sqlite3
from database import db

print("🔍 ДЕБАГ БАЗЫ ДАННЫХ")

# Проверим базу напрямую
conn = sqlite3.connect('business_processes.db')
cursor = conn.cursor()

# Посмотрим все таблицы
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("📊 Таблицы в базе:", tables)

# Посчитаем процессы
cursor.execute('SELECT COUNT(*) FROM processes')
count = cursor.fetchone()[0]
print(f"📈 Всего процессов: {count}")

if count > 0:
    # Покажем первые 5 процессов
    cursor.execute('SELECT process_id, process_name, keywords FROM processes LIMIT 5')
    processes = cursor.fetchall()
    print("\n📋 Первые 5 процессов:")
    for process in processes:
        print(f"  {process[0]}: {process[1]}")
        print(f"    Ключевые слова: {process[2]}")
    
    # Проверим поиск напрямую
    print("\n🔍 ПРОВЕРКА ПОИСКА:")
    test_queries = ['прием', 'перевозки', 'B1', 'возврат']
    for query in test_queries:
        cursor.execute('''
            SELECT process_id, process_name FROM processes 
            WHERE process_id LIKE ? OR process_name LIKE ? OR keywords LIKE ? OR description LIKE ?
        ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        results = cursor.fetchall()
        print(f"  '{query}': найдено {len(results)}")
        for result in results:
            print(f"    - {result[0]}: {result[1]}")

conn.close()

# Проверим через наш класс Database
print(f"\n🔍 ПРОВЕРКА ЧЕРЕЗ КЛАСС Database:")
for query in ['прием', 'B1']:
    results = db.search_processes(query)
    print(f"  Database.search_processes('{query}'): {len(results)} результатов")
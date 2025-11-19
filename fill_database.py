import sqlite3
import json
import os
from pathlib import Path

def create_tables():
    """Создает таблицы в базе данных"""
    # Создаем папку data если ее нет
    Path("data").mkdir(exist_ok=True)
    
    conn = sqlite3.connect('data/processes.db')
    cursor = conn.cursor()
    
    # Создаем таблицу процессов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            process_id TEXT UNIQUE NOT NULL,
            process_name TEXT NOT NULL,
            description TEXT NOT NULL,
            keywords TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Таблицы созданы")

def fill_database():
    """Заполняет базу данных данными из JSON файла"""
    try:
        json_path = 'data/processes.json'
        
        # Проверяем существование файла
        if not os.path.exists(json_path):
            print(f"❌ Файл {json_path} не найден")
            return
        
        # Загружаем данные из JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            processes = json.load(f)
        
        conn = sqlite3.connect('data/processes.db')
        cursor = conn.cursor()
        
        # Очищаем таблицу перед заполнением
        cursor.execute('DELETE FROM processes')
        
        # Вставляем данные
        for process in processes:
            process_id = process.get('process_id', '')
            process_name = process.get('process_name', '')
            description = process.get('description', 'Описание отсутствует')
            keywords = process.get('keywords', '')
            
            # Проверяем, что описание не пустое
            if not description:
                description = 'Описание отсутствует'
                print(f"⚠️  Внимание: процесс {process_id} не имеет описания!")
            
            cursor.execute('''
                INSERT INTO processes (process_id, process_name, description, keywords)
                VALUES (?, ?, ?, ?)
            ''', (process_id, process_name, description, keywords))
        
        conn.commit()
        conn.close()
        
        print(f"✅ База данных заполнена. Добавлено {len(processes)} процессов")
        
        # Проверим несколько записей
        conn = sqlite3.connect('data/processes.db')
        cursor = conn.cursor()
        cursor.execute('SELECT process_id, process_name, description FROM processes LIMIT 5')
        sample_data = cursor.fetchall()
        conn.close()
        
        print("\n🔍 Проверка данных (первые 5 записей):")
        for process in sample_data:
            print(f"  {process[0]}: {process[1]} - Описание: {'Есть' if process[2] and process[2] != 'Описание отсутствует' else 'Отсутствует'}")
        
    except Exception as e:
        print(f"❌ Ошибка при заполнении базы: {e}")

if __name__ == '__main__':
    create_tables()
    fill_database()
import os
import sqlite3
import psycopg2
from urllib.parse import urlparse
import re
from typing import List, Tuple, Any, Optional
from datetime import datetime

class Database:
    def __init__(self):
        self.db_type = self.get_db_type()
        self.conn = self.get_connection()
        self.create_tables()
        self.populate_data()
    
    def get_db_type(self):
        """Определяет тип базы данных"""
        if 'DATABASE_URL' in os.environ:
            return 'postgres'
        else:
            return 'sqlite'
    
    def get_connection(self):
        """Создает соединение с базой данных"""
        if self.db_type == 'postgres':
            return self.get_postgres_connection()
        else:
            return self.get_sqlite_connection()
    
    def get_postgres_connection(self):
        """Создает соединение с PostgreSQL"""
        database_url = os.environ.get('DATABASE_URL')
        conn = psycopg2.connect(database_url, sslmode='require')
        return conn
    
    def get_sqlite_connection(self):
        """Создает соединение с SQLite"""
        os.makedirs('data', exist_ok=True)
        return sqlite3.connect('data/processes.db')
    
    def create_tables(self):
        """Создает необходимые таблицы"""
        cursor = self.conn.cursor()
        
        if self.db_type == 'postgres':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processes (
                    id SERIAL PRIMARY KEY,
                    process_id TEXT UNIQUE NOT NULL,
                    process_name TEXT NOT NULL,
                    description TEXT,
                    keywords TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS suggestions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    user_name TEXT NOT NULL,
                    username TEXT,
                    suggestion_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_id TEXT UNIQUE NOT NULL,
                    process_name TEXT NOT NULL,
                    description TEXT,
                    keywords TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    user_name TEXT NOT NULL,
                    username TEXT,
                    suggestion_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        self.conn.commit()
        cursor.close()
    
    def populate_data(self):
        """Заполняет базу данных начальными данными"""
        cursor = self.conn.cursor()
        
        # Проверяем, есть ли уже данные
        if self.db_type == 'postgres':
            cursor.execute('SELECT COUNT(*) FROM processes')
        else:
            cursor.execute('SELECT COUNT(*) FROM processes')
        
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Заполняем данными из processes.json
            import json
            try:
                with open('data/processes.json', 'r', encoding='utf-8') as f:
                    processes = json.load(f)
                
                for process in processes:
                    process_id = process.get('process_id', '')
                    process_name = process.get('process_name', '')
                    description = process.get('description', '')
                    keywords = process.get('keywords', '')
                    
                    if self.db_type == 'postgres':
                        cursor.execute('''
                            INSERT INTO processes (process_id, process_name, description, keywords)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (process_id) DO NOTHING
                        ''', (process_id, process_name, description, keywords))
                    else:
                        cursor.execute('''
                            INSERT OR IGNORE INTO processes (process_id, process_name, description, keywords)
                            VALUES (?, ?, ?, ?)
                        ''', (process_id, process_name, description, keywords))
                
                self.conn.commit()
                print(f"✅ База данных заполнена. Добавлено {len(processes)} процессов")
            except Exception as e:
                print(f"❌ Ошибка при заполнении базы: {e}")
        
        cursor.close()

    # Остальные методы остаются без изменений
    def _normalize_text(self, text: str) -> str:
        """Нормализует текст: заменяет ё на е и приводит к нижнему регистру"""
        if not text:
            return ""
        return text.lower().replace('ё', 'е')

    def _get_word_stems(self, word: str) -> List[str]:
        """Возвращает возможные основы слова для поиска с учетом нормализации е/ё"""
        word = self._normalize_text(word.strip())
        
        if len(word) < 3:
            return [word]
        
        stems = [word]
        
        # Основные правила для русского языка - улучшенная версия
        if len(word) > 4:
            # Убираем распространенные окончания прилагательных и существительных
            if (word.endswith('ой') or word.endswith('ый') or word.endswith('ий') or 
                word.endswith('ая') or word.endswith('яя') or 
                word.endswith('ое') or word.endswith('ее') or 
                word.endswith('ые') or word.endswith('ие')):
                stems.append(word[:-2])
            
            # Окончания существительных
            elif (word.endswith('ах') or word.endswith('ях') or 
                  word.endswith('ам') or word.endswith('ям') or
                  word.endswith('ами') or word.endswith('ями') or
                  word.endswith('ов') or word.endswith('ев') or
                  word.endswith('ом') or word.endswith('ем') or
                  word.endswith('ой') or word.endswith('ей')):
                stems.append(word[:-2])
                if len(word) > 5:
                    stems.append(word[:-3])  # Для более длинных слов
                    
            elif (word.endswith('у') or word.endswith('ю') or
                  word.endswith('а') or word.endswith('я') or
                  word.endswith('о') or word.endswith('е') or
                  word.endswith('ь')):
                stems.append(word[:-1])
        
        # Специальные случаи для часто используемых слов
        special_cases = {
            'расхождение': ['расхожд', 'расхожден'],
            'расхождения': ['расхожд', 'расхожден'],
            'повреждение': ['поврежден', 'поврежд'],
            'повреждения': ['поврежден', 'поврежд'],
            'зафиксировать': ['зафиксир', 'фиксир'],
            'значительный': ['значительн', 'значим'],
            'значительные': ['значительн', 'значим'],
            'недовоз': ['недовоз', 'недов'],
            'прием': ['прием', 'приём', 'принима'],
            'приём': ['прием', 'приём', 'принима'],
            'пустой': ['пуст', 'пусто'],
            'пустая': ['пуст', 'пусто'],
            'пустые': ['пуст', 'пусто'],
            'упаковка': ['упаковк', 'упаков'],
            'упаковки': ['упаковк', 'упаков'],
            'упаковку': ['упаковк', 'упаков'],
            'селлер': ['селлер', 'селер'],
            'перевозка': ['перевоз', 'перевозк'],
            'перевозки': ['перевоз', 'перевозк'],
            'размещение': ['размещен', 'размещ'],
            'проверка': ['провер', 'проверк'],
            'целостности': ['целост', 'целостн'],
            'товара': ['товар'],
            'товары': ['товар'],
        }
        
        if word in special_cases:
            stems.extend(special_cases[word])
        
        # Добавляем варианты с ё/е для текущего слова
        if 'е' in word:
            stems.append(word.replace('е', 'ё'))
        if 'ё' in word:
            stems.append(word.replace('ё', 'е'))
        
        return list(set([stem for stem in stems if len(stem) >= 3]))

    def _calculate_relevance(self, process_data: Tuple, query_stems: List[str], original_query: str) -> int:
        """Вычисляет релевантность процесса для запроса с улучшенной логикой"""
        process_id, process_name, description, keywords = process_data
        
        # Нормализуем все текстовые поля процесса
        norm_process_name = self._normalize_text(process_name)
        norm_description = self._normalize_text(description or '')
        norm_keywords = self._normalize_text(keywords or '')
        
        # Объединяем все поля для поиска
        all_text = f"{norm_process_name} {norm_description} {norm_keywords}"
        
        relevance = 0
        
        # 1. Проверяем наличие всех стемм запроса
        found_stems = 0
        for stem in query_stems:
            if stem in all_text:
                found_stems += 1
        
        # Если не найдены все стеммы, сильно понижаем релевантность
        if found_stems < len(query_stems):
            relevance -= 20
        
        # 2. Бонус за точное совпадение фразы
        norm_query = self._normalize_text(original_query)
        if norm_query in all_text:
            relevance += 50
        
        # 3. Бонус за совпадение в названии процесса
        for stem in query_stems:
            if stem in norm_process_name:
                relevance += 10
        
        # 4. Бонус за совпадение в ключевых словах
        for stem in query_stems:
            if stem in norm_keywords:
                relevance += 8
        
        # 5. Бонус за совпадение в описании
        for stem in query_stems:
            if stem in norm_description:
                relevance += 5
        
        # 6. Бонус за нахождение всех слов запроса близко друг к другу
        words_in_text = 0
        for stem in query_stems:
            if stem in all_text:
                words_in_text += 1
        
        if words_in_text == len(query_stems):
            relevance += 15
        
        return relevance

    def search_processes(self, query: str) -> List[Tuple]:
        """Улучшенный поиск процессов с точной релевантностью"""
        cursor = self.conn.cursor()
        
        # Разбиваем запрос на слова
        words = [word.strip() for word in query.split() if word.strip()]
        
        if not words:
            return []
        
        # Получаем все процессы для поиска
        cursor.execute('SELECT process_id, process_name, description, keywords FROM processes')
        all_processes = cursor.fetchall()
        
        # Создаем стеммы для всех слов запроса
        all_stems = []
        for word in words:
            stems = self._get_word_stems(word)
            all_stems.extend(stems)
        
        # Убираем дубликаты стемм
        all_stems = list(set(all_stems))
        
        # Ищем процессы и вычисляем релевантность
        results_with_relevance = []
        for process_data in all_processes:
            relevance = self._calculate_relevance(process_data, all_stems, query)
            if relevance > 0:  # Показываем только процессы с положительной релевантностью
                results_with_relevance.append((process_data, relevance))
        
        # Сортируем по релевантности (по убыванию)
        results_with_relevance.sort(key=lambda x: x[1], reverse=True)
        
        # Берем только топ-5 результатов
        top_results = results_with_relevance[:5]
        
        # Фильтруем только действительно релевантные процессы (релевантность > 10)
        final_results = [process for process, relevance in top_results if relevance > 10]
        
        cursor.close()
        return final_results
    
    def get_all_processes(self) -> List[Tuple]:
        """Возвращает все процессы в формате (process_id, process_name)"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT process_id, process_name FROM processes ORDER BY process_id')
        processes = cursor.fetchall()
        cursor.close()
        return processes
    
    def get_process_by_id(self, process_id: str) -> Optional[Tuple]:
        """Находит процесс по ID"""
        cursor = self.conn.cursor()
        if self.db_type == 'postgres':
            cursor.execute('SELECT * FROM processes WHERE process_id = %s', (process_id,))
        else:
            cursor.execute('SELECT * FROM processes WHERE process_id = ?', (process_id,))
        process = cursor.fetchone()
        cursor.close()
        return process
    
    def save_suggestion(self, user_id: int, user_name: str, username: str, suggestion_text: str) -> bool:
        """Сохраняет пожелание пользователя в базу данных"""
        try:
            cursor = self.conn.cursor()
            if self.db_type == 'postgres':
                cursor.execute('''
                    INSERT INTO suggestions (user_id, user_name, username, suggestion_text)
                    VALUES (%s, %s, %s, %s)
                ''', (user_id, user_name, username, suggestion_text))
            else:
                cursor.execute('''
                    INSERT INTO suggestions (user_id, user_name, username, suggestion_text)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, user_name, username, suggestion_text))
            
            self.conn.commit()
            cursor.close()
            return True
            
        except Exception as e:
            print(f"Ошибка при сохранении пожелания: {e}")
            return False

# Создаем глобальный экземпляр базы данных
db = Database()
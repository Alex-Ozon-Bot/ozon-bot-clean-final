from database import db

# Тестируем получение процесса по ID
test_ids = ['B1.1', 'B3.1', 'B6.6.1']

for process_id in test_ids:
    process_data = db.get_process_by_id(process_id)
    if process_data:
        print(f"Процесс {process_id}:")
        print(f"  Длина данных: {len(process_data)}")
        print(f"  Данные: {process_data}")
        print(f"  process_id: {process_data[1]}")
        print(f"  process_name: {process_data[2]}")
        print(f"  description: {process_data[3][:50]}..." if len(process_data) > 3 else "Нет описания")
        print()
    else:
        print(f"❌ Процесс {process_id} не найден")
        print()
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from config import BOT_TOKEN
from database import db

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    user = update.effective_user
    update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я бот-помощник по поиску бизнес-процессов Ozon.\n\n"
        "💡 <b>Что я умею:</b>\n"
        "• 🔍 Искать процессы по ключевым словам\n"
        "• 📋 Показывать список всех процессов\n\n"
        "<b>🔍 Начните поиск:</b>\n"
        "Напишите что ищете, например: 'прием перевозки', 'выдача заказа'",
        parse_mode='HTML'
    )

def help_command(update: Update, context: CallbackContext):
    """Обработчик команды /help"""
    update.message.reply_text(
        "🔍 <b>Как пользоваться ботом:</b>\n\n"
        "Просто введите запрос для поиска процессов.\n\n"
        "<b>Примеры запросов:</b>\n"
        "• прием перевозки\n"
        "• выдача заказа\n" 
        "• оформление недовоза\n\n"
        "Используйте /list чтобы увидеть все процессы",
        parse_mode='HTML'
    )

def list_command(update: Update, context: CallbackContext):
    """Обработчик команды /list"""
    try:
        processes = db.get_all_processes()
        
        if not processes:
            update.message.reply_text("❌ База процессов пуста.")
            return
        
        text = "📋 <b>Список бизнес-процессов:</b>\n\n"
        
        for i, process in enumerate(processes[:15], 1):
            if isinstance(process, (list, tuple)) and len(process) >= 2:
                process_id = process[0]
                process_name = process[1]
                text += f"{i}. {process_id} - {process_name}\n"
        
        text += "\n💡 Введите код процесса для деталей (например: B1.3)"
        
        update.message.reply_text(text, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Ошибка в list_command: {e}")
        update.message.reply_text("❌ Ошибка при получении списка процессов")

def handle_message(update: Update, context: CallbackContext):
    """Обработчик текстовых сообщений"""
    try:
        query = update.message.text.strip()
        
        if len(query) < 2:
            update.message.reply_text("❌ Запрос слишком короткий.")
            return
        
        # Если запрос похож на код процесса
        clean_query = query.upper().replace(' ', '')
        if any(clean_query.startswith(prefix) for prefix in ['B1', 'B2', 'B3', 'B4', 'B5', 'B6']):
            process_data = db.get_process_by_id(clean_query)
            if process_data:
                show_process_details(update, process_data)
                return
        
        # Обычный поиск
        results = db.search_processes(query)
        
        if not results:
            update.message.reply_text(
                f"❌ По запросу '{query}' ничего не найдено.\n\n"
                "💡 Попробуйте другой запрос или /list"
            )
            return
        
        # Показываем результаты
        show_simple_results(update, query, results)
            
    except Exception as e:
        logger.error(f"Ошибка в handle_message: {e}")
        update.message.reply_text("❌ Ошибка при поиске")

def show_simple_results(update: Update, query: str, results):
    """Показывает список найденных процессов"""
    try:
        text = f"🔍 Найдено процессов: {len(results)}\n"
        text += f"Запрос: '{query}'\n\n"
        
        for i, result in enumerate(results, 1):
            if isinstance(result, (list, tuple)) and len(result) >= 2:
                process_id = result[0]
                process_name = result[1]
                text += f"{i}. {process_id} - {process_name}\n"
        
        text += f"\n💡 Введите код процесса для деталей"
        
        update.message.reply_text(text)
        
    except Exception as e:
        logger.error(f"Ошибка в show_simple_results: {e}")
        update.message.reply_text(f"Найдено процессов: {len(results)}")

def show_process_details(update: Update, process_data):
    """Показывает детальную информацию о процессе"""
    try:
        if isinstance(process_data, (list, tuple)) and len(process_data) >= 5:
            process_id = process_data[1]
            process_name = process_data[2]
            description = process_data[3]
            keywords = process_data[4] if len(process_data) > 4 else ""
            
            if not description:
                description = "Описание временно недоступно."
            
            text = f"<b>{process_id} - {process_name}</b>\n\n"
            text += f"<b>Описание:</b>\n{description}"
            
            if keywords:
                text += f"\n\n<b>Ключевые слова:</b> {keywords}"
            
            update.message.reply_text(text, parse_mode='HTML')
        else:
            update.message.reply_text("❌ Ошибка данных процесса")
            
    except Exception as e:
        logger.error(f"Ошибка в show_process_details: {e}")
        update.message.reply_text("❌ Ошибка при отображении процесса")

def main():
    """Запуск бота"""
    try:
        # Создаем Updater
        updater = Updater(BOT_TOKEN, use_context=True)
        
        # Получаем диспетчер
        dp = updater.dispatcher
        
        # Добавляем обработчики
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_command))
        dp.add_handler(CommandHandler("list", list_command))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        
        # Запускаем бота
        print("🤖 Бот запускается...")
        print("📊 База данных подключена")
        print("💬 Бот готов к работе!")
        
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")

if __name__ == '__main__':
    main()
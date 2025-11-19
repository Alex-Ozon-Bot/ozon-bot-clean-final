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

# ID администратора для уведомлений
ADMIN_CHAT_ID = 324493714

def start(update: Update, context: CallbackContext):
    """Обработчик команды /start"""
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("🔍 Найти процесс", callback_data="new_search")],
        [InlineKeyboardButton("📋 Все процессы", callback_data="list_all")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я бот-помощник по поиску бизнес-процессов Ozon.\n\n"
        "💡 <b>Что я умею:</b>\n"
        "• 🔍 Искать процессы по ключевым словам\n"
        "• 📋 Показывать список всех процессов\n"
        "• 💡 Принимать предложения\n\n"
        "<b>🔍 Начните поиск:</b>\n"
        "Напишите что ищете, например: 'оформление недовоза', 'заполнение ТТН'",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

def help_command(update: Update, context: CallbackContext):
    """Обработчик команды /help"""
    update.message.reply_text(
        "🔍 <b>Как пользоваться ботом:</b>\n\n"
        "<b>Поиск процессов:</b>\n"
        "• Напишите запрос в чат\n"
        "• Примеры: 'прием перевозки', 'выдача заказа'\n\n"
        "<b>Просмотр всех процессов:</b>\n"
        "• Используйте команду /list\n\n"
        "💡 Просто введите запрос для начала!",
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
        
        # Показываем только первые 20 процессов
        for i, process in enumerate(processes[:20], 1):
            if isinstance(process, (list, tuple)) and len(process) >= 2:
                process_id = process[0]
                process_name = process[1]
                text += f"{i}. <code>{process_id}</code> - {process_name}\n"
        
        text += "\n💡 <b>Для просмотра деталей введите код процесса</b> (например: B1.3)"
        
        if len(text) > 4096:
            parts = [text[i:i+4096] for i in range(0, len(text), 4096)]
            for part in parts:
                update.message.reply_text(part, parse_mode='HTML')
        else:
            update.message.reply_text(text, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Ошибка в list_command: {e}")
        update.message.reply_text("❌ Ошибка при получении списка процессов")

def handle_message(update: Update, context: CallbackContext):
    """Обработчик текстовых сообщений"""
    try:
        query = update.message.text.strip()
        logger.info(f"Поиск: '{query}'")
        
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
        logger.info(f"Найдено результатов: {len(results)}")
        
        if not results:
            update.message.reply_text(
                f"❌ По запросу '{query}' ничего не найдено.\n\n"
                "💡 Попробуйте другой запрос или /list",
                parse_mode='HTML'
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
        text = f"🔍 <b>Найдено процессов: {len(results)}</b>\n"
        text += f"Запрос: '{query}'\n\n"
        
        for i, result in enumerate(results, 1):
            if isinstance(result, (list, tuple)) and len(result) >= 2:
                process_id = result[0]
                process_name = result[1]
                text += f"{i}. <code>{process_id}</code> - {process_name}\n"
        
        text += f"\n💡 Введите код процесса для деталей"
        
        update.message.reply_text(text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Ошибка в show_simple_results: {e}")
        simple_text = f"Найдено: {len(results)}\n"
        for i, result in enumerate(results[:10], 1):
            if isinstance(result, (list, tuple)) and len(result) >= 2:
                simple_text += f"{i}. {result[0]} - {result[1]}\n"
        update.message.reply_text(simple_text)

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
            
            if len(text) > 4000:
                text = text[:4000] + "..."
            
            update.message.reply_text(text, parse_mode='HTML')
        else:
            update.message.reply_text("❌ Ошибка данных процесса")
            
    except Exception as e:
        logger.error(f"Ошибка в show_process_details: {e}")
        update.message.reply_text("❌ Ошибка при отображении процесса")

def button_handler(update: Update, context: CallbackContext):
    """Обработчик нажатий на кнопки"""
    try:
        query = update.callback_query
        query.answer()
        
        data = query.data
        
        if data == "list_all":
            list_command_callback(query)
        elif data == "new_search":
            query.message.reply_text("🔍 Введите запрос для поиска:")
        elif data == "help":
            help_callback(query)
        elif data.startswith("show_"):
            process_id = data[5:]
            process_data = db.get_process_by_id(process_id)
            if process_data:
                show_process_callback(query, process_data)
                
    except Exception as e:
        logger.error(f"Ошибка в button_handler: {e}")

def list_command_callback(query):
    """Показывает список процессов в callback"""
    try:
        processes = db.get_all_processes()
        
        if not processes:
            query.message.reply_text("❌ База процессов пуста.")
            return
        
        text = "📋 <b>Бизнес-процессы:</b>\n\n"
        
        for process in processes[:15]:
            if isinstance(process, (list, tuple)) and len(process) >= 2:
                process_id = process[0]
                process_name = process[1]
                text += f"• <code>{process_id}</code> - {process_name}\n"
        
        query.message.reply_text(text, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Ошибка в list_command_callback: {e}")
        query.message.reply_text("❌ Ошибка")

def show_process_callback(query, process_data):
    """Показывает процесс в callback"""
    try:
        if isinstance(process_data, (list, tuple)) and len(process_data) >= 5:
            process_id = process_data[1]
            process_name = process_data[2]
            description = process_data[3]
            
            if not description:
                description = "Описание временно недоступно."
            
            text = f"<b>{process_id} - {process_name}</b>\n\n{description}"
            
            if len(text) > 4000:
                text = text[:4000] + "..."
            
            query.message.reply_text(text, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Ошибка в show_process_callback: {e}")

def help_callback(query):
    """Показывает справку в callback"""
    query.message.reply_text(
        "💡 Просто введите запрос для поиска процессов.\n"
        "Примеры: 'прием', 'выдача', 'оформление'",
        parse_mode='HTML'
    )

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
        dp.add_handler(CallbackQueryHandler(button_handler))
        
        # Запускаем бота
        print("🤖 Бот запускается...")
        print("📊 База данных подключена")
        print("💬 Бот готов!")
        
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")

if __name__ == '__main__':
    main()
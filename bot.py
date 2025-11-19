import logging
import os
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("🔍 Найти нужный процесс", callback_data="new_search")],
        [InlineKeyboardButton("📋 Список всех процессов", callback_data="list_all")],
        [InlineKeyboardButton("💡 Отправить предложение", callback_data="send_suggestion")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я бот-помощник по поиску бизнес-процессов Ozon.\n\n"
        "💡 <b>Что я умею:</b>\n"
        "• 🔍 Искать процессы по ключевым словам\n"
        "• 📋 Показывать полный список всех процессов\n"
        "• 💡 Принимать предложения по улучшению\n\n"
        "<b>🔍 Начните поиск:</b>\n"
        "Напишите что ищете, например: '<b>оформление недовоза</b>', '<b>заполнение ТТН</b>'",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    keyboard = [
        [InlineKeyboardButton("🔍 Начать поиск процесса", callback_data="new_search")],
        [InlineKeyboardButton("📋 Смотреть список всех процессов", callback_data="list_all")],
        [InlineKeyboardButton("💡 Отправить предложение", callback_data="send_suggestion")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔍 <b>Как пользоваться ботом:</b>\n\n"
        "<b>Поиск процессов:</b>\n"
        "• Напишите запрос из нескольких слов\n"
        "• Если ничего не находит, попробуйте одно-два ключевых слова\n\n"
        "<b>Примеры запросов:</b>\n"
        "• <code>прием перевозки</code>\n"
        "• <code>выдача заказа</code>\n" 
        "• <code>конфликт с клиентом</code>\n\n"
        "<b>Просмотр списка всех процессов:</b>\n"
        "• Используйте команду /list\n\n"
        "<b>💡 Есть идеи по улучшению?</b>\n"
        "• Используйте команду /suggestion\n\n"
        "<b>💡 Для поиска процесса просто введите запрос!</b>",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /list"""
    try:
        processes = db.get_all_processes()
        
        if not processes:
            await update.message.reply_text("❌ База процессов пуста.")
            return
        
        text = "📋 <b>Полный список бизнес-процессов:</b>\n\n"
        
        # Группируем процессы по категориям
        categories = {
            '🚚 ПРИЕМ И ОБРАБОТКА ПЕРЕВОЗОК (B1)': [],
            '📦 ХРАНЕНИЕ ТОВАРОВ (B2)': [],
            '👤 ВЫДАЧА ЗАКАЗОВ (B3)': [],
            '🔄 ВОЗВРАТЫ (B4)': [],
            '📤 ОТПРАВКИ НА СКЛАД (B5)': [],
            '🤝 РАБОТА С СЕЛЛЕРАМИ (B6)': []
        }
        
        for process in processes:
            if isinstance(process, (list, tuple)) and len(process) >= 2:
                process_id = process[0]
                process_name = process[1]
                
                if process_id.startswith('B1'):
                    categories['🚚 ПРИЕМ И ОБРАБОТКА ПЕРЕВОЗОК (B1)'].append((process_id, process_name))
                elif process_id.startswith('B2'):
                    categories['📦 ХРАНЕНИЕ ТОВАРОВ (B2)'].append((process_id, process_name))
                elif process_id.startswith('B3'):
                    categories['👤 ВЫДАЧА ЗАКАЗОВ (B3)'].append((process_id, process_name))
                elif process_id.startswith('B4'):
                    categories['🔄 ВОЗВРАТЫ (B4)'].append((process_id, process_name))
                elif process_id.startswith('B5'):
                    categories['📤 ОТПРАВКИ НА СКЛАД (B5)'].append((process_id, process_name))
                elif process_id.startswith('B6'):
                    categories['🤝 РАБОТА С СЕЛЛЕРАМИ (B6)'].append((process_id, process_name))
        
        # Формируем сообщение с категориями
        for category, items in categories.items():
            if items:
                text += f"\n<b>{category}:</b>\n"
                for i, (process_id, process_name) in enumerate(items[:10], 1):
                    text += f"{i}. <code>{process_id}</code> - {process_name}\n"
                if len(items) > 10:
                    text += f"   ... и еще {len(items) - 10} процессов\n"
        
        text += "\n💡 <b>Для просмотра деталей введите код процесса</b> (например: B1.3)"
        
        # Разбиваем сообщение если оно слишком длинное
        if len(text) > 4096:
            parts = [text[i:i+4096] for i in range(0, len(text), 4096)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='HTML')
        else:
            await update.message.reply_text(text, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Ошибка в list_command: {e}")
        await update.message.reply_text("❌ Ошибка при получении списка процессов")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    try:
        query = update.message.text.strip()
        logger.info(f"Поиск: '{query}'")
        
        if len(query) < 2:
            await update.message.reply_text("❌ Запрос слишком короткий. Введите хотя бы 2 символа.")
            return
        
        # Если запрос похож на код процесса
        clean_query = query.upper().replace(' ', '')
        if any(clean_query.startswith(prefix) for prefix in ['B1', 'B2', 'B3', 'B4', 'B5', 'B6']):
            process_data = db.get_process_by_id(clean_query)
            if process_data:
                await show_process_details(update, process_data)
                return
        
        # Обычный поиск
        results = db.search_processes(query)
        logger.info(f"Найдено результатов: {len(results)}")
        
        if not results:
            await update.message.reply_text(
                f"❌ По запросу '<b>{query}</b>' ничего не найдено.\n\n"
                "💡 <b>Попробуйте:</b>\n"
                "• Более простой запрос\n"
                "• /list для просмотра всех процессов\n"
                "• /help для справки",
                parse_mode='HTML'
            )
            return
        
        # Показываем пронумерованный список результатов
        await show_simple_results(update, query, results)
            
    except Exception as e:
        logger.error(f"Ошибка в handle_message: {e}")
        await update.message.reply_text("❌ Произошла ошибка при поиске")

async def show_simple_results(update: Update, query: str, results):
    """Показывает простой пронумерованный список найденных процессов"""
    try:
        text = f"🔍 <b>РЕЗУЛЬТАТЫ ПОИСКА</b>\n"
        text += f"Запрос: '<code>{query}</code>'\n"
        text += f"Найдено процессов: <b>{len(results)}</b>\n\n"
        
        # Простой пронумерованный список процессов
        for i, result in enumerate(results, 1):
            if isinstance(result, (list, tuple)) and len(result) >= 2:
                process_id = result[0]
                process_name = result[1]
            else:
                process_id = "Неизвестно"
                process_name = "Неизвестно"
            
            text += f"<b>{i}.</b> <code>{process_id}</code> - {process_name}\n"
        
        text += f"\n💡 <b>Для просмотра деталей введите код процесса</b>\n"
                
        # Добавляем кнопки для быстрого доступа
        keyboard = []
        for i, result in enumerate(results[:5], 1):
            if isinstance(result, (list, tuple)) and len(result) >= 1:
                process_id = result[0]
                button_text = f"{i}. {process_id}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"show_{process_id}")])
        
        keyboard.append([InlineKeyboardButton("📋 Все процессы", callback_data="list_all")])
        keyboard.append([InlineKeyboardButton("🔍 Новый поиск", callback_data="new_search")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, parse_mode='HTML', reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в show_simple_results: {e}")
        # Упрощенный fallback
        simple_text = f"🔍 Найдено процессов: {len(results)}\n\n"
        for i, result in enumerate(results[:10], 1):
            if isinstance(result, (list, tuple)) and len(result) >= 2:
                simple_text += f"{i}. {result[0]} - {result[1]}\n"
        
        await update.message.reply_text(simple_text, parse_mode='HTML')

async def show_process_details(update: Update, process_data):
    """Показывает детальную информацию о процессе"""
    try:
        if isinstance(process_data, (list, tuple)) and len(process_data) >= 5:
            process_id = process_data[1]
            process_name = process_data[2]
            description = process_data[3]
            keywords = process_data[4] if len(process_data) > 4 else ""
            
            if not description:
                description = "Описание временно недоступно."
            
            text = f"<b>🔄 {process_id} - {process_name}</b>\n\n"
            text += f"<b>📝 Описание:</b>\n{description}"
            
            if keywords:
                text += f"\n\n<b>🔑 Ключевые слова:</b> {keywords}"
            
            # Обрезаем если слишком длинное
            if len(text) > 4000:
                text = text[:4000] + "...\n\n<i>Описание сокращено</i>"
            
            # Клавиатура для навигации
            keyboard = [
                [InlineKeyboardButton("🔍 Новый поиск", callback_data="new_search")],
                [InlineKeyboardButton("📋 Все процессы", callback_data="list_all")],
                [InlineKeyboardButton("❓ Помощь", callback_data="help")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await update.message.reply_text("❌ Неизвестный формат данных процесса")
            
    except Exception as e:
        logger.error(f"Ошибка в show_process_details: {e}")
        await update.message.reply_text("❌ Ошибка при отображении процесса")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "list_all":
            await list_command_callback(query)
        elif data == "new_search":
            await query.message.reply_text(
                "🔍 <b>Введите запрос для поиска:</b>\n\n"
                "<b>Примеры:</b>\n"
                "• <code>прием перевозки</code>\n"
                "• <code>выдача заказа</code>\n"
                "• <code>оформление недовоза</code>",
                parse_mode='HTML'
            )
        elif data == "help":
            await help_callback(query)
        elif data == "send_suggestion":
            await suggestion_callback(query)
        elif data.startswith("show_"):
            process_id = data[5:]
            process_data = db.get_process_by_id(process_id)
            if process_data:
                await show_process_callback(query, process_data)
            else:
                await query.message.reply_text(f"❌ Процесс {process_id} не найден.")
                
    except Exception as e:
        logger.error(f"Ошибка в button_handler: {e}")

async def list_command_callback(query):
    """Показывает список процессов в callback"""
    try:
        processes = db.get_all_processes()
        
        if not processes:
            await query.message.reply_text("❌ База процессов пуста.")
            return
        
        # Создаем клавиатуру с кнопками процессов
        keyboard = []
        
        for process in processes[:20]:  # Ограничиваем показ
            if isinstance(process, (list, tuple)) and len(process) >= 2:
                process_id = process[0]
                process_name = process[1]
                
                button_text = f"{process_id} - {process_name}"
                if len(button_text) > 40:
                    button_text = button_text[:37] + "..."
                
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"show_{process_id}")])
        
        keyboard.append([InlineKeyboardButton("🔍 Новый поиск", callback_data="new_search")])
        keyboard.append([InlineKeyboardButton("❓ Помощь", callback_data="help")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "📋 <b>СПИСОК БИЗНЕС-ПРОЦЕССОВ</b>\n\n"
            "💡 <b>Для просмотра описания нажмите на процесс</b>"
        )
        
        await query.message.reply_text(text, parse_mode='HTML', reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в list_command_callback: {e}")
        await query.message.reply_text("❌ Ошибка при получении списка процессов")

async def show_process_callback(query, process_data):
    """Показывает процесс в callback"""
    try:
        if isinstance(process_data, (list, tuple)) and len(process_data) >= 5:
            process_id = process_data[1]
            process_name = process_data[2]
            description = process_data[3]
            keywords = process_data[4] if len(process_data) > 4 else ""
            
            if not description:
                description = "Описание временно недоступно."
            
            text = f"<b>🔄 {process_id} - {process_name}</b>\n\n"
            text += f"<b>📝 Описание:</b>\n{description}"
            
            if keywords:
                text += f"\n\n<b>🔑 Ключевые слова:</b> {keywords}"
            
            # Сокращаем для callback
            if len(text) > 4000:
                text = text[:4000] + "..."
            
            keyboard = [
                [InlineKeyboardButton("🔍 Новый поиск", callback_data="new_search")],
                [InlineKeyboardButton("📋 Все процессы", callback_data="list_all")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Ошибка в show_process_callback: {e}")
        await query.message.reply_text("❌ Ошибка при отображении процесса")

async def help_callback(query):
    """Показывает справку в callback"""
    keyboard = [
        [InlineKeyboardButton("🔍 Начать поиск", callback_data="new_search")],
        [InlineKeyboardButton("📋 Все процессы", callback_data="list_all")],
        [InlineKeyboardButton("💡 Предложить улучшение", callback_data="send_suggestion")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    help_text = (
        "🔍 <b>Использование бота:</b>\n\n"
        "<b>Поиск:</b>\n"
        "• Вводите запросы в чат\n"
        "• Если не находит по фразе, ищите по ключевым словам\n\n"
        "<b>Примеры запросов:</b>\n"
        "• <code>прием перевозки</code>\n"
        "• <code>выдача заказа</code>\n"
        "• <code>оформление недовоза</code>\n\n"
        "💡 Просто введите запрос для начала!"
    )
    await query.message.reply_text(help_text, parse_mode='HTML', reply_markup=reply_markup)

async def suggestion_callback(query):
    """Обработчик кнопки отправки пожелания"""
    await query.message.reply_text(
        "💡 <b>Отправьте Ваше предложение по улучшению</b>\n\n"
        "Опишите Вашу идею или замечание:\n"
        "• Работы бота\n"
        "• Бизнес-процессов\n" 
        "• Или любые другие улучшения\n\n"
        "<i>Просто напишите Ваше сообщение...</i>",
        parse_mode='HTML'
    )

def main():
    """Запуск бота"""
    try:
        # Создаем Application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("list", list_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # Запускаем бота
        print("🤖 Бот запускается...")
        print("📊 База данных подключена")
        print("🔍 Поиск активен")
        print("💬 Бот готов к работе!")
        
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")

if __name__ == '__main__':
    main()
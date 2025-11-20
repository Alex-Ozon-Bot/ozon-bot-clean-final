import time
import telegram
import logging
import asyncio
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from config import BOT_TOKEN
from database import db
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is healthy')
    
    def log_message(self, format, *args):
        return

def start_health_server():
    """Запуск HTTP сервера для проверки здоровья"""
    try:
        port = int(os.environ.get('PORT', 8080))
        server = HTTPServer(('0.0.0.0', port), HealthHandler)
        print(f"✅ Сервер здоровья запущен на порту {port}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Ошибка запуска health server: {e}")
        # Перезапуск через 5 секунд при ошибке
        time.sleep(5)
        start_health_server()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ID администратора для уведомлений (замените на ваш Telegram ID)
ADMIN_CHAT_ID = 324493714  # Ваш Telegram ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Создаем клавиатуру с кнопками
    keyboard = [
        [InlineKeyboardButton("🔍 Найти нужный процесс", callback_data="new_search")],
        [InlineKeyboardButton("📋 Список всех процессов", callback_data="list_all")],
        [InlineKeyboardButton("📄 Скачать все процессы в PDF", callback_data="get_pdf")],
        [InlineKeyboardButton("📚 Скачать Руководство по чтению процессов в нотации BPMN", callback_data="get_guide")],
        [InlineKeyboardButton("🎥 Смотреть обучающий ролик по BPMN", callback_data="bpmn_video")],
        [InlineKeyboardButton("🧪 Пройти тест по BPMN", callback_data="take_test")],
        [InlineKeyboardButton("💡 Отправить предложение", callback_data="send_suggestion")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я бот-помощник по поиску, пониманию и улучшению бизнес-процессов Ozon.\n\n"
        "💡 <b>Что я умею:</b>\n"
        "• 🔍 Искать процессы по ключевым словам\n"
        "• 📄 Отправлять PDF со всеми бизнес-процессами\n"
        "• 📋 Показывать полный список всех процессов\n"
        "• 📚 Обучать чтению BPMN-схем\n"
        "• 🎥 Показывать обучающее видео по BPMN\n"
        "• 🧪 Проверять знания по BPMN\n"
        "• 💡 Принимать предложения по улучшению\n"
        "• ❓ Помогать с использованием бота\n\n"
        "<b>📚 Руководство по чтению процессов в нотации BPMN:</b>\n"
        "Используйте команду /guide для изучения нотации\n\n"
        "<b>🎥 Обучающий ролик по BPMN:</b>\n"
        "Используйте команду /video для просмотра видео\n\n"
        "<b>🧪 Тест по BPMN:</b>\n"
        "Используйте команду /test для проверки знаний\n\n"
        "<b>📄 Полный PDF с процессами:</b>\n"
        "Используйте команду /pdf для получения полного файла\n\n"
        "<b>💡 Есть идея по улучшению или нашли несоответствия?</b>\n"
        "Используйте команду /suggestion для отправки предложений\n\n"
        "<b>🔍 Начните поиск:</b>\n"
        "Напишите что ищете, например: '<b>оформление недовоза</b>', '<b>заполнение ТТН</b>', '<b>возврат товара селлеру</b>'",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    keyboard = [
        [InlineKeyboardButton("📄 Скачать все процессы в PDF", callback_data="get_pdf")],
        [InlineKeyboardButton("📚 Скачать Руководство по чтению процессов в нотации BPMN", callback_data="get_guide")],
        [InlineKeyboardButton("🎥 Смотреть обучающий ролик по BPMN", callback_data="bpmn_video")],
        [InlineKeyboardButton("🧪 Пройти тест по BPMN", callback_data="take_test")],
        [InlineKeyboardButton("📋 Смотреть список всех процессов", callback_data="list_all")],
        [InlineKeyboardButton("💡 Отправить предложение", callback_data="send_suggestion")],
        [InlineKeyboardButton("🔍 Начать поиск процесса", callback_data="new_search")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔍 <b>Как пользоваться ботом:</b>\n\n"
        "<b>Поиск процессов:</b>\n"
        "• Напишите запрос из нескольких слов без учета регистра (можно и ТТН, и ттн)\n"
        "• Если ничего не находит по нескольким словам, то напишите одно-два ключевых слова\n\n"
        "<b>Примеры запросов:</b>\n"
        "• <code>прием перевозки</code>\n"
        "• <code>выдача заказа</code>\n" 
        "• <code>конфликт с клиентом</code>\n"
        "• <code>какие ттн отдать водителю</code>\n\n"
        "<b>Изучение BPMN:</b>\n"
        "• Используйте команду /guide для получения руководства по чтению схем процессов\n"
        "• Используйте команду /video для просмотра обучающего ролика BPMN\n"
        "• Используйте команду /test для проверки знаний по BPMN\n\n"
        "<b>Просмотр списка всех процессов:</b>\n"
        "• Используйте команду /list\n\n"
        "<b>Полный PDF со всеми процессами:</b>\n"
        "• Используйте команду /pdf\n\n"
        "<b>💡 Есть идеи по улучшению или увидели несоответствия?</b>\n"
        "• Используйте команду /suggestion для отправки предложений\n\n"
        "<b>💡 Для поиска процесса просто введите запрос!</b>",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def suggestion_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /suggestion для отправки пожеланий"""
    # Сохраняем состояние, что пользователь хочет отправить пожелание
    context.user_data['waiting_for_suggestion'] = True
    
    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_suggestion")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "💡 <b>Отправьте Ваше предложение по улучшению или найденное несоответствие</b>\n\n"
        "Опишите Вашу идею, несоответствие или предложение по улучшению:\n"
        "• Работы бота\n"
        "• Корректности бизнес-процессов\n" 
        "• Руководства по BPMN\n"
        "• Обучающих материалов\n"
        "• Или любые другие улучшения\n\n"
        "<i>Просто напишите Ваше сообщение ниже...</i>",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def handle_suggestion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текста пожелания"""
    try:
        user = update.effective_user
        suggestion_text = update.message.text.strip()
        
        if not suggestion_text:
            await update.message.reply_text("❌ Пожалуйста, введите текст предложения.")
            return
        
        # Сохраняем пожелание в базу данных
        db.save_suggestion(user.id, user.first_name, user.username, suggestion_text)
        
        # Отправляем уведомление администратору
        await notify_admin(context, user, suggestion_text)
        
        # Подтверждаем пользователю
        keyboard = [
            [InlineKeyboardButton("🔍 Новый поиск процесса", callback_data="new_search")],
            [InlineKeyboardButton("💡 Еще предложение", callback_data="send_suggestion")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "✅ <b>Спасибо за Вашу обратную связь!</b>\n\n"
            "Ваше предложение по улучшению передано кому следует и будет рассмотрено.\n"
            "Мы ценим Ваш вклад в развитие бота и бизнес-процессов!",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        
        # Сбрасываем состояние
        context.user_data['waiting_for_suggestion'] = False
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении предложения: {e}")
        await update.message.reply_text("❌ Произошла ошибка при сохранении предложения.")

async def notify_admin(context: ContextTypes.DEFAULT_TYPE, user, suggestion_text):
    """Отправляет уведомление администратору о новом пожелании"""
    try:
        admin_message = (
            "🔔 <b>НОВОЕ ПРЕДЛОЖЕНИЕ ОТ ПОЛЬЗОВАТЕЛЯ</b>\n\n"
            f"<b>Пользователь:</b> {user.first_name}\n"
            f"<b>ID:</b> {user.id}\n"
            f"<b>Username:</b> @{user.username if user.username else 'не указан'}\n"
            f"<b>Время:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"<b>Текст пожелания:</b>\n{suggestion_text}\n\n"
            "<i>Для просмотра всех пожеланий используйте команду /viewsuggestions в боте</i>"
        )
        
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_message,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления администратору: {e}")

async def view_suggestions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для просмотра пожеланий (только для администратора)"""
    try:
        user_id = update.effective_user.id
        
        # Проверяем, является ли пользователь администратором
        if user_id != ADMIN_CHAT_ID:
            await update.message.reply_text("❌ У вас нет доступа к этой команде.")
            return
        
        suggestions = db.get_all_suggestions()
        
        if not suggestions:
            await update.message.reply_text("📝 Пожеланий пока нет.")
            return
        
        text = "📝 <b>Список пожеланий от пользователей:</b>\n\n"
        
        for i, suggestion in enumerate(suggestions, 1):
            # Формат: (id, user_id, user_name, username, suggestion_text, created_at)
            if isinstance(suggestion, (list, tuple)) and len(suggestion) >= 6:
                user_name = suggestion[2]
                username = f"@{suggestion[3]}" if suggestion[3] else "без username"
                suggestion_text = suggestion[4]
                created_at = suggestion[5]
                
                text += f"<b>{i}. {user_name} ({username})</b>\n"
                text += f"<i>{created_at}</i>\n"
                text += f"<b>Текст:</b> {suggestion_text}\n"
                text += "─" * 30 + "\n\n"
        
        # Разбиваем сообщение если оно слишком длинное
        if len(text) > 4096:
            parts = [text[i:i+4096] for i in range(0, len(text), 4096)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='HTML')
        else:
            await update.message.reply_text(text, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Ошибка в view_suggestions_command: {e}")
        await update.message.reply_text("❌ Ошибка при получении списка пожеланий")

async def send_processes_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка PDF-файла с бизнес-процессами"""
    try:
        # Создаем клавиатуру с кнопками
        keyboard = [
            [InlineKeyboardButton("📦 Официальная инструкция Ozon (ПВЗ Беларусь)", url="https://univer.ozon.ru/knowledge-base/material/doc/1014414")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем PDF-файл
        with open("Бизнес-процессы Ozon ООО Технологии упаковки.pdf", "rb") as pdf_file:
            await update.message.reply_document(
                document=pdf_file,
                filename="Бизнес-процессы Ozon ООО Технологии упаковки.pdf",
                caption="📋 <b>Полный перечень бизнес-процессов Ozon</b>\n\n"
                       "Этот файл содержит все бизнес-процессы, касающиеся работы в ПВЗ Ozon.\n"
                       "Используйте поиск в боте для быстрого нахождения нужного процесса.\n"
                       "После скачивания откройте файл, включите отображение содержания или нажимая на кнопки процесов выберите нужный процесс для изучения или распечатки.\n\n"
                       "📦 <b>Дополнительная информация:</b>\n"
                       "Если вам нужна дополнительная официальная информация от Ozon, воспользуйтесь кнопкой ниже ↓",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        await update.message.reply_text(
            "❌ Файл с бизнес-процессами временно недоступен.\n"
            "Пожалуйста, обратитесь к руководителю по качеству и операционным процессам."
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке PDF: {e}")
        await update.message.reply_text("❌ Произошла ошибка при отправке файла")

async def send_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка руководства по чтению бизнес-процессов"""
    try:
        # Отправляем файл руководства
        with open("РД-1.0 Руководство по чтению БП ООО Технологии упаковки.docx", "rb") as guide_file:
            await update.message.reply_document(
                document=guide_file,
                filename="РД-1.0 Руководство по чтению бизнес-процессов.docx",
                caption="📚 <b>Руководство по чтению бизнес-процессов в нотации BPMN</b>\n\n"
                       "Это руководство поможет Вам:\n"
                       "• 📖 Научиться читать схемы BPMN\n"
                       "• 🔍 Понимать символы и обозначения\n"
                       "• 💡 Эффективно работать с бизнес-процессами\n"
                       "• 🎯 Быстрее находить нужную информацию в процессах\n\n"
                       "🎥 <b>Дополнительный материал:</b>\n"
                       "Посмотрите обучающий ролик по BPMN: /video\n\n"
                       "🧪 <b>После изучения руководства и просмотра ролика проверьте свои знания:</b>\n"
                       "Используйте команду /test для прохождения теста",
                parse_mode='HTML'
            )
    except FileNotFoundError:
        await update.message.reply_text(
            "❌ Файл руководства временно недоступен.\n"
            "Пожалуйста, обратитесь к руководителю по качеству и операционным процессам."
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке руководства: {e}")
        await update.message.reply_text("❌ Произошла ошибка при отправке руководства")

async def send_bpmn_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка ссылки на обучающий ролик по BPMN"""
    video_url = "https://youtu.be/y80ibAgdMMc"
    
    keyboard = [
        [InlineKeyboardButton("🎥 Смотреть ролик на YouTube", url=video_url)],
        [InlineKeyboardButton("📚 Скачать Руководство BPMN", callback_data="get_guide")],
        [InlineKeyboardButton("🧪 Пройти тест по BPMN", callback_data="take_test")],
        [InlineKeyboardButton("💡 Отправить предложение", callback_data="send_suggestion")],
        [InlineKeyboardButton("🔍 Начать поиск процесса", callback_data="new_search")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎥 <b>Обучающий ролик по нотации BPMN</b>\n\n"
        "Это видео поможет Вам разобраться в основах BPMN - нотации для моделирования бизнес-процессов.\n\n"
        "📝 <b>Что вы узнаете:</b>\n"
        "• Основные элементы BPMN и их назначение\n"
        "• Как читать и понимать схемы процессов\n"
        "• Примеры использования различных элементов\n"
        "• Разбор взаимосвязей всех элеметов конкретного процесса\n\n"
        "🎯 <b>Рекомендуется к просмотру:</b>\n"
        "• Всем новичкам в работе с бизнес-процессами\n"
        "• Сотрудникам, которые хотят лучше понимать схемы Ozon\n"
        "• Тем, кто готовится к тесту по BPMN или стать супер-сотрудником\n\n"
        f"🔗 <a href='{video_url}'>Ссылка на видео</a>",
        parse_mode='HTML',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

async def send_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка ссылки на тест по BPMN"""
    test_url = "https://onlinetestpad.com/pca3izxncofpk"
    video_url = "https://youtu.be/y80ibAgdMMc"
    
    keyboard = [
        [InlineKeyboardButton("🧪 Перейти к тесту", url=test_url)],
        [InlineKeyboardButton("🎥 Обучающий ролик по BPMN", callback_data="bpmn_video")],
        [InlineKeyboardButton("📚 Скачать Руководство BPMN", callback_data="get_guide")],
        [InlineKeyboardButton("💡 Отправить предложение", callback_data="send_suggestion")],
        [InlineKeyboardButton("🔍 Начать поиск процесса", callback_data="new_search")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🧪 <b>Тест по чтению бизнес-процессов в нотации BPMN</b>\n\n"
        "Проверьте свои знания по чтению и пониманию BPMN-схем!\n\n"
        "📝 <b>Что Вас ждет в тесте:</b>\n"
        "• Вопросы по основным элементам BPMN\n"
        "• Проверка понимания символов, обозначений и их взаимосвязей\n"
        "• Практические кейсы из реальной работы в ПВЗ Ozon\n\n"
        "🎯 <b>Рекомендуется:</b>\n"
        "• Изучить руководство по BPMN перед тестом\n"
        "• Посмотреть обучающий ролик: /video\n"
        "• Иметь базовое понимание порядка действий в Турбо ПВЗ\n"
        "• Выделить 5-10 минут для прохождения\n\n"
        f"🔗 <a href='{test_url}'>Ссылка на тест</a>",
        parse_mode='HTML',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

async def send_pdf_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка PDF в callback"""
    try:
        query = update.callback_query
        await query.answer()
        
        chat_id = query.message.chat_id
        
        # Создаем клавиатуру с кнопками
        keyboard = [
            [InlineKeyboardButton("📦 Официальная инструкция Ozon (ПВЗ Беларусь)", url="https://univer.ozon.ru/knowledge-base/material/doc/1014414")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем PDF-файл
        with open("Бизнес-процессы Ozon ООО Технологии упаковки.pdf", "rb") as pdf_file:
            await context.bot.send_document(
                chat_id=chat_id,
                document=pdf_file,
                filename="Бизнес-процессы Ozon ООО Технологии упаковки.pdf",
                caption="📋 <b>Полное собрание бизнес-процессов Ozon в одном файле</b>\n\n"
                       "Этот файл содержит все бизнес-процессы, касающиеся работы в ПВЗ Ozon.\n"
                       "Используйте поиск в боте для быстрого нахождения нужного процесса.\n"
                       "После скачивания откройте файл, включите отображение содержания или нажимая на кнопки процесов выберите нужный процесс для изучения или распечатки.\n\n"
                       "📦 <b>Дополнительная информация:</b>\n"
                       "Если вам нужна дополнительная официальная информация от Ozon, воспользуйтесь кнопкой ниже ↓",
                parse_mode='HTML',
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        await query.message.reply_text(
            "❌ Файл с бизнес-процессами временно недоступен.\n"
            "Пожалуйста, обратитесь к руководителю по качеству и операционным процессам."
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке PDF в callback: {e}")
        await query.message.reply_text("❌ Произошла ошибка при отправке файла")

async def send_guide_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка руководства в callback"""
    try:
        query = update.callback_query
        await query.answer()
        
        chat_id = query.message.chat_id
        # Отправляем файл руководства
        with open("РД-1.0 Руководство по чтению БП ООО Технологии упаковки.docx", "rb") as guide_file:
            await context.bot.send_document(
                chat_id=chat_id,
                document=guide_file,
                filename="РД-1.0 Руководство по чтению бизнес-процессов.docx",
                caption="📚 <b>Руководство по чтению бизнес-процессов в нотации BPMN</b>\n\n"
                       "Это руководство поможет Вам:\n"
                       "• 📖 Научиться читать схемы BPMN\n"
                       "• 🔍 Понимать символы и обозначения\n"
                       "• 💡 Эффективно работать с бизнес-процессами\n"
                       "• 🎯 Быстрее находить нужную информацию в процессах\n\n"
                       "🎥 <b>Дополнительный материал:</b>\n"
                       "Посмотрите обучающий ролик по BPMN: /video\n\n"
                       "🧪 <b>После изучения руководства проверьте свои знания:</b>\n"
                       "Используйте команду /test для прохождения теста",
                parse_mode='HTML'
            )
    except FileNotFoundError:
        await query.message.reply_text(
            "❌ Файл руководства временно недоступен.\n"
            "Пожалуйста, обратитесь к руководителю по качеству и операционным процессам."
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке руководства в callback: {e}")
        await query.message.reply_text("❌ Произошла ошибка при отправке руководства")

async def send_video_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка видео в callback"""
    query = update.callback_query
    await query.answer()
    
    video_url = "https://youtu.be/y80ibAgdMMc"
    
    keyboard = [
        [InlineKeyboardButton("🎥 Смотреть ролик на YouTube", url=video_url)],
        [InlineKeyboardButton("📚 Скачать Руководство BPMN", callback_data="get_guide")],
        [InlineKeyboardButton("🧪 Пройти тест по BPMN", callback_data="take_test")],
        [InlineKeyboardButton("💡 Отправить предложение", callback_data="send_suggestion")],
        [InlineKeyboardButton("🔍 Начать поиск процесса", callback_data="new_search")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        "🎥 <b>Обучающий ролик по нотации BPMN</b>\n\n"
        "Это видео поможет вам разобраться в основах BPMN - нотации для моделирования бизнес-процессов.\n\n"
        "📝 <b>Что вы узнаете:</b>\n"
        "• Основные элементы BPMN и их назначение\n"
        "• Как читать и понимать схемы процессов\n"
        "• Примеры использования различных элементов\n"
        "• Практические советы по работе с BPMN\n\n"
        "🎯 <b>Рекомендуется к просмотру:</b>\n"
        "• Всем новичкам в работе с бизнес-процессами\n"
        "• Сотрудникам, которые хотят лучше понимать процессы Ozon\n"
        "• Тем, кто готовится к тесту по BPMN или хочет стать суперсотрудником\n\n"
        f"🔗 <a href='{video_url}'>Ссылка на видео</a>",
        parse_mode='HTML',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

async def send_test_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка теста в callback"""
    query = update.callback_query
    await query.answer()
    
    test_url = "https://onlinetestpad.com/pca3izxncofpk"
    video_url = "https://youtu.be/y80ibAgdMMc"
    
    keyboard = [
        [InlineKeyboardButton("🧪 Перейти к тесту", url=test_url)],
        [InlineKeyboardButton("🎥 Обучающий ролик по BPMN", callback_data="bpmn_video")],
        [InlineKeyboardButton("📚 Скачать Руководство BPMN", callback_data="get_guide")],
        [InlineKeyboardButton("💡 Отправить предложение", callback_data="send_suggestion")],
        [InlineKeyboardButton("🔍 Начать поиск процесса", callback_data="new_search")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        "🧪 <b>Тест по чтению бизнес-процессов в нотации BPMN</b>\n\n"
        "Проверьте свои знания по чтению и пониманию BPMN-схем!\n\n"
        "📝 <b>Что Вас ждет в тесте:</b>\n"
        "• Вопросы по основным элементам BPMN\n"
        "• Задачи на чтение бизнес-процессов\n"
        "• Проверка понимания символов и обозначений\n"
        "• Практические кейсы из работы ПВЗ Ozon\n\n"
        "🎯 <b>Рекомендуется:</b>\n"
        "• Изучить руководство по BPMN перед тестом\n"
        "• Посмотреть обучающий ролик по BPMN\n"
        "• Иметь базовый опыт работы с процессами Ozon\n"
        "• Выделить 5-10 минут для прохождения\n\n"
        f"🔗 <a href='{test_url}'>Ссылка на тест</a>",
        parse_mode='HTML',
        reply_markup=reply_markup,
        disable_web_page_preview=True
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
            # Формат: ('B1.1', 'Ожидание перевозки')
            if isinstance(process, (list, tuple)) and len(process) >= 2:
                process_id = process[0]  # Первый элемент - process_id
                process_name = process[1]  # Второй элемент - process_name
                
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
                for i, (process_id, process_name) in enumerate(items[:10], 1):  # Ограничиваем показ
                    text += f"{i}. <code>{process_id}</code> - {process_name}\n"
                if len(items) > 10:
                    text += f"   ... и еще {len(items) - 10} процессов\n"
        
        text += "\n💡 <b>Для просмотра деталей введите код процесса</b> (например: B1.3)"
        text += "\n\n💡 <b>Нужен полный файл со всеми процессами?</b> Используйте команду /pdf"
        
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

async def debug_processes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Диагностика процессов"""
    try:
        processes = db.get_all_processes()
        
        if not processes:
            await update.message.reply_text("❌ База процессов пуста.")
            return
        
        text = f"🔍 <b>Диагностика:</b> найдено {len(processes)} процессов\n\n"
        
        # Покажем структуру первого процесса
        if processes:
            first = processes[0]
            text += f"<b>Структура первого процесса:</b>\n"
            text += f"Тип: {type(first).__name__}\n"
            text += f"Длина: {len(first)} элементов\n"
            for i, item in enumerate(first):
                text += f"{i}: {type(item).__name__} = {str(item)[:100]}\n"
            text += "\n"
        
        # Покажем несколько процессов для примера
        text += "<b>Первые 5 процессов:</b>\n"
        for i, process in enumerate(processes[:5], 1):
            if isinstance(process, (list, tuple)) and len(process) >= 2:
                process_id = process[0]
                process_name = process[1]
                text += f"{i}. {process_id} - {process_name}\n"
            else:
                text += f"{i}. Неизвестный формат: {process}\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка диагностики: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    try:
        # Проверяем, не ожидается ли от пользователя пожелание
        if context.user_data.get('waiting_for_suggestion'):
            await handle_suggestion(update, context)
            return
            
        query = update.message.text.strip()
        logger.info(f"Поиск: '{query}'")
        
        if len(query) < 2:
            await update.message.reply_text("❌ Запрос слишком короткий. Введите хотя бы 2 символа.")
            return
        
        # Если запрос похож на код процесса
        clean_query = query.upper().replace(' ', '')
        if any(clean_query.startswith(prefix) for prefix in ['B1', 'B2', 'B3', 'B4', 'B5', 'B6']):
            # Пробуем найти точное совпадение с кодом процесса
            process_data = db.get_process_by_id(clean_query)
            if process_data:
                await show_process_details(update, process_data)
                return
            else:
                # Если точного совпадения нет, делаем обычный поиск
                pass
        
        # Обычный поиск
        results = db.search_processes(query)
        logger.info(f"Найдено результатов: {len(results)}")
        
        if not results:
            await update.message.reply_text(
                f"❌ По запросу '<b>{query}</b>' ничего не найдено.\n\n"
                "💡 <b>Попробуйте:</b>\n"
                "• Более простой запрос ('отправка' вместо 'отправка на склад Ozon')\n"
                "• /list для просмотра всех процессов\n"
                "• /pdf для получения полного файла со всеми процессами\n"
                "• /help для справки по использованию",
                parse_mode='HTML'
            )
            return
        
        # Показываем пронумерованный список результатов
        await show_simple_results(update, query, results)
            
    except Exception as e:
        logger.error(f"Ошибка в handle_message: {e}")
        await update.message.reply_text("❌ Произошла ошибка при поиска")

async def show_simple_results(update: Update, query: str, results):
    """Показывает простой пронумерованный список найденных процессов"""
    try:
        text = f"🔍 <b>РЕЗУЛЬТАТЫ ПОИСКА</b>\n"
        text += f"Запрос: '<code>{query}</code>'\n"
        text += f"Найдено процессов: <b>{len(results)}</b>\n\n"
        
        # Простой пронумерованный список процессов
        for i, result in enumerate(results, 1):
            # ПРАВИЛЬНОЕ извлечение данных из результата
            # Формат результата: (process_id, process_name, description, keywords)
            if isinstance(result, (list, tuple)) and len(result) >= 2:
                # Правильные индексы для данных из базы
                process_id = result[0]  # process_id - первый элемент
                process_name = result[1]  # process_name - второй элемент
            else:
                # Если формат неправильный, используем fallback
                try:
                    # Пробуем получить доступ к атрибутам, если это объект Row
                    process_id = getattr(result, 'process_id', 'Неизвестно')
                    process_name = getattr(result, 'process_name', 'Неизвестно')
                except:
                    process_id = "Неизвестно"
                    process_name = "Неизвестно"
            
            text += f"<b>{i}.</b> <code>{process_id}</code> - {process_name}\n"
        
        text += f"\n💡 <b>Для просмотра краткого описания подходящего процесса нажмите на кнопку ниже ↓</b>\n"
                
        # Добавляем кнопки для быстрого доступа к первым процессам
        keyboard = []
        for i, result in enumerate(results[:5], 1):
            # ПРАВИЛЬНОЕ извлечение process_id для callback_data
            if isinstance(result, (list, tuple)) and len(result) >= 1:
                process_id = result[0]  # process_id - первый элемент
                # Получаем название процесса
                process_name = result[1] if len(result) > 1 else 'Процесс'
                # Укорачиваем текст кнопки если слишком длинный
                button_text = f"{i}. {process_id}"
                if len(process_name) > 20:
                    button_text += f" - {process_name[:20]}..."
                else:
                    button_text += f" - {process_name}"
                
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"show_{process_id}")])
        
        keyboard.append([InlineKeyboardButton("📄 Скачать PDF со всеми процессами", callback_data="get_pdf")])
        keyboard.append([InlineKeyboardButton("📋 Открыть перечень всех процессов", callback_data="list_all")])
        keyboard.append([InlineKeyboardButton("💡 Отправить предложение", callback_data="send_suggestion")])
        keyboard.append([InlineKeyboardButton("🔍 Новый поиск процесса", callback_data="new_search")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, parse_mode='HTML', reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в show_simple_results: {e}")
        # Упрощенный fallback с диагностикой
        simple_text = f"🔍 Найдено процессов: {len(results)}\n\n"
        for i, result in enumerate(results[:10], 1):
            try:
                if isinstance(result, (list, tuple)) and len(result) >= 2:
                    simple_text += f"{i}. {result[0]} - {result[1]}\n"
                else:
                    simple_text += f"{i}. {str(result)[:100]}\n"
            except:
                simple_text += f"{i}. Ошибка отображения\n"
        
        await update.message.reply_text(simple_text, parse_mode='HTML')

async def show_process_details(update: Update, process_data):
    """Показывает детальную информацию о процессе"""
    try:
        # Добавим диагностику
        logger.info(f"Данные процесса: {process_data}")
        
        # ПРАВИЛЬНЫЙ формат данных из SQLite: (process_id, process_name, description, keywords)
        if isinstance(process_data, (list, tuple)) and len(process_data) >= 4:
            # Правильный формат: (process_id, process_name, description, keywords)
            process_id = process_data[0]  # process_id - первый элемент
            process_name = process_data[1]  # process_name - второй элемент
            description = process_data[2]  # description - третий элемент
            keywords = process_data[3] if len(process_data) > 3 else "Ключевые слова недоступны"
            
            # Проверяем описание
            if not description:
                description = "Описание временно недоступно. Пожалуйста, обратитесь к региональному менеджеру."
                logger.warning(f"Пустое описание для процесса {process_id}")
        else:
            await update.message.reply_text("❌ Неизвестный формат данных процесса")
            return
            
        # Исправленный формат вывода
        text = f"<b>🔄 {process_id} - {process_name}</b>\n\n"
        text += f"<b>📝 Описание:</b>\n{description}"
        
        if keywords and keywords != "Ключевые слова недоступны":
            text += f"\n\n<b>🔑 Ключевые слова:</b> {keywords}"
        
        # Обрезаем если слишком длинное
        if len(text) > 4000:
            text = text[:4000] + "...\n\n<i>Описание сокращено</i>"
        
        # Клавиатура для навигации
        keyboard = [
            [InlineKeyboardButton("🔍 Новый поиск процесса", callback_data="new_search")],
            [InlineKeyboardButton("📄 Скачать PDF со всеми процессами", callback_data="get_pdf")],
            [InlineKeyboardButton("📋 Открыть перечень всех процессов", callback_data="list_all")],
            [InlineKeyboardButton("💡 Отправить предложение", callback_data="send_suggestion")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Ошибка в show_process_details: {e}")
        await update.message.reply_text("❌ Ошибка при отображении процесса")

async def show_process_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает процесс в callback"""
    try:
        query = update.callback_query
        await query.answer()
        
        process_id = query.data[5:]  # Извлекаем process_id из callback_data
        process_data = db.get_process_by_id(process_id)
        
        if not process_data:
            await query.message.reply_text(f"❌ Процесс {process_id} не найден.")
            return
            
        # Добавим диагностику
        logger.info(f"Данные процесса (callback): {process_data}")
        
        # ПРАВИЛЬНЫЙ формат данных из SQLite: (process_id, process_name, description, keywords)
        if isinstance(process_data, (list, tuple)) and len(process_data) >= 4:
            # Правильный формат: (process_id, process_name, description, keywords)
            process_id = process_data[0]  # process_id - первый элемент
            process_name = process_data[1]  # process_name - второй элемент
            description = process_data[2]  # description - третий элемент
            keywords = process_data[3] if len(process_data) > 3 else "Ключевые слова недоступны"
            
            # Проверяем описание
            if not description:
                description = "Описание временно недоступно. Пожалуйста, обратитесь к руководителю по качеству и операционным процессам."
                logger.warning(f"Пустое описание для процесса {process_id} (callback)")
        else:
            await query.message.reply_text("❌ Неизвестный формат данных процесса")
            return
            
        # Исправленный формат вывода
        text = f"<b>🔄 {process_id} - {process_name}</b>\n\n"
        text += f"<b>📝 Описание:</b>\n{description}"
        
        if keywords and keywords != "Ключевые слова недоступны":
            text += f"\n\n<b>🔑 Ключевые слова:</b> {keywords}"
        
        # Сокращаем для callback если слишком длинное
        if len(text) > 4000:
            text = text[:4000] + "..."
        
        keyboard = [
            [InlineKeyboardButton("🔍 Новый поиск процесса", callback_data="new_search")],
            [InlineKeyboardButton("📄 Скачать PDF со всеми процессами", callback_data="get_pdf")],
            [InlineKeyboardButton("📋 Открыть перечень всех процессов", callback_data="list_all")],
            [InlineKeyboardButton("💡 Отправить предложение", callback_data="send_suggestion")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем новое сообщение вместо редактирования
        await query.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Ошибка в show_process_callback: {e}")
        await query.message.reply_text("❌ Ошибка при отображении процесса")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "list_all":
            await list_command_callback(update, context)
        
        elif data == "new_search":
            # Вместо редактирования сообщения отправляем новое
            await query.message.reply_text(
                "🔍 <b>Введите запрос для поиска:</b>\n\n"
                "<b>Примеры:</b>\n"
                "• <code>селлер</code> - прием выдача и другие процессы, связанные с селлером\n"
                "• <code>оформление дубля</code> - как оформить, выдать и отправить на склад дубль\n"
                "• <code>перевозка с приложением курьера</code> - отправка перевозки, если водитель использует приложение\n"
                "• <code>особенности заказов ozon global</code> - что можно и нельзя делать при выдаче товаров Ozon global",
                parse_mode='HTML'
            )
        
        elif data == "help":
            await help_callback(update, context)
        
        elif data == "get_pdf":
            await send_pdf_callback(update, context)
        
        elif data == "get_guide":
            await send_guide_callback(update, context)
        
        elif data == "bpmn_video":
            await send_video_callback(update, context)
        
        elif data == "take_test":
            await send_test_callback(update, context)
        
        elif data == "send_suggestion":
            await suggestion_callback(update, context)
        
        elif data == "cancel_suggestion":
            await cancel_suggestion_callback(update, context)
        
        elif data.startswith("show_"):
            await show_process_callback(update, context)
        
        elif data == "ignore":
            # Игнорируем нажатия на заголовки категорий
            pass
                
    except Exception as e:
        logger.error(f"Ошибка в button_handler: {e}")

async def suggestion_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки отправки пожелания"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['waiting_for_suggestion'] = True
    
    keyboard = [
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_suggestion")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.reply_text(
        "💡 <b>Отправьте Ваше пожелание или предложение по улучшению</b>\n\n"
        "Опишите Вашу идею, замечание или предложение по улучшению:\n"
        "• Работы бота\n"
        "• Бизнес-процессов\n" 
        "• Руководства по BPMN\n"
        "• Обучающих материалов\n"
        "• Или любые другие улучшения\n\n"
        "<i>Просто напишите Ваше сообщение ниже...</i>",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

async def cancel_suggestion_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик отмены отправки пожелания"""
    query = update.callback_query
    await query.answer()
    
    if context.user_data.get('waiting_for_suggestion'):
        context.user_data['waiting_for_suggestion'] = False
        
        keyboard = [
            [InlineKeyboardButton("🔍 Новый поиск процесса", callback_data="new_search")],
            [InlineKeyboardButton("💡 Предложить позже", callback_data="send_suggestion")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            "❌ <b>Отправка пожелания отменена</b>\n\n"
            "Вы всегда можете отправить предложение позже, используя команду /suggestion или кнопку в меню.",
            parse_mode='HTML',
            reply_markup=reply_markup
        )

async def list_command_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список процессов в callback с интерактивными кнопками"""
    try:
        query = update.callback_query
        await query.answer()
        
        processes = db.get_all_processes()
        
        if not processes:
            await query.message.reply_text("❌ База процессов пуста.")
            return
        
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
        
        # Создаем клавиатуру с кнопками процессов
        keyboard = []
        
        for category_name, items in categories.items():
            if items:
                # Добавляем заголовок категории
                keyboard.append([InlineKeyboardButton(
                    f"────────── {category_name} ──────────", 
                    callback_data="ignore"
                )])
                
                # Добавляем кнопки процессов в этой категории
                for process_id, process_name in items:
                    # Создаем кнопку с callback_data для выбора процесса
                    button_text = f"{process_id} - {process_name}"
                    # Укорачиваем текст если слишком длинный
                    if len(button_text) > 40:
                        button_text = button_text[:37] + "..."
                    
                    keyboard.append([InlineKeyboardButton(
                        button_text, 
                        callback_data=f"show_{process_id}"
                    )])
        
        # Добавляем навигационные кнопки
        keyboard.append([
            InlineKeyboardButton("📄 Скачать PDF со всеми процессами", callback_data="get_pdf")
        ])
        keyboard.append([
            InlineKeyboardButton("🔍 Новый поиск", callback_data="new_search"),
            InlineKeyboardButton("💡 Предложить улучшение", callback_data="send_suggestion")
        ])
        keyboard.append([
            InlineKeyboardButton("❓ Помощь", callback_data="help")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = (
            "📋 <b>СПИСОК ВСЕХ БИЗНЕС-ПРОЦЕССОВ</b>\n\n"
            "💡 <b>Для просмотра описания процесса просто нажмите на его название в списке ниже ↓</b>\n\n"
            "Процессы сгруппированы по категориям для удобства навигации."
        )
        
        # Отправляем новое сообщение с интерактивным списком
        await query.message.reply_text(text, parse_mode='HTML', reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Ошибка в list_command_callback: {e}")
        await query.message.reply_text("❌ Ошибка при получении списка процессов")

async def debug_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Диагностика поиска"""
    try:
        query = " ".join(context.args) if context.args else "постоплата"
        results = db.search_processes(query)
        
        text = f"🔍 <b>Диагностика поиска:</b> '{query}'\n\n"
        text += f"Найдено результатов: {len(results)}\n\n"
        
        if results:
            text += "<b>Структура первого результата:</b>\n"
            first = results[0]
            text += f"Тип: {type(first).__name__}\n"
            text += f"Длина: {len(first) if isinstance(first, (list, tuple)) else 'N/A'}\n"
            
            if isinstance(first, (list, tuple)):
                for i, item in enumerate(first):
                    text += f"[{i}]: {type(item).__name__} = {str(item)[:50]}\n"
            else:
                text += f"Значение: {first}\n"
            
            text += f"\n<b>Все результаты:</b>\n"
            for i, result in enumerate(results[:5], 1):
                if isinstance(result, (list, tuple)):
                    if len(result) >= 3:
                        text += f"{i}. ID:{result[1]}, Name:{result[2]}\n"
                    elif len(result) >= 2:
                        text += f"{i}. ID:{result[0]}, Name:{result[1]}\n"
                    else:
                        text += f"{i}. {result}\n"
                else:
                    text += f"{i}. {result}\n"
        else:
            text += "Результатов нет"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка диагностики поиска: {e}")

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает справку в callback"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📄 Скачать PDF со всеми процессами", callback_data="get_pdf")],
        [InlineKeyboardButton("📚 Скачать Руководство по чтению процессов", callback_data="get_guide")],
        [InlineKeyboardButton("🎥 Смотреть обучающий ролик по BPMN", callback_data="bpmn_video")],
        [InlineKeyboardButton("🧪 Пройти тест по BPMN", callback_data="take_test")],
        [InlineKeyboardButton("💡 Отправить предложение", callback_data="send_suggestion")],
        [InlineKeyboardButton("📋 Открыть перечень всех процессов", callback_data="list_all")],
        [InlineKeyboardButton("🔍 Начать поиск процесса", callback_data="new_search")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    help_text = (
        "🔍 <b>Использование бота:</b>\n\n"
        "<b>Поиск:</b>\n"
        "• Вводите запросы в строку чата\n"
        "• Если не находит по фразе, то ищите по ключевым словам\n\n"
        "<b>Примеры запросов:</b>\n"
        "• <code>прием перевозки</code>\n• <code>прием отправлений FBO</code>\n• <code>возврат пустых ящиков</code>\n• <code>выдача</code>\n\n"
        "<b>Обучение BPMN:</b>\n"
        "• Используйте команду /guide для изучения руководства\n"
        "• Используйте команду /video для просмотра обучающего ролика\n"
        "• Используйте команду /test для проверки знаний\n\n"
        "<b>Скачать PDF со всеми процессами:</b>\n"
        "• Используйте команду /pdf или кнопку ниже\n\n"
        "<b>💡 Есть идеи по улучшению или заметили ошибки?</b>\n"
        "• Используйте команду /suggestion для отправки пожеланий\n\n"
        "💡 Просто введите запрос для начала!"
    )
    # Отправляем новое сообщение вместо редактирования
    await query.message.reply_text(help_text, parse_mode='HTML', reply_markup=reply_markup)

async def check_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверяет конкретный процесс"""
    try:
        process_id = context.args[0] if context.args else "B1.3"
        
        process_data = db.get_process_by_id(process_id)
        
        if not process_data:
            await update.message.reply_text(f"❌ Процесс {process_id} не найден")
            return
        
        text = f"🔍 <b>Диагностика процесса {process_id}:</b>\n\n"
        text += f"Тип данных: {type(process_data)}\n"
        text += f"Длина: {len(process_data) if isinstance(process_data, (list, tuple)) else 'N/A'}\n\n"
        
        if isinstance(process_data, (list, tuple)):
            for i, item in enumerate(process_data):
                text += f"[{i}]: {type(item).__name__} = {str(item)[:100]}\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка проверки: {e}")

def main():
    """Запуск бота"""
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            print(f"🔄 Попытка запуска {retry_count + 1}/{max_retries}")
            
            # Запускаем health server в отдельном потоке
            health_thread = threading.Thread(target=start_health_server, daemon=True)
            health_thread.start()
            print("✅ Health server запущен")
            
            # Даем время health server запуститься
            time.sleep(2)
            
            # Создаем Application
            application = Application.builder().token(BOT_TOKEN).build()
            print("✅ Application создано")
            
            # Добавляем обработчики
            application.add_handler(CommandHandler("start", start))
            application.add_handler(CommandHandler("help", help_command))
            application.add_handler(CommandHandler("list", list_command))
            application.add_handler(CommandHandler("pdf", send_processes_pdf))
            application.add_handler(CommandHandler("guide", send_guide))
            application.add_handler(CommandHandler("video", send_bpmn_video))
            application.add_handler(CommandHandler("test", send_test))
            application.add_handler(CommandHandler("suggestion", suggestion_command))
            application.add_handler(CommandHandler("viewsuggestions", view_suggestions_command))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            application.add_handler(CallbackQueryHandler(button_handler))
            
            print("✅ Обработчики добавлены")
            print("🤖 Бот запускается...")
            
            # Запускаем бота
            application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                poll_interval=3,
                timeout=20
            )
            
        except telegram.error.Conflict as e:
            print(f"❌ Конфликт: {e}")
            retry_count += 1
            wait_time = 10 * retry_count
            print(f"🔄 Перезапуск через {wait_time} секунд...")
            time.sleep(wait_time)
            
        except Exception as e:
            print(f"❌ Ошибка запуска бота: {e}")
            retry_count += 1
            wait_time = 30 * retry_count
            print(f"🔄 Перезапуск через {wait_time} секунд...")
            time.sleep(wait_time)
    
    print("❌ Превышено максимальное количество попыток запуска")
        main()
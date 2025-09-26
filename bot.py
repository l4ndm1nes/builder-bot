import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from database import get_or_create_user, create_request, get_active_requests, find_matches
from google_sheets import sheets_manager
from models import User, Request
from config import Config
import re

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ConstructionBot:
    def __init__(self):
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настраивает обработчики команд"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("profile", self.profile_command))
        self.application.add_handler(CommandHandler("my_requests", self.my_requests_command))
        
        # Обработчики кнопок
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Обработчики сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def start_command(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        try:
            # Получаем пользователя в зависимости от типа update
            if hasattr(update, 'effective_user') and update.effective_user:
                user = update.effective_user
            elif hasattr(update, 'from_user') and update.from_user:
                user = update.from_user
            else:
                logger.error("start_command: No user found in update")
                return
            
            db_user = get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            welcome_text = f"""
🏗️ Добро пожаловать в бот диспетчеризации строительной техники!

Привет, {user.first_name}! 

Этот бот поможет вам:
• Найти строительную технику для ваших проектов
• Найти клиентов для вашей техники
• Связаться с подходящими партнерами

Выберите, что вас интересует:
            """
            
            keyboard = [
                [InlineKeyboardButton("🔍 Ищу технику (Клиент)", callback_data="client_mode")],
                [InlineKeyboardButton("🚛 Предлагаю технику (Исполнитель)", callback_data="contractor_mode")],
                [InlineKeyboardButton("👤 Мой профиль", callback_data="profile")],
                [InlineKeyboardButton("📋 Мои заявки", callback_data="my_requests")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if hasattr(update, 'message') and update.message:
                await update.message.reply_text(welcome_text, reply_markup=reply_markup)
            elif hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup)
            else:
                logger.error(f"Unknown update type: {type(update)}")
                
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            if hasattr(update, 'message') and update.message:
                await update.message.reply_text("Произошла ошибка. Попробуйте еще раз.")
            elif hasattr(update, 'callback_query') and update.callback_query:
                await update.callback_query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
📖 Справка по боту:

🔍 **Режим клиента:**
• Создайте заявку с описанием нужной техники
• Укажите локацию, бюджет и сроки
• Получите уведомления о подходящих исполнителях

🚛 **Режим исполнителя:**
• Создайте заявку с описанием вашей техники
• Укажите цены и доступность
• Получайте уведомления о подходящих заказах

📋 **Мои заявки:**
• Просматривайте и управляйте своими заявками
• Отслеживайте статус сопоставлений

👤 **Профиль:**
• Настройте контактную информацию
• Переключайтесь между режимами клиента/исполнителя

**Команды:**
/start - Главное меню
/help - Эта справка
/profile - Настройки профиля
/my_requests - Мои заявки
        """
        await update.message.reply_text(help_text)
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /profile"""
        await self.show_profile(update, context)
    
    async def my_requests_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /my_requests"""
        await self.show_my_requests(update, context)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        logger.info(f"button_callback: Получен callback: {data}")
        logger.info(f"button_callback: Пользователь: {query.from_user.id}, {query.from_user.first_name}")
        
        try:
            if data == "client_mode":
                logger.info("button_callback: Обрабатываем client_mode")
                await self.start_client_request(query, context)
            elif data == "contractor_mode":
                logger.info("button_callback: Обрабатываем contractor_mode")
                await self.start_contractor_request(query, context)
            elif data == "profile":
                logger.info("button_callback: Обрабатываем profile")
                await self.show_profile(query, context)
            elif data == "my_requests":
                logger.info("button_callback: Обрабатываем my_requests")
                await self.show_my_requests(query, context)
            elif data == "start_menu":
                logger.info("button_callback: Обрабатываем start_menu")
                await self.start_command(query, context)
            elif data.startswith("create_request_"):
                request_type = data.split("_")[2]
                logger.info(f"button_callback: Обрабатываем create_request_{request_type}")
                await self.create_request_flow(query, context, request_type)
            elif data == "toggle_mode":
                logger.info("button_callback: Обрабатываем toggle_mode")
                await self.toggle_mode(query, context)
            elif data == "set_phone":
                logger.info("button_callback: Обрабатываем set_phone")
                await self.set_phone(query, context)
            elif data == "contact_message":
                logger.info("button_callback: Обрабатываем contact_message")
                await self.handle_contact_preference(query, context, "message")
            elif data == "contact_call":
                logger.info("button_callback: Обрабатываем contact_call")
                await self.handle_contact_preference(query, context, "call")
            else:
                # Обработка неизвестных callback'ов
                logger.warning(f"button_callback: Неизвестный callback: {data}")
                await query.edit_message_text("Неизвестная команда. Используйте /start для возврата в главное меню.")
        except Exception as e:
            logger.error(f"button_callback: Ошибка при обработке {data}: {e}", exc_info=True)
            try:
                await query.edit_message_text("Произошла ошибка. Попробуйте еще раз или используйте /start.")
            except Exception as e2:
                logger.error(f"button_callback: Ошибка при отправке сообщения об ошибке: {e2}")
    
    async def start_client_request(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Начинает процесс создания заявки клиента"""
        text = """
🔍 Создание заявки клиента

Вы ищете строительную технику? Отлично!

Для создания заявки мне понадобится следующая информация:
• Тип техники (экскаватор, кран, бульдозер и т.д.)
• Локация работ
• Описание работ
• Бюджет
• Сроки выполнения

Готовы начать?
        """
        
        keyboard = [
            [InlineKeyboardButton("✅ Да, создать заявку", callback_data="create_request_client")],
            [InlineKeyboardButton("❌ Отмена", callback_data="start_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    async def start_contractor_request(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Начинает процесс создания заявки исполнителя"""
        text = """
🚛 Создание заявки исполнителя

Вы предлагаете строительную технику? Отлично!

Для создания заявки мне понадобится следующая информация:
• Доступная техника
• Локация работы
• Опыт работы
• Цены
• Контактная информация

Готовы начать?
        """
        
        keyboard = [
            [InlineKeyboardButton("✅ Да, создать заявку", callback_data="create_request_contractor")],
            [InlineKeyboardButton("❌ Отмена", callback_data="start_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    async def create_request_flow(self, query, context: ContextTypes.DEFAULT_TYPE, request_type: str):
        """Начинает поток создания заявки"""
        context.user_data['creating_request'] = True
        context.user_data['request_type'] = request_type
        context.user_data['request_data'] = {}
        
        if request_type == 'client':
            text = """
🔍 Создание заявки клиента

Шаг 1/5: Тип техники

Укажите тип строительной техники, которая вам нужна:
(например: экскаватор, кран, бульдозер, самосвал, автобетоносмеситель)
            """
        else:
            text = """
🚛 Создание заявки исполнителя

Шаг 1/5: Доступная техника

Укажите какую строительную технику вы можете предоставить:
(например: экскаватор JCB, кран 25т, бульдозер CAT)
            """
        
        await query.edit_message_text(text)
    
    async def show_profile(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает профиль пользователя"""
        try:
            logger.info("show_profile: Начало функции")
            
            # Получаем пользователя в зависимости от типа update
            if hasattr(update, 'effective_user') and update.effective_user:
                user = update.effective_user
            elif hasattr(update, 'from_user') and update.from_user:
                user = update.from_user
            else:
                logger.error("show_profile: No user found in update")
                return
            
            logger.info(f"show_profile: Пользователь: {user.id}, {user.first_name}")
                
            db_user = get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            logger.info(f"show_profile: DB пользователь создан/найден: {db_user.id}")
            
            profile_text = f"""
👤 Ваш профиль:

🆔 ID: {db_user.telegram_id}
👤 Имя: {db_user.first_name} {db_user.last_name or ''}
📱 Username: @{db_user.username or 'не указан'}
📞 Телефон: {db_user.phone or 'не указан'}
🏗️ Режим: {'Исполнитель' if db_user.is_contractor else 'Клиент'}
📅 Регистрация: {db_user.created_at.strftime('%d.%m.%Y')}
            """
            
            keyboard = [
                [InlineKeyboardButton("📞 Указать телефон", callback_data="set_phone")],
                [InlineKeyboardButton("🔄 Переключить режим", callback_data="toggle_mode")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="start_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            logger.info("show_profile: Отправляем сообщение")
            if hasattr(update, 'message') and update.message:
                logger.info("show_profile: Отправляем через message")
                await update.message.reply_text(profile_text, reply_markup=reply_markup)
            elif hasattr(update, 'callback_query') and update.callback_query:
                logger.info("show_profile: Отправляем через callback_query")
                await update.callback_query.edit_message_text(profile_text, reply_markup=reply_markup)
            else:
                logger.error(f"show_profile: Неизвестный тип update: {type(update)}")
                
        except Exception as e:
            logger.error(f"show_profile: Ошибка: {e}", exc_info=True)
            error_text = "Произошла ошибка при загрузке профиля. Попробуйте еще раз."
            try:
                if hasattr(update, 'message') and update.message:
                    await update.message.reply_text(error_text)
                elif hasattr(update, 'callback_query') and update.callback_query:
                    await update.callback_query.edit_message_text(error_text)
            except Exception as e2:
                logger.error(f"show_profile: Ошибка при отправке сообщения об ошибке: {e2}")
    
    async def show_my_requests(self, update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает заявки пользователя"""
        try:
            logger.info("show_my_requests: Начало функции")
            
            # Получаем пользователя в зависимости от типа update
            if hasattr(update, 'effective_user') and update.effective_user:
                user = update.effective_user
            elif hasattr(update, 'from_user') and update.from_user:
                user = update.from_user
            else:
                logger.error("show_my_requests: No user found in update")
                return
            
            logger.info(f"show_my_requests: Пользователь: {user.id}, {user.first_name}")
                
            db_user = get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            logger.info(f"show_my_requests: DB пользователь создан/найден: {db_user.id}")
            
            # Получаем заявки пользователя из базы данных
            from database import SessionLocal, Request
            logger.info("show_my_requests: Подключаемся к базе данных")
            db = SessionLocal()
            try:
                logger.info(f"show_my_requests: Ищем заявки для пользователя {db_user.id}")
                user_requests = db.query(Request).filter(Request.user_id == db_user.id).order_by(Request.created_at.desc()).all()
                logger.info(f"show_my_requests: Найдено заявок: {len(user_requests)}")
                
                if not user_requests:
                    text = """
📋 Ваши заявки:

У вас пока нет активных заявок.

Создайте первую заявку, чтобы начать поиск партнеров!
                    """
                    logger.info("show_my_requests: Нет заявок, показываем заглушку")
                else:
                    text = "📋 Ваши заявки:\n\n"
                    for req in user_requests[:5]:  # Показываем последние 5 заявок
                        status_emoji = "✅" if req.status == "active" else "⏸️"
                        type_emoji = "🔍" if req.request_type == "client" else "🚛"
                        text += f"{status_emoji} {type_emoji} ID: {req.id}\n"
                        text += f"   📍 {req.location}\n"
                        text += f"   📅 {req.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                        text += f"   📊 Статус: {req.status}\n\n"
                    
                    if len(user_requests) > 5:
                        text += f"... и еще {len(user_requests) - 5} заявок"
                    logger.info(f"show_my_requests: Сформирован текст с {len(user_requests)} заявками")
                
            finally:
                db.close()
                logger.info("show_my_requests: База данных закрыта")
            
            keyboard = [
                [InlineKeyboardButton("➕ Создать заявку", callback_data="start_menu")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="start_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            logger.info("show_my_requests: Отправляем сообщение")
            if hasattr(update, 'message') and update.message:
                logger.info("show_my_requests: Отправляем через message")
                await update.message.reply_text(text, reply_markup=reply_markup)
            elif hasattr(update, 'callback_query') and update.callback_query:
                logger.info("show_my_requests: Отправляем через callback_query")
                await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
            else:
                logger.error(f"show_my_requests: Неизвестный тип update: {type(update)}")
                
        except Exception as e:
            logger.error(f"show_my_requests: Ошибка: {e}", exc_info=True)
            error_text = "Произошла ошибка при загрузке заявок. Попробуйте еще раз."
            try:
                if hasattr(update, 'message') and update.message:
                    await update.message.reply_text(error_text)
                elif hasattr(update, 'callback_query') and update.callback_query:
                    await update.callback_query.edit_message_text(error_text)
            except Exception as e2:
                logger.error(f"show_my_requests: Ошибка при отправке сообщения об ошибке: {e2}")
    
    async def toggle_mode(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Переключает режим пользователя между клиентом и исполнителем"""
        try:
            user = query.from_user
            db_user = get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Переключаем режим
            db_user.is_contractor = not db_user.is_contractor
            from database import SessionLocal
            db = SessionLocal()
            try:
                db.merge(db_user)
                db.commit()
            finally:
                db.close()
            
            # Показываем обновленное меню
            await self.start_command(query, context)
            
        except Exception as e:
            logger.error(f"toggle_mode: Ошибка: {e}", exc_info=True)
            await query.edit_message_text("Произошла ошибка при переключении режима. Попробуйте еще раз.")
    
    async def set_phone(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Запрашивает у пользователя номер телефона"""
        try:
            text = """
📞 **Укажите номер телефона**

Пожалуйста, отправьте ваш номер телефона в формате:
• +380501234567
• 0501234567
• (050) 123-45-67

Это поможет другим пользователям связаться с вами.
            """
            
            keyboard = [
                [InlineKeyboardButton("❌ Отмена", callback_data="start_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
            
            # Устанавливаем флаг ожидания телефона
            context.user_data['waiting_for_phone'] = True
            
        except Exception as e:
            logger.error(f"set_phone: Ошибка: {e}", exc_info=True)
            await query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")
    
    async def handle_phone_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает ввод номера телефона"""
        try:
            phone = update.message.text.strip()
            
            # Простая валидация телефона
            import re
            phone_pattern = r'^(\+?38)?0\d{9}$'
            clean_phone = re.sub(r'[^\d+]', '', phone)
            
            if not re.match(phone_pattern, clean_phone):
                await update.message.reply_text(
                    "❌ Неверный формат номера телефона.\n\n"
                    "Пожалуйста, используйте формат:\n"
                    "• +380501234567\n"
                    "• 0501234567\n\n"
                    "Попробуйте еще раз:"
                )
                return
            
            # Сохраняем телефон в базе данных
            user = update.effective_user
            db_user = get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            db_user.phone = clean_phone
            from database import SessionLocal
            db = SessionLocal()
            try:
                db.merge(db_user)
                db.commit()
            finally:
                db.close()
            
            # Очищаем флаг ожидания
            context.user_data.pop('waiting_for_phone', None)
            
            # Показываем успешное сообщение
            success_text = f"""
✅ **Номер телефона сохранен!**

📞 Ваш телефон: {clean_phone}

Теперь другие пользователи смогут связаться с вами.
            """
            
            keyboard = [
                [InlineKeyboardButton("👤 Мой профиль", callback_data="profile")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="start_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(success_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"handle_phone_input: Ошибка: {e}", exc_info=True)
            await update.message.reply_text("Произошла ошибка при сохранении телефона. Попробуйте еще раз.")
    
    async def handle_contact_preference(self, query, context: ContextTypes.DEFAULT_TYPE, preference: str):
        """Обрабатывает выбор способа связи"""
        try:
            # Получаем данные заявки
            request_data = context.user_data.get('request_data', {})
            request_type = context.user_data.get('request_type', 'client')
            
            # Добавляем предпочтение связи
            request_data['contact_preference'] = preference
            
            # Очищаем флаги
            context.user_data.pop('waiting_for_contact_preference', None)
            context.user_data.pop('request_data', None)
            context.user_data.pop('request_type', None)
            
            # Создаем заявку
            await self.finish_request_creation(query, context, request_data, request_type)
            
        except Exception as e:
            logger.error(f"handle_contact_preference: Ошибка: {e}", exc_info=True)
            await query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        if context.user_data.get('creating_request'):
            await self.handle_request_creation(update, context)
        elif context.user_data.get('waiting_for_phone'):
            await self.handle_phone_input(update, context)
        else:
            await update.message.reply_text(
                "Используйте команды или кнопки для навигации. /help - для справки."
            )
    
    async def handle_request_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает создание заявки пошагово"""
        text = update.message.text
        request_data = context.user_data.get('request_data', {})
        request_type = context.user_data.get('request_type')
        step = len(request_data) + 1
        
        if step == 1:
            if request_type == 'client':
                request_data['equipment_type'] = text
                await update.message.reply_text("Шаг 2/5: Локация\n\nУкажите город или область, где нужна техника:")
            else:
                request_data['available_equipment'] = text
                await update.message.reply_text("Шаг 2/5: Локация\n\nУкажите город или область, где вы работаете:")
        
        elif step == 2:
            request_data['location'] = text
            if request_type == 'client':
                await update.message.reply_text("Шаг 3/5: Описание работ\n\nОпишите, какие работы нужно выполнить:")
            else:
                await update.message.reply_text("Шаг 3/5: Опыт работы\n\nСколько лет вы работаете в сфере строительной техники?")
        
        elif step == 3:
            if request_type == 'client':
                request_data['description'] = text
                await update.message.reply_text("Шаг 4/5: Бюджет\n\nУкажите ваш бюджет в гривнах:")
            else:
                try:
                    request_data['experience_years'] = int(text)
                    await update.message.reply_text("Шаг 4/5: Цена за час\n\nУкажите стоимость аренды за час в гривнах:")
                except ValueError:
                    await update.message.reply_text("Пожалуйста, укажите количество лет числом:")
                    return
        
        elif step == 4:
            if request_type == 'client':
                try:
                    request_data['budget'] = float(text)
                    await update.message.reply_text("Шаг 5/5: Сроки\n\nНа сколько дней нужна техника?")
                except ValueError:
                    await update.message.reply_text("Пожалуйста, укажите бюджет числом:")
                    return
            else:
                try:
                    request_data['price_per_hour'] = float(text)
                    await update.message.reply_text("Шаг 5/5: Контактная информация\n\nУкажите ваш номер телефона:")
                except ValueError:
                    await update.message.reply_text("Пожалуйста, укажите цену числом:")
                    return
        
        elif step == 5:
            if request_type == 'client':
                request_data['work_duration'] = text
                # Переходим к выбору способа связи
                await self.ask_contact_preference(update, context, request_data, request_type)
            else:
                # Обновляем телефон пользователя в базе данных
                user = update.effective_user
                from database import SessionLocal
                db = SessionLocal()
                try:
                    db_user = get_or_create_user(
                        telegram_id=user.id,
                        username=user.username,
                        first_name=user.first_name,
                        last_name=user.last_name
                    )
                    db_user.phone = text
                    db.commit()  # Сохраняем изменения
                    print(f"Телефон пользователя обновлен: {text}")
                finally:
                    db.close()
                # Переходим к выбору способа связи
                await self.ask_contact_preference(update, context, request_data, request_type)
        
        context.user_data['request_data'] = request_data
    
    async def ask_contact_preference(self, update: Update, context: ContextTypes.DEFAULT_TYPE, request_data: dict, request_type: str):
        """Спрашивает предпочтения по способу связи"""
        text = """
📞 **Как с вами лучше связаться?**

Выберите предпочтительный способ связи:
        """
        
        keyboard = [
            [InlineKeyboardButton("💬 Написать в Telegram", callback_data="contact_message")],
            [InlineKeyboardButton("📞 Позвонить по телефону", callback_data="contact_call")],
            [InlineKeyboardButton("❌ Отмена", callback_data="start_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
        
        # Устанавливаем флаг ожидания выбора способа связи
        context.user_data['waiting_for_contact_preference'] = True
        context.user_data['request_data'] = request_data
        context.user_data['request_type'] = request_type
    
    async def finish_request_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, request_data: dict, request_type: str):
        """Завершает создание заявки"""
        user = update.effective_user
        from database import SessionLocal
        db = SessionLocal()
        try:
            db_user = get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Создаем заголовок
            if request_type == 'client':
                title = f"Ищу {request_data.get('equipment_type', 'технику')} в {request_data.get('location', '')}"
            else:
                title = f"Предлагаю {request_data.get('available_equipment', 'технику')} в {request_data.get('location', '')}"
            
            # Создаем заявку в базе данных
            request = create_request(
                user_id=db_user.id,
                request_type=request_type,
                title=title,
                contact_preference=request_data.get('contact_preference', 'message'),
                **request_data
            )
            
            # Добавляем в Google Sheets
            sheets_manager.add_request(request, db_user)
            
            # Очищаем данные пользователя
            context.user_data.pop('creating_request', None)
            context.user_data.pop('request_type', None)
            context.user_data.pop('request_data', None)
            
            success_text = f"""
✅ Заявка успешно создана!

🆔 ID заявки: {request.id}
📋 Тип: {'Клиент' if request_type == 'client' else 'Исполнитель'}
📍 Локация: {request_data.get('location', '')}
📅 Создана: {request.created_at.strftime('%d.%m.%Y %H:%M')}

Ваша заявка добавлена в систему и будет рассмотрена диспетчером. 
Вы получите уведомления о подходящих совпадениях!
            """
            
            keyboard = [
                [InlineKeyboardButton("📋 Мои заявки", callback_data="my_requests")],
                [InlineKeyboardButton("➕ Создать еще заявку", callback_data="start_menu")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="start_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(success_text, reply_markup=reply_markup)
            
        finally:
            db.close()
    
    def run(self):
        """Запускает бота"""
        logger.info("Запуск бота...")
        self.application.run_polling()

if __name__ == '__main__':
    from database import create_tables
    create_tables()
    
    bot = ConstructionBot()
    bot.run()

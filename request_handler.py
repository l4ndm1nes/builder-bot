#!/usr/bin/env python3
"""
Простой обработчик создания заявок
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_or_create_user, create_request
from sync_sheets import sheets_sync
from config import Config
from models import User

logger = logging.getLogger(__name__)

class RequestHandler:
    def __init__(self):
        self.steps = {
            'client': [
                {'key': 'equipment_type', 'question': 'Шаг 1/5: Тип техники\n\nУкажите тип строительной техники, которая вам нужна:\n(например: экскаватор, кран, бульдозер, самосвал, автобетоносмеситель)'},
                {'key': 'location', 'question': 'Шаг 2/5: Локация\n\nУкажите город или область, где нужна техника:'},
                {'key': 'description', 'question': 'Шаг 3/5: Описание работ\n\nОпишите, какие работы нужно выполнить:'},
                {'key': 'budget', 'question': 'Шаг 4/5: Бюджет\n\nУкажите ваш бюджет в гривнах:', 'type': 'float'},
                {'key': 'work_duration', 'question': 'Шаг 5/5: Сроки\n\nНа сколько дней нужна техника?'},
            ],
            'contractor': [
                {'key': 'available_equipment', 'question': 'Шаг 1/5: Тип техники\n\nКакую технику вы предлагаете?\n(например: самосвал 25 тонн, трактор, автокран 50т)'},
                {'key': 'location', 'question': 'Шаг 2/5: Локация\n\nУкажите город или область, где вы работаете:'},
                {'key': 'experience_years', 'question': 'Шаг 3/5: Опыт работы\n\nСколько лет вы работаете в сфере строительной техники?', 'type': 'int'},
                {'key': 'price_per_hour', 'question': 'Шаг 4/5: Цена за час\n\nУкажите стоимость аренды за час в гривнах:', 'type': 'float'},
                {'key': 'phone', 'question': 'Шаг 5/5: Контактная информация\n\nУкажите ваш номер телефона:'},
            ]
        }
    
    def start_request(self, request_type: str, context: ContextTypes.DEFAULT_TYPE):
        """Начинает создание заявки"""
        context.user_data['request_handler'] = {
            'type': request_type,
            'step': 0,
            'data': {}
        }
        print(f"DEBUG: start_request - request_type={request_type}, user_data={context.user_data}")
        # Возвращаем первый вопрос
        return self.steps[request_type][0]['question']
    
    def get_current_step_question(self, context: ContextTypes.DEFAULT_TYPE):
        """Возвращает вопрос для текущего шага"""
        handler_data = context.user_data.get('request_handler', {})
        request_type = handler_data.get('type')
        step = handler_data.get('step', 0)
        
        if not request_type or step >= len(self.steps[request_type]):
            return None
            
        return self.steps[request_type][step]['question']
    
    def process_step(self, text: str, context: ContextTypes.DEFAULT_TYPE):
        handler_data = context.user_data.get('request_handler', {})
        request_type = handler_data.get('type')
        step = handler_data.get('step', 0)
        data = handler_data.get('data', {})
        
        print(f"DEBUG: step={step}, request_type={request_type}")
        
        if not request_type or step >= len(self.steps[request_type]):
            return {'error': 'Ошибка'}
        
        step_config = self.steps[request_type][step]
        key = step_config['key']
        value_type = step_config.get('type', 'str')
        
        print(f"DEBUG: key={key}, value_type={value_type}")
        
        try:
            if value_type == 'int':
                value = int(text)
            elif value_type == 'float':
                value = float(text)
            else:
                value = text
        except ValueError:
            return {'error': 'Укажите число'}
        
        data[key] = value
        step += 1
        
        context.user_data['request_handler'] = {
            'type': request_type,
            'step': step,
            'data': data
        }
        
        if step >= len(self.steps[request_type]):
            return {'completed': True, 'data': data, 'type': request_type}
        
        return {'question': self.steps[request_type][step]['question']}
    
    def create_contact_preference_keyboard(self):
        """Создает клавиатуру для выбора способа связи"""
        keyboard = [
            [InlineKeyboardButton("💬 Написать в Telegram", callback_data="contact_message")],
            [InlineKeyboardButton("📞 Позвонить по телефону", callback_data="contact_call")],
            [InlineKeyboardButton("❌ Отмена", callback_data="start_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def finish_request(self, update_or_query, context: ContextTypes.DEFAULT_TYPE, contact_preference: str):
        """Завершает создание заявки"""
        try:
            handler_data = context.user_data.get('request_handler', {})
            request_type = handler_data.get('type')
            data = handler_data.get('data', {})
            
            # Получаем пользователя
            if hasattr(update_or_query, 'effective_user'):
                user = update_or_query.effective_user
            elif hasattr(update_or_query, 'from_user'):
                user = update_or_query.from_user
            else:
                raise Exception("Пользователь не найден")
            
            # Создаем пользователя в БД
            db_user = get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Обновляем телефон если указан (для исполнителей)
            if request_type == 'contractor' and 'phone' in data:
                from database import SessionLocal
                db = SessionLocal()
                try:
                    # Получаем пользователя в новой сессии
                    fresh_user = db.query(User).filter(User.telegram_id == user.id).first()
                    if fresh_user:
                        fresh_user.phone = data['phone']
                        db.commit()
                        # Обновляем db_user.id для создания заявки
                        user_id = fresh_user.id
                    else:
                        logger.error(f"Пользователь с telegram_id {user.id} не найден")
                        user_id = db_user.id
                except Exception as e:
                    logger.error(f"Ошибка обновления телефона: {e}")
                    user_id = db_user.id
                finally:
                    db.close()
            else:
                user_id = db_user.id
            
            # Создаем заголовок
            if request_type == 'client':
                title = f"Ищу {data.get('equipment_type', 'технику')} в {data.get('location', '')}"
            else:
                title = f"Предлагаю {data.get('available_equipment', 'технику')} в {data.get('location', '')}"
            
            # Создаем заявку
            request_data = data.copy()
            request_data['contact_preference'] = contact_preference
            
            # Убираем phone из данных заявки (он относится к User, а не к Request)
            if 'phone' in request_data:
                del request_data['phone']
            
            request = create_request(
                user_id=user_id,
                request_type=request_type,
                title=title,
                **request_data
            )
            
            # Добавляем в Google Sheets
            sheets_sync.add_request_to_sheets(request, db_user)
            
            # Уведомляем админа
            await self.notify_admin(request, db_user)
            
            # Очищаем данные
            context.user_data.pop('request_handler', None)
            
            # Формируем сообщение об успехе
            success_text = f"""
✅ Заявка успешно создана!

🆔 ID заявки: {request.id}
📋 Тип: {'Клиент' if request_type == 'client' else 'Исполнитель'}
📍 Локация: {data.get('location', '')}
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
            
            # Отправляем сообщение
            if hasattr(update_or_query, 'message'):
                await update_or_query.message.reply_text(success_text, reply_markup=reply_markup)
            elif hasattr(update_or_query, 'edit_message_text'):
                await update_or_query.edit_message_text(success_text, reply_markup=reply_markup)
            
            return True
            
        except Exception as e:
            logger.error(f"finish_request: Ошибка: {e}", exc_info=True)
            
            error_text = "Произошла ошибка при создании заявки. Попробуйте еще раз."
            if hasattr(update_or_query, 'message'):
                await update_or_query.message.reply_text(error_text)
            elif hasattr(update_or_query, 'edit_message_text'):
                await update_or_query.edit_message_text(error_text)
            
            return False
    
    async def notify_admin(self, request, user):
        """Уведомляет админа о новой заявке"""
        try:
            admin_id = Config.ADMIN_USER_ID
            if not admin_id:
                return
            
            type_emoji = "🔍" if request.request_type == "client" else "🚛"
            contact_emoji = "💬" if request.contact_preference == "message" else "📞"
            
            admin_message = f"""
🆕 **Новая заявка #{request.id}**

{type_emoji} **Тип:** {'Клиент' if request.request_type == 'client' else 'Исполнитель'}
👤 **Пользователь:** {user.first_name} {user.last_name or ''}
📞 **Телефон:** {user.phone or 'Не указан'}
📍 **Локация:** {request.location}
📝 **Заголовок:** {request.title}
{contact_emoji} **Связь:** {request.contact_preference}

📅 **Создана:** {request.created_at.strftime('%d.%m.%Y %H:%M')}
            """
            
            from telegram import Bot
            bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
            await bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"notify_admin: Ошибка: {e}")

# Глобальный экземпляр
request_handler = RequestHandler()

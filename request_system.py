"""
Система создания заявок на основе связного списка
Каждый шаг знает только следующий шаг
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

class RequestStep:
    """Один шаг в создании заявки"""
    def __init__(self, step_id, field_name, question, next_step=None, validation_type='str'):
        self.step_id = step_id
        self.field_name = field_name
        self.question = question
        self.next_step = next_step
        self.validation_type = validation_type
    
    def validate_input(self, text):
        """Валидирует ввод"""
        try:
            if self.validation_type == 'int':
                return int(text), None
            elif self.validation_type == 'float':
                return float(text), None
            else:
                return text.strip(), None
        except ValueError:
            return None, f"Пожалуйста, введите корректное значение ({self.validation_type})"

class RequestFlow:
    """Поток создания заявки"""
    def __init__(self):
        self.steps = {}
        self.start_step = None
    
    def add_step(self, step):
        """Добавляет шаг в поток"""
        self.steps[step.step_id] = step
        if self.start_step is None:
            self.start_step = step.step_id
    
    def get_step(self, step_id):
        """Получает шаг по ID"""
        return self.steps.get(step_id)

class RequestSystem:
    def __init__(self):
        self.flows = {}
        self._create_flows()
    
    def _create_flows(self):
        """Создает потоки для клиентов и исполнителей"""
        
        # === ПОТОК ДЛЯ КЛИЕНТОВ ===
        client_flow = RequestFlow()
        
        # Шаг 1: Тип техники
        step1 = RequestStep(
            'equipment_type',
            'equipment_type',
            'Шаг 1/6: Тип техники\n\nУкажите тип строительной техники, которая вам нужна:\n(например: экскаватор, кран, бульдозер, самосвал)',
            'location'
        )
        
        # Шаг 2: Локация
        step2 = RequestStep(
            'location',
            'location',
            'Шаг 2/6: Локация\n\nУкажите город или область, где нужна техника:',
            'description'
        )
        
        # Шаг 3: Описание
        step3 = RequestStep(
            'description',
            'description',
            'Шаг 3/6: Описание работ\n\nОпишите, какие работы нужно выполнить:',
            'budget'
        )
        
        # Шаг 4: Бюджет
        step4 = RequestStep(
            'budget',
            'budget',
            'Шаг 4/6: Бюджет\n\nУкажите ваш бюджет в гривнах:',
            'work_duration',
            'float'
        )
        
        # Шаг 5: Сроки
        step5 = RequestStep(
            'work_duration',
            'work_duration',
            'Шаг 5/6: Сроки\n\nНа сколько дней нужна техника:',
            'phone_client'
        )
        
        # Шаг 6: Телефон для клиента
        step6 = RequestStep(
            'phone_client',
            'phone',
            'Шаг 6/6: Контактная информация\n\nУкажите ваш номер телефона:',
            'contact_preference'
        )
        
        # Шаг 7: Способ связи (кнопки)
        step7 = RequestStep(
            'contact_preference',
            'contact_preference',
            'Шаг 7/7: Способ связи\n\nКак с вами лучше связаться?',
            None  # Последний шаг
        )
        
        client_flow.add_step(step1)
        client_flow.add_step(step2)
        client_flow.add_step(step3)
        client_flow.add_step(step4)
        client_flow.add_step(step5)
        client_flow.add_step(step6)
        client_flow.add_step(step7)
        
        self.flows['client'] = client_flow
        
        # === ПОТОК ДЛЯ ИСПОЛНИТЕЛЕЙ ===
        contractor_flow = RequestFlow()
        
        # Шаг 1: Доступная техника
        c_step1 = RequestStep(
            'available_equipment',
            'available_equipment',
            'Шаг 1/6: Доступная техника\n\nУкажите какую строительную технику вы можете предоставить:\n(например: экскаватор JCB, кран 25т, бульдозер CAT)',
            'location_contractor'
        )
        
        # Шаг 2: Локация
        c_step2 = RequestStep(
            'location_contractor',
            'location',
            'Шаг 2/6: Локация\n\nУкажите город или область, где вы работаете:',
            'experience_years'
        )
        
        # Шаг 3: Опыт
        c_step3 = RequestStep(
            'experience_years',
            'experience_years',
            'Шаг 3/6: Опыт работы\n\nСколько лет вы работаете в сфере строительной техники?',
            'price_per_hour',
            'int'
        )
        
        # Шаг 4: Цена
        c_step4 = RequestStep(
            'price_per_hour',
            'price_per_hour',
            'Шаг 4/6: Цена за час\n\nУкажите стоимость аренды за час в гривнах:',
            'phone_contractor',
            'float'
        )
        
        # Шаг 5: Телефон
        c_step5 = RequestStep(
            'phone_contractor',
            'phone',
            'Шаг 5/6: Контактная информация\n\nУкажите ваш номер телефона:',
            'contact_preference_contractor'
        )
        
        # Шаг 6: Способ связи (кнопки)
        c_step6 = RequestStep(
            'contact_preference_contractor',
            'contact_preference',
            'Шаг 6/6: Способ связи\n\nКак с вами лучше связаться?',
            None  # Последний шаг
        )
        
        contractor_flow.add_step(c_step1)
        contractor_flow.add_step(c_step2)
        contractor_flow.add_step(c_step3)
        contractor_flow.add_step(c_step4)
        contractor_flow.add_step(c_step5)
        contractor_flow.add_step(c_step6)
        
        self.flows['contractor'] = contractor_flow
    
    def start_request(self, request_type: str, context: ContextTypes.DEFAULT_TYPE):
        """Начинает создание заявки"""
        # Полностью очищаем контекст
        self.clear_context(context)
        
        flow = self.flows.get(request_type)
        if not flow:
            return "Ошибка: неизвестный тип заявки"
        
        # Устанавливаем новое состояние
        context.user_data['request_active'] = True
        context.user_data['request_type'] = request_type
        context.user_data['current_step_id'] = flow.start_step
        context.user_data['request_data'] = {}
        
        logger.info(f"Начинаем заявку {request_type}, первый шаг: {flow.start_step}")
        
        # Возвращаем первый вопрос
        first_step = flow.get_step(flow.start_step)
        return first_step.question
    
    def process_text_input(self, text: str, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает текстовый ввод"""
        if not context.user_data.get('request_active'):
            return {"error": "Заявка не активна"}
        
        request_type = context.user_data.get('request_type')
        current_step_id = context.user_data.get('current_step_id')
        request_data = context.user_data.get('request_data', {})
        
        flow = self.flows.get(request_type)
        if not flow:
            return {"error": "Неизвестный тип заявки"}
        
        current_step = flow.get_step(current_step_id)
        if not current_step:
            return {"error": "Неизвестный шаг"}
        
        logger.info(f"Обрабатываем шаг {current_step_id}, поле {current_step.field_name}")
        
        # Если это шаг с кнопками - ошибка
        if current_step_id in ['contact_preference', 'contact_preference_contractor']:
            return {"error": "Этот шаг требует нажатия кнопки"}
        
        # Валидация
        value, error = current_step.validate_input(text)
        if error:
            return {"error": error}
        
        # Сохраняем значение
        request_data[current_step.field_name] = value
        context.user_data['request_data'] = request_data
        
        # Переходим к следующему шагу
        next_step_id = current_step.next_step
        if not next_step_id:
            # Это был последний шаг
            return {"completed": True}
        
        context.user_data['current_step_id'] = next_step_id
        next_step = flow.get_step(next_step_id)
        
        # Если следующий шаг - кнопки
        if next_step_id in ['contact_preference', 'contact_preference_contractor']:
            return {"buttons": True, "question": next_step.question}
        
        return {"question": next_step.question}
    
    def process_button_input(self, button_data: str, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает нажатие кнопки"""
        if not context.user_data.get('request_active'):
            return {"error": "Заявка не активна"}
        
        current_step_id = context.user_data.get('current_step_id')
        request_data = context.user_data.get('request_data', {})
        
        # Проверяем, что мы на шаге выбора связи
        if current_step_id not in ['contact_preference', 'contact_preference_contractor']:
            return {"error": "Неверный шаг для кнопки"}
        
        # Обрабатываем выбор
        if button_data == 'contact_message':
            preference = 'message'
        elif button_data == 'contact_call':
            preference = 'call'
        else:
            return {"error": "Неверный выбор"}
        
        request_data['contact_preference'] = preference
        context.user_data['request_data'] = request_data
        
        return {"completed": True}
    
    def create_contact_buttons(self):
        """Создает кнопки для выбора способа связи"""
        keyboard = [
            [InlineKeyboardButton("💬 Написать в Telegram", callback_data="contact_message")],
            [InlineKeyboardButton("📞 Позвонить по телефону", callback_data="contact_call")],
            [InlineKeyboardButton("❌ Отмена", callback_data="start_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def clear_context(self, context: ContextTypes.DEFAULT_TYPE):
        """Полностью очищает контекст заявки"""
        keys_to_remove = [
            'request_active', 'request_type', 'current_step_id', 'request_data',
            'creating_request', 'request_step', 'waiting_for_contact_preference',
            'current_step'
        ]
        for key in keys_to_remove:
            context.user_data.pop(key, None)
        
        logger.info("Контекст заявки очищен")
    
    def is_request_active(self, context: ContextTypes.DEFAULT_TYPE):
        """Проверяет, активна ли заявка"""
        return context.user_data.get('request_active', False)

# Глобальный экземпляр
request_system = RequestSystem()
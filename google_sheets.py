import gspread
from google.oauth2.service_account import Credentials
from config import Config
from datetime import datetime
import logging
import json
import os

logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    def __init__(self):
        self.sheet = None
        self._connect()
    
    def _connect(self):
        """Подключается к Google Sheets"""
        try:
            # Настройка области видимости
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Загрузка учетных данных
            # Сначала пробуем из переменной окружения
            credentials_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
            if credentials_json:
                # Парсим JSON из переменной окружения
                credentials_dict = json.loads(credentials_json)
                creds = Credentials.from_service_account_info(
                    credentials_dict, 
                    scopes=scope
                )
                logger.info("Используем credentials из переменной окружения")
            else:
                # Fallback на файл
                creds = Credentials.from_service_account_file(
                    Config.GOOGLE_SHEETS_CREDENTIALS_FILE, 
                    scopes=scope
                )
                logger.info("Используем credentials из файла")
            
            # Подключение к Google Sheets
            gc = gspread.authorize(creds)
            self.sheet = gc.open_by_key(Config.GOOGLE_SHEET_ID).sheet1
            
            # Создаем заголовки если лист пустой
            try:
                # Проверяем, есть ли данные в таблице
                all_values = self.sheet.get_all_values()
                if not all_values or len(all_values) == 0:
                    logger.info("Таблица пустая, создаем заголовки")
                    self._create_headers()
                else:
                    logger.info(f"Таблица содержит {len(all_values)} строк")
            except Exception as e:
                logger.error(f"Ошибка при проверке таблицы: {e}")
                # Если не можем проверить, создаем заголовки
                self._create_headers()
                
        except Exception as e:
            logger.error(f"Ошибка подключения к Google Sheets: {e}")
            self.sheet = None
    
    def _create_headers(self):
        """Создает заголовки в таблице"""
        headers = [
            'ID', 'Дата создания', 'Тип заявки', 'Пользователь', 'Телефон',
            'Заголовок', 'Описание', 'Локация', 'Тип техники', 'Длительность работ',
            'Бюджет', 'Доступная техника', 'Опыт (лет)', 'Цена за час', 'Статус'
        ]
        self.sheet.append_row(headers)
    
    def add_request(self, request, user):
        """Добавляет заявку в Google Sheets"""
        if not self.sheet:
            logger.error("Google Sheets не подключен")
            return False
        
        try:
            row_data = [
                request.id,                                                    # A: ID
                request.created_at.strftime('%d.%m.%Y %H:%M'),                # B: Дата создания
                'Клиент' if request.request_type == 'client' else 'Исполнитель', # C: Тип заявки
                f"{user.first_name} {user.last_name or ''}".strip(),          # D: Пользователь
                user.phone or 'Не указан',                                     # E: Телефон
                request.title,                                                 # F: Заголовок
                request.description or '',                                     # G: Описание
                request.location,                                              # H: Локация
                request.equipment_type or '',                                  # I: Тип техники
                request.work_duration or '',                                   # J: Длительность работ
                request.budget or '',                                          # K: Бюджет
                request.available_equipment or '',                             # L: Доступная техника
                request.experience_years or '',                                # M: Опыт (лет)
                request.price_per_hour or '',                                  # N: Цена за час
                request.status                                                 # O: Статус
            ]
            
            logger.info(f"Добавляем заявку {request.id} в Google Sheets: {row_data}")
            self.sheet.append_row(row_data)
            logger.info(f"✅ Заявка {request.id} успешно добавлена в Google Sheets")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления заявки в Google Sheets: {e}")
            return False
    
    def update_request_status(self, request_id, new_status):
        """Обновляет статус заявки в Google Sheets"""
        if not self.sheet:
            return False
        
        try:
            # Находим строку с нужным ID
            cell = self.sheet.find(str(request_id))
            if cell:
                # Обновляем статус (последний столбец)
                self.sheet.update_cell(cell.row, 15, new_status)
                return True
        except Exception as e:
            logger.error(f"Ошибка обновления статуса в Google Sheets: {e}")
        
        return False
    
    def get_all_requests(self):
        """Получает все заявки из Google Sheets"""
        if not self.sheet:
            return []
        
        try:
            return self.sheet.get_all_records()
        except Exception as e:
            logger.error(f"Ошибка получения данных из Google Sheets: {e}")
            return []

# Глобальный экземпляр менеджера
sheets_manager = GoogleSheetsManager()

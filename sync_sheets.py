#!/usr/bin/env python3
"""
Скрипт для синхронизации Google Sheets с базой данных
"""

import logging
from database import SessionLocal, Request, User
from google_sheets import sheets_manager
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SheetsSync:
    def __init__(self):
        self.sheets_manager = sheets_manager
    
    def sync_all_requests(self):
        """Синхронизирует все заявки из БД в Google Sheets"""
        try:
            db = SessionLocal()
            try:
                # Получаем все заявки из БД
                requests = db.query(Request).order_by(Request.created_at.desc()).all()
                logger.info(f"📋 Найдено {len(requests)} заявок в БД")
                
                # Очищаем Google Sheets (кроме заголовков)
                self._clear_sheets_data()
                
                # Добавляем все заявки в Google Sheets
                for request in requests:
                    user = db.query(User).filter(User.id == request.user_id).first()
                    if user:
                        success = self.sheets_manager.add_request(request, user)
                        if success:
                            logger.info(f"✅ Заявка {request.id} синхронизирована")
                        else:
                            logger.error(f"❌ Ошибка синхронизации заявки {request.id}")
                    else:
                        logger.warning(f"⚠️ Пользователь не найден для заявки {request.id}")
                
                logger.info("✅ Синхронизация завершена")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Ошибка синхронизации: {e}")
    
    def _clear_sheets_data(self):
        """Очищает данные в Google Sheets (кроме заголовков)"""
        try:
            if not self.sheets_manager.sheet:
                logger.error("Google Sheets не подключен")
                return False
            
            # Получаем все данные
            all_values = self.sheets_manager.sheet.get_all_values()
            
            if len(all_values) > 1:  # Если есть данные кроме заголовков
                # Удаляем все строки кроме первой (заголовки)
                self.sheets_manager.sheet.delete_rows(2, len(all_values))
                logger.info("🗑️ Данные в Google Sheets очищены")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки Google Sheets: {e}")
            return False
    
    def add_request_to_sheets(self, request, user):
        """Добавляет одну заявку в Google Sheets"""
        try:
            return self.sheets_manager.add_request(request, user)
        except Exception as e:
            logger.error(f"❌ Ошибка добавления заявки в Google Sheets: {e}")
            return False
    
    def update_request_in_sheets(self, request_id, new_status):
        """Обновляет статус заявки в Google Sheets"""
        try:
            return self.sheets_manager.update_request_status(request_id, new_status)
        except Exception as e:
            logger.error(f"❌ Ошибка обновления заявки в Google Sheets: {e}")
            return False

# Глобальный экземпляр для использования в боте
sheets_sync = SheetsSync()

if __name__ == "__main__":
    # Запускаем полную синхронизацию
    sheets_sync.sync_all_requests()

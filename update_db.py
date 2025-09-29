#!/usr/bin/env python3
"""
Скрипт для обновления базы данных
"""

import logging
from database import SessionLocal, Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_contact_preferences():
    """Обновляет contact_preference для существующих записей"""
    db = SessionLocal()
    try:
        # Находим все записи где contact_preference = None
        requests = db.query(Request).filter(Request.contact_preference.is_(None)).all()
        
        logger.info(f"Найдено {len(requests)} записей для обновления")
        
        for req in requests:
            req.contact_preference = 'message'  # Устанавливаем значение по умолчанию
            logger.info(f"Обновлена заявка ID: {req.id}")
        
        db.commit()
        logger.info("✅ Все записи обновлены успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка обновления: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_contact_preferences()

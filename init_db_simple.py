#!/usr/bin/env python3
"""
Простой скрипт для инициализации базы данных
"""
import os
import sys
from database import engine, Base
from models import User, Request

def init_db():
    """Инициализирует базу данных"""
    try:
        print("🏗️ Инициализация базы данных...")
        
        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)
        print("✅ Таблицы базы данных созданы")
        
        # Проверяем подключение
        from database import SessionLocal
        db = SessionLocal()
        try:
            # Пробуем выполнить простой запрос
            result = db.execute("SELECT 1").fetchone()
            print("✅ Подключение к базе данных работает")
        finally:
            db.close()
        
        print("🚀 Инициализация завершена!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1)


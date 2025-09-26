#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных в Railway
"""
import os
import sys
from database import engine, Base
from models import User, Request

def init_railway_db():
    """Инициализирует базу данных в Railway"""
    try:
        print("🏗️ Инициализация базы данных в Railway...")
        
        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)
        print("✅ Таблицы базы данных созданы")
        
        print("🚀 Инициализация завершена!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return False

if __name__ == "__main__":
    success = init_railway_db()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных
"""

from database import create_tables
from google_sheets import sheets_manager

def main():
    print("🏗️ Инициализация базы данных...")
    
    # Создаем таблицы
    create_tables()
    print("✅ Таблицы базы данных созданы")
    
    # Проверяем подключение к Google Sheets
    if sheets_manager.sheet:
        print("✅ Подключение к Google Sheets успешно")
    else:
        print("⚠️ Не удалось подключиться к Google Sheets")
        print("Убедитесь, что:")
        print("1. Файл credentials.json существует")
        print("2. GOOGLE_SHEET_ID указан в .env")
        print("3. Таблица доступна для сервисного аккаунта")
    
    print("\n🚀 Инициализация завершена!")
    print("Теперь можно запускать бота: python bot.py")

if __name__ == "__main__":
    main()

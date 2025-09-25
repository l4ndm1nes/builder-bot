#!/usr/bin/env python3
"""
Скрипт для тестирования основных функций бота
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_config():
    """Тестирует конфигурацию"""
    print("🔧 Проверка конфигурации...")
    
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'GOOGLE_SHEET_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        return False
    
    print("✅ Все необходимые переменные окружения настроены")
    return True

def test_database():
    """Тестирует подключение к базе данных"""
    print("🗄️ Проверка базы данных...")
    
    try:
        from database import create_tables, SessionLocal
        create_tables()
        
        # Пробуем создать сессию
        db = SessionLocal()
        db.close()
        
        print("✅ База данных работает корректно")
        return True
    except Exception as e:
        print(f"❌ Ошибка базы данных: {e}")
        return False

def test_google_sheets():
    """Тестирует подключение к Google Sheets"""
    print("📊 Проверка Google Sheets...")
    
    try:
        from google_sheets import sheets_manager
        
        if sheets_manager.sheet:
            # Пробуем получить данные
            data = sheets_manager.get_all_requests()
            print("✅ Google Sheets подключен и работает")
            return True
        else:
            print("❌ Не удалось подключиться к Google Sheets")
            return False
    except Exception as e:
        print(f"❌ Ошибка Google Sheets: {e}")
        return False

def test_telegram_bot():
    """Тестирует создание экземпляра бота"""
    print("🤖 Проверка Telegram бота...")
    
    try:
        from bot import ConstructionBot
        
        # Создаем экземпляр бота (не запускаем)
        bot = ConstructionBot()
        print("✅ Telegram бот создан успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания бота: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование системы диспетчеризации строительной техники\n")
    
    tests = [
        ("Конфигурация", test_config),
        ("База данных", test_database),
        ("Google Sheets", test_google_sheets),
        ("Telegram бот", test_telegram_bot)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        result = test_func()
        results.append((test_name, result))
    
    print(f"\n{'='*50}")
    print("📋 Результаты тестирования:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print(f"\n{'='*50}")
    if all_passed:
        print("🎉 Все тесты пройдены! Система готова к работе.")
        print("Запустите бота командой: python bot.py")
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте настройки.")
        print("Убедитесь, что:")
        print("1. Файл .env создан и заполнен")
        print("2. Файл credentials.json существует")
        print("3. Google таблица доступна")
        print("4. Все зависимости установлены")

if __name__ == "__main__":
    main()

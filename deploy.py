#!/usr/bin/env python3
"""
Скрипт для автоматического деплоя бота
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Выполняет команду и выводит результат"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - успешно")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ошибка")
        print(f"Код ошибки: {e.returncode}")
        if e.stdout:
            print(f"Вывод: {e.stdout}")
        if e.stderr:
            print(f"Ошибка: {e.stderr}")
        return False

def check_requirements():
    """Проверяет наличие необходимых инструментов"""
    print("🔍 Проверка требований...")
    
    requirements = {
        "git": "git --version",
        "python": "python --version",
        "pip": "pip --version"
    }
    
    missing = []
    for tool, command in requirements.items():
        if not run_command(command, f"Проверка {tool}"):
            missing.append(tool)
    
    if missing:
        print(f"❌ Отсутствуют необходимые инструменты: {', '.join(missing)}")
        return False
    
    print("✅ Все требования выполнены")
    return True

def setup_environment():
    """Настраивает окружение"""
    print("🔧 Настройка окружения...")
    
    # Проверяем наличие .env файла
    if not Path(".env").exists():
        print("⚠️ Файл .env не найден")
        print("Скопируйте env_example.txt в .env и заполните переменные")
        return False
    
    # Проверяем наличие credentials.json
    if not Path("credentials.json").exists():
        print("⚠️ Файл credentials.json не найден")
        print("Скачайте файл с ключами Google API и переименуйте в credentials.json")
        return False
    
    print("✅ Окружение настроено")
    return True

def test_locally():
    """Тестирует бота локально"""
    print("🧪 Тестирование...")
    
    if not run_command("python test_bot.py", "Тестирование системы"):
        print("❌ Тесты провалены. Исправьте ошибки перед деплоем.")
        return False
    
    return True

def deploy_to_railway():
    """Деплоит на Railway"""
    print("🚀 Деплой на Railway...")
    
    # Проверяем, инициализирован ли Railway
    if not Path("railway.json").exists():
        print("❌ Railway не настроен")
        return False
    
    # Коммитим изменения
    if not run_command("git add .", "Добавление файлов в git"):
        return False
    
    if not run_command('git commit -m "Deploy construction bot"', "Коммит изменений"):
        return False
    
    # Деплоим
    if not run_command("railway up", "Деплой на Railway"):
        return False
    
    print("✅ Деплой на Railway завершен")
    return True

def deploy_to_heroku():
    """Деплоит на Heroku"""
    print("🚀 Деплой на Heroku...")
    
    # Проверяем, настроен ли Heroku
    try:
        subprocess.run("heroku --version", shell=True, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ Heroku CLI не установлен")
        return False
    
    # Коммитим изменения
    if not run_command("git add .", "Добавление файлов в git"):
        return False
    
    if not run_command('git commit -m "Deploy construction bot"', "Коммит изменений"):
        return False
    
    # Деплоим
    if not run_command("git push heroku main", "Деплой на Heroku"):
        return False
    
    print("✅ Деплой на Heroku завершен")
    return True

def main():
    """Основная функция деплоя"""
    print("🚀 Автоматический деплой бота диспетчеризации строительной техники\n")
    
    # Выбираем платформу
    if len(sys.argv) > 1:
        platform = sys.argv[1].lower()
    else:
        platform = input("Выберите платформу (railway/heroku): ").lower()
    
    if platform not in ["railway", "heroku"]:
        print("❌ Неподдерживаемая платформа. Используйте 'railway' или 'heroku'")
        return
    
    # Проверяем требования
    if not check_requirements():
        return
    
    # Настраиваем окружение
    if not setup_environment():
        return
    
    # Тестируем локально
    if not test_locally():
        return
    
    # Деплоим
    if platform == "railway":
        success = deploy_to_railway()
    else:
        success = deploy_to_heroku()
    
    if success:
        print("\n🎉 Деплой завершен успешно!")
        print("Ваш бот теперь работает в продакшне!")
        print("\nСледующие шаги:")
        print("1. Проверьте работу бота в Telegram")
        print("2. Настройте мониторинг")
        print("3. Добавьте дополнительные функции при необходимости")
    else:
        print("\n❌ Деплой не удался. Проверьте ошибки выше.")

if __name__ == "__main__":
    main()

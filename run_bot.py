#!/usr/bin/env python3
"""
Скрипт для запуска бота с обработкой ошибок
"""

import logging
import sys
import os
import threading
from bot import ConstructionBot
from web_server import app
import uvicorn

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def run_web_server():
    """Запускает веб-сервер для healthcheck"""
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")

def main():
    """Запускает бота"""
    try:
        logger.info("🚀 Запуск бота диспетчеризации строительной техники...")
        
        # Запускаем веб-сервер в отдельном потоке
        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()
        logger.info("🌐 Веб-сервер запущен для healthcheck")
        
        # Создаем экземпляр бота
        bot = ConstructionBot()
        logger.info("✅ Бот создан успешно")
        
        # Запускаем бота
        logger.info("🔄 Запуск polling...")
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("⏹️ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

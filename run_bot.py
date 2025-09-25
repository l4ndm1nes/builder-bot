#!/usr/bin/env python3
"""
Скрипт для запуска бота с обработкой ошибок
"""

import logging
import sys
from bot import ConstructionBot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Запускает бота"""
    try:
        logger.info("🚀 Запуск бота диспетчеризации строительной техники...")
        
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

from loguru import logger

logger.add("logs/features-message.log", format="{time} {level} {message}", level="INFO", rotation="100 MB")
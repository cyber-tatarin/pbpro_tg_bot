import os

from loguru import logger
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())


def get_logger():
    logger.add("bot.log", format="{time} {level} {message}", level=os.getenv('LOG_LEVEL'),
               rotation="1 MB", compression="zip")
    return logger

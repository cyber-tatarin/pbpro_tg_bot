import os

import loguru
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

logger = loguru.logger
logger.add("bot.log", format="{time} {level} {message}", level=os.getenv('LOG_LEVEL'),
           rotation="1 MB", compression="zip")


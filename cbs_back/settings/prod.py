
import os
from .base import *
from dotenv import load_dotenv
import logging
from icecream import ic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

if os.name == 'linux':
    ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS')
elif os.name == 'nt':
    ALLOWED_HOSTS = ['127.0.0.1']


DJANGO_ENV_PROD = [os.getenv('DJANGO_ENV_PROD')]

if 'production' in DJANGO_ENV_PROD:
    logger.info("Running in production mode")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": f"{os.getenv('DB_NAME')}",
        "USER": f"{os.getenv('DB_USERNAME')}",
        "PASSWORD": f"{os.getenv('DB_PASSWORD')}",
        "HOST": f"{os.getenv('DB_HOST')}",
        "PORT": int(f"{os.getenv('DB_PORT')}"),
    },
    "OPTIONS": {
            "pool": True,
        },
}

ic(DATABASES)
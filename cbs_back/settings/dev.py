
from .base import *
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

from cbs_back.settings.base import BASE_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
DEBUG = True

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
ALLOWED_HOSTS = ['*']


if os.getenv('DJANGO_ENV') == 'test':
   logger.info("Running in test mode")
   

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}



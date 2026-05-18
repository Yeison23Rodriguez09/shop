#  beauty_shop/config/logging.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

LOG_LEVEL = os.getenv('DJANGO_LOG_LEVEL', 'INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    # ========================
    # 📍 Formatters
    # ========================
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} | {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },

    # ========================
    # 🛎 Handlers
    # ========================
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/django.log',
            'formatter': 'verbose',
        },
    },

    # ========================
    # 📦 Loggers
    # ========================
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

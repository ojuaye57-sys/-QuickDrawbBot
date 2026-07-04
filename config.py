"""
Configuration settings for QuickDraw Bot
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Bot configuration"""
    
    # Telegram Bot Token
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    
    # Hugging Face API
    HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY')
    HUGGINGFACE_MODEL = os.environ.get(
        'HUGGINGFACE_MODEL',
        'stabilityai/stable-diffusion-2-1'
    )
    
    # Railway Settings
    PORT = int(os.environ.get('PORT', 8080))
    WEBHOOK_URL = os.environ.get('RAILWAY_STATIC_URL', os.environ.get('WEBHOOK_URL'))
    USE_WEBHOOK = bool(os.environ.get('USE_WEBHOOK', 'true').lower() == 'true')
    
    # Image Settings
    DEFAULT_SIZE = os.environ.get('DEFAULT_IMAGE_SIZE', '512x512')
    MAX_PROMPT_LENGTH = 1000
    
    # Rate Limiting
    RATE_LIMIT = int(os.environ.get('RATE_LIMIT', 10))  # requests per minute
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

class DevelopmentConfig(Config):
    """Development configuration"""
    USE_WEBHOOK = False
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    USE_WEBHOOK = True
    LOG_LEVEL = 'INFO'

# Select config based on environment
ENV = os.environ.get('ENV', 'development')
if ENV == 'production':
    config = ProductionConfig
else:
    config = DevelopmentConfig

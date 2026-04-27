import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key')
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///danjuma.db')
    VIRUSTOTAL_API_KEY = os.environ.get('VIRUSTOTAL_API_KEY')

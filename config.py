import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'medadvisor-secret-key-2024')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///medadvisor.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_EXPIRATION_HOURS = 24

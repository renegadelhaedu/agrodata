from werkzeug.security import generate_password_hash
import os

class Config:
    SECRET_KEY = "agrodata2025"
    SQLALCHEMY_DATABASE_URI = "sqlite:///iot_data.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADMIN_USER_HASH = generate_password_hash("admin")
    ADMIN_PASSWORD_HASH = generate_password_hash("1234")

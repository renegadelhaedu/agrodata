import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///iot_data.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get("SECRET_KEY", "Sh24G4lKJ4@")

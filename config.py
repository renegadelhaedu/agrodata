import os

from flask_login import LoginManager
from werkzeug.security import generate_password_hash

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

login_manager = LoginManager()


def obter_hash_admin(nome_variavel, valor_padrao):
    return os.getenv(nome_variavel) or generate_password_hash(valor_padrao)

@login_manager.user_loader
def load_user(user_id):
    from modelo.admin import Admin
    from modelo.usuario import Usuario
    try:
        tipo_usuario, id_numerico = user_id.split('_')
        id_numerico = int(id_numerico)

        if tipo_usuario == 'admin':
            return Admin()
        elif tipo_usuario == 'user':
            return Usuario.query.get(id_numerico)

    except ValueError:
        return None
    return None


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "agrodata2025")
    SQLALCHEMY_DATABASE_URI = "sqlite:///iot_data.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADMIN_USER_HASH = obter_hash_admin("ADMIN_USER_HASH", "admin")
    ADMIN_PASSWORD_HASH = obter_hash_admin("ADMIN_PASSWORD_HASH", "1234")

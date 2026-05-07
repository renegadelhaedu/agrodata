from werkzeug.security import generate_password_hash
from flask_login import LoginManager
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    from modelo.modelsDB import Admin, Usuario
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
    SECRET_KEY = "agrodata2025"
    SQLALCHEMY_DATABASE_URI = "sqlite:///iot_data.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADMIN_USER_HASH = generate_password_hash("admin")
    ADMIN_PASSWORD_HASH = generate_password_hash("1234")

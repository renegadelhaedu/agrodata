from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Admin(UserMixin):
    def __init__(self):
        self.id = 1
        self.login = "admin"

        # Gere o hash uma vez e cole aqui
        self.password_hash = (
            "scrypt:32768:8:1$mUmose2a4dY0WZv3$ecd673fe91f5b8d914d0fd39869cf34b8a5c62ef4049b8349a6aa02415f7e221c6bf74a33cb2c346c1c48d18de59869a0a4667a90d689e390d372cb37d1de663"
        )

    @property
    def is_admin(self):
        return True

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"admin_{self.id}"
from flask_login import UserMixin

class Admin(UserMixin):
    def __init__(self):
        self.id = 1
        self.login = 'admin'
        self.senha = '1234'

    @property
    def is_admin(self):
        return True

    def get_id(self):
        return f"admin_{self.id}"


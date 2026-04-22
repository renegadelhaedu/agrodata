from functools import wraps
from flask import  redirect, url_for
from flask_login import current_user, logout_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('home'))

        if not current_user.is_professor:
            logout_user()
            return redirect(url_for('home'))

        return f(*args, **kwargs)

    return decorated_function
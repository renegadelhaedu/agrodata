import app
from banco import db

app = app.app

def init_db():
    with app.app_context():
        db.create_all()
        print("Banco inicializado!")

if __name__ == "__main__":
    init_db()


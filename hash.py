from werkzeug.security import generate_password_hash

hash_senha = generate_password_hash("1234")

print(hash_senha)
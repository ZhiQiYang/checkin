# encrypt_env.py
from cryptography.fernet import Fernet

def load_key():
    return open("secret.key", "rb").read()

def encrypt_file(file_name):
    key = load_key()
    f = Fernet(key)
    with open(file_name, "rb") as file:
        file_data = file.read()
    encrypted_data = f.encrypt(file_data)
    with open(file_name + ".enc", "wb") as file:
        file.write(encrypted_data)

encrypt_file(".env")

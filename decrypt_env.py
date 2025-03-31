# decrypt_env.py
from cryptography.fernet import Fernet

def load_key():
    return open("secret.key", "rb").read()

def decrypt_file(file_name):
    key = load_key()
    f = Fernet(key)
    with open(file_name, "rb") as file:
        encrypted_data = file.read()
    decrypted_data = f.decrypt(encrypted_data)
    with open(file_name.replace(".enc", ""), "wb") as file:
        file.write(decrypted_data)

decrypt_file(".env.enc")

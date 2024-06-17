import base64 

from cryptography.fernet import Fernet 


def generate_key() -> bytes:
    return Fernet.generate_key()

def encrypt_payload(payload: bytes, key: bytes, valid_base64: bool = True) -> bytes:
    func = Fernet(key)
    data = func.encrypt(payload)

    if valid_base64:
        data = base64.b64encode(data, b"-_").decode().replace("=", "").encode() 

    return data


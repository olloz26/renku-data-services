"""Encryption and decryption functions."""

import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def get_encryption_key(password: bytes, salt: bytes) -> bytes:
    """Create an encryption key with the password and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password))


def generate_random_encryption_key() -> bytes:
    """Generate a random key to be used with Fernet encryption."""
    return Fernet.generate_key()


def encrypt_string(password: bytes, salt: str, data: str) -> bytes:
    """Encrypt a given string."""
    key = get_encryption_key(password=password, salt=salt.encode())
    return Fernet(key).encrypt(data.encode())


def decrypt_string(password: bytes, salt: str, data: bytes) -> str:
    """Decrypt a given string."""
    key = get_encryption_key(password=password, salt=salt.encode())
    return Fernet(key).decrypt(data).decode()


def encrypt_rsa(public_key: rsa.RSAPublicKey, data: bytes) -> bytes:
    """Encrypt with an RSA public key."""
    encrypted_data = public_key.encrypt(
        data, padding.OAEP(padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    return encrypted_data


def decrypt_rsa(private_key: rsa.RSAPrivateKey, encrypted_data: bytes) -> bytes:
    """Decrypt with an RSA private key."""
    data = private_key.decrypt(
        encrypted_data, padding.OAEP(padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    return data

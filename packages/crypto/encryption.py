"""
AEAD Symmetric Encryption and Key Derivation (HKDF-SHA256)
"""
import os
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305, AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

def derive_shared_key(shared_secret: bytes, salt: bytes = b"ursafe_mesh_salt", info: bytes = b"ursafe_aead_key") -> bytes:
    """Derives a 32-byte symmetric AEAD key from a raw Diffie-Hellman secret using HKDF-SHA256."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=info,
    )
    return hkdf.derive(shared_secret)

def encrypt_aead(plaintext: bytes, key: bytes, associated_data: bytes = b"", cipher_type: str = "ChaCha20-Poly1305") -> Tuple[bytes, bytes]:
    """
    Encrypts plaintext with AEAD cipher and random nonce.
    Returns (nonce, ciphertext_with_tag).
    """
    if cipher_type == "ChaCha20-Poly1305":
        nonce = os.urandom(12)
        cipher = ChaCha20Poly1305(key)
        ciphertext = cipher.encrypt(nonce, plaintext, associated_data)
        return nonce, ciphertext
    elif cipher_type == "AES-256-GCM":
        nonce = os.urandom(12)
        cipher = AESGCM(key)
        ciphertext = cipher.encrypt(nonce, plaintext, associated_data)
        return nonce, ciphertext
    else:
        raise ValueError(f"Unsupported cipher type: {cipher_type}")

def decrypt_aead(ciphertext: bytes, key: bytes, nonce: bytes, associated_data: bytes = b"", cipher_type: str = "ChaCha20-Poly1305") -> bytes:
    """Decrypts and authenticates ciphertext. Raises exception if tag or ciphertext has been tampered with."""
    if cipher_type == "ChaCha20-Poly1305":
        cipher = ChaCha20Poly1305(key)
        return cipher.decrypt(nonce, ciphertext, associated_data)
    elif cipher_type == "AES-256-GCM":
        cipher = AESGCM(key)
        return cipher.decrypt(nonce, ciphertext, associated_data)
    else:
        raise ValueError(f"Unsupported cipher type: {cipher_type}")

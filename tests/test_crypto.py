"""
Unit Tests for UrSafe Cryptography Subsystem
"""
import pytest
from packages.crypto.keys import KeyPair, Ed25519KeyPair, X25519KeyPair
from packages.crypto.encryption import encrypt_aead, decrypt_aead, derive_shared_key
from packages.crypto.replay import ReplayFilter
from packages.crypto.keystore import CryptoKeystore
from packages.crypto.identity import DeviceIdentity, UserIdentity, ResponderIdentity
from packages.protocol.envelope import MessageEnvelope, Location

def test_ed25519_sign_and_verify():
    kp = Ed25519KeyPair.generate()
    message = b"CRITICAL_SOS_DISPATCH_TOKEN"
    signature = kp.sign(message)

    assert len(signature) == 64
    assert kp.verify(signature, message) is True
    assert kp.verify(signature, b"TAMPERED_MESSAGE") is False

def test_x25519_diffie_hellman_and_hkdf():
    alice = X25519KeyPair.generate()
    bob = X25519KeyPair.generate()

    alice_shared = alice.exchange(bob.public_bytes)
    bob_shared = bob.exchange(alice.public_bytes)

    assert alice_shared == bob_shared

    alice_key = derive_shared_key(alice_shared)
    bob_key = derive_shared_key(bob_shared)
    assert alice_key == bob_key
    assert len(alice_key) == 32

def test_chacha20_poly1305_encryption_and_tampering():
    key = b"01234567890123456789012345678901"
    plaintext = b"Victim trapped in sector 4B with 3 family members"
    aad = b"incident_meta_v1"

    nonce, ciphertext = encrypt_aead(plaintext, key, associated_data=aad, cipher_type="ChaCha20-Poly1305")
    decrypted = decrypt_aead(ciphertext, key, nonce, associated_data=aad, cipher_type="ChaCha20-Poly1305")
    assert decrypted == plaintext

    # Tampering test: alter one bit in ciphertext
    tampered = bytearray(ciphertext)
    tampered[5] ^= 0xFF
    with pytest.raises(Exception):
        decrypt_aead(bytes(tampered), key, nonce, associated_data=aad, cipher_type="ChaCha20-Poly1305")

def test_replay_filter_sliding_window():
    rf = ReplayFilter(window_size=16)
    sender = "node_victim_01"

    # In-order packets
    assert rf.is_valid_and_update(sender, 1) is True
    assert rf.is_valid_and_update(sender, 2) is True
    assert rf.is_valid_and_update(sender, 3) is True

    # Replay of packet 2
    assert rf.is_valid_and_update(sender, 2) is False

    # Out-of-order jump
    assert rf.is_valid_and_update(sender, 10) is True

    # Valid out-of-order packet within window (window is 10 - 16, so >= 1)
    assert rf.is_valid_and_update(sender, 5) is True

    # Replay of packet 5
    assert rf.is_valid_and_update(sender, 5) is False

    # Big jump beyond window
    assert rf.is_valid_and_update(sender, 100) is True

    # Now packet 10 is outside the window (100 - 16 = 84 cutoff)
    assert rf.is_valid_and_update(sender, 10) is False

def test_keystore_envelope_signing_and_verification():
    keystore = CryptoKeystore()
    loc = Location(latitude=12.9716, longitude=77.5946)
    env = MessageEnvelope.create_sos(keystore.node_id, "FLOOD", "CRITICAL", 2, loc)

    signed_env = keystore.sign_envelope(env)
    assert signed_env.signature != ""

    # Verify with valid public key
    assert keystore.verify_envelope(signed_env, keystore.public_signing_bytes) is True

    # Tamper payload
    signed_env.payload["people_affected"] = 99
    # Payload hash changed, signing bytes will differ
    assert keystore.verify_envelope(signed_env, keystore.public_signing_bytes) is False

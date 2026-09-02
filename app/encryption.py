import os
from cryptography.fernet import Fernet
from sqlalchemy.types import TypeDecorator, Text


# For an MVP, we check the environment variable first.
# If not found, we fallback to a local file, or generate a new one.
_FERNET_KEY_FILE = ".fernet_key"

def _get_fernet_key():
    env_key = os.getenv("FERNET_KEY")
    if env_key:
        return env_key.encode('utf-8')
    if os.path.exists(_FERNET_KEY_FILE):
        with open(_FERNET_KEY_FILE, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(_FERNET_KEY_FILE, "wb") as f:
        f.write(key)
    return key

try:
    _fernet = Fernet(_get_fernet_key())
except Exception as e:
    # Safe fallback if key is completely invalid (prevents app crash, but breaks crypto)
    print(f"WARNING: Invalid Fernet key provided. Encryption will fail. Error: {e}")
    _fernet = Fernet(Fernet.generate_key())


class EncryptedString(TypeDecorator):
    """
    A custom SQLAlchemy TypeDecorator that encrypts a string on the way in
    and decrypts it on the way out using Fernet (symmetric encryption).
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        # Encrypt the string and store it as bytes/text
        if isinstance(value, str):
            value = value.encode('utf-8')
        return _fernet.encrypt(value).decode('utf-8')

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # Decrypt the text back to a string
        if isinstance(value, str):
            value_bytes = value.encode('utf-8')
        else:
            value_bytes = value
            
        from cryptography.fernet import InvalidToken
        try:
            return _fernet.decrypt(value_bytes).decode('utf-8')
        except InvalidToken:
            # Fallback for unencrypted data existing in the database before encryption was added
            return value if isinstance(value, str) else value.decode('utf-8')

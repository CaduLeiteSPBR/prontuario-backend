from src.models.user import db
from cryptography.fernet import Fernet
import os
import base64

class Config(db.Model):
    __tablename__ = 'configs'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    is_encrypted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def __init__(self, key, value, is_encrypted=False):
        self.key = key
        self.is_encrypted = is_encrypted
        if is_encrypted:
            self.value = self._encrypt_value(value)
        else:
            self.value = value
    
    def get_value(self):
        """Retorna o valor descriptografado se necessário"""
        if self.is_encrypted:
            return self._decrypt_value(self.value)
        return self.value
    
    def set_value(self, value):
        """Define o valor, criptografando se necessário"""
        if self.is_encrypted:
            self.value = self._encrypt_value(value)
        else:
            self.value = value
    
    def _get_encryption_key(self):
        """Gera ou recupera a chave de criptografia"""
        key_file = os.path.join(os.path.dirname(__file__), '..', 'database', 'encryption.key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Gera nova chave se não existir
            key = Fernet.generate_key()
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def _encrypt_value(self, value):
        """Criptografa um valor"""
        if not value:
            return value
        
        key = self._get_encryption_key()
        fernet = Fernet(key)
        encrypted_value = fernet.encrypt(value.encode())
        return base64.b64encode(encrypted_value).decode()
    
    def _decrypt_value(self, encrypted_value):
        """Descriptografa um valor"""
        if not encrypted_value:
            return encrypted_value
        
        try:
            key = self._get_encryption_key()
            fernet = Fernet(key)
            decoded_value = base64.b64decode(encrypted_value.encode())
            decrypted_value = fernet.decrypt(decoded_value)
            return decrypted_value.decode()
        except Exception as e:
            print(f"Erro ao descriptografar valor: {e}")
            return None
    
    @staticmethod
    def get_config(key, default=None):
        """Método estático para recuperar uma configuração"""
        config = Config.query.filter_by(key=key).first()
        if config:
            return config.get_value()
        return default
    
    @staticmethod
    def set_config(key, value, is_encrypted=False):
        """Método estático para definir uma configuração"""
        config = Config.query.filter_by(key=key).first()
        if config:
            config.set_value(value)
            config.is_encrypted = is_encrypted
        else:
            config = Config(key=key, value=value, is_encrypted=is_encrypted)
            db.session.add(config)
        
        db.session.commit()
        return config
    
    def to_dict(self):
        """Converte o objeto para dicionário (sem expor valores criptografados)"""
        return {
            'id': self.id,
            'key': self.key,
            'is_encrypted': self.is_encrypted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


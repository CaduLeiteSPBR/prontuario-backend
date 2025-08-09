from src.models.user import db
import base64
import os

class Config(db.Model):
    __tablename__ = 'configs'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def __init__(self, key, value=None):
        self.key = key
        if value:
            self.set_value(value)
    
    def set_value(self, value):
        """Armazena valor com codificação base64 simples"""
        if value:
            encoded_value = base64.b64encode(value.encode()).decode()
            self.value = encoded_value
        else:
            self.value = None
    
    def get_value(self):
        """Recupera valor decodificado"""
        if self.value:
            try:
                return base64.b64decode(self.value.encode()).decode()
            except:
                return self.value
        return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'configured': self.value is not None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_config(key):
        return Config.query.filter_by(key=key).first()
    
    @staticmethod
    def set_config(key, value):
        config = Config.get_config(key)
        if config:
            config.set_value(value)
        else:
            config = Config(key, value)
            db.session.add(config)
        
        db.session.commit()
        return config
    
    @staticmethod
    def delete_config(key):
        config = Config.get_config(key)
        if config:
            db.session.delete(config)
            db.session.commit()
            return True
        return False


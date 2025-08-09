from src.models.user import db
from datetime import datetime
import json

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informações Pessoais
    full_name = db.Column(db.String(200), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    
    # Endereço
    address_street = db.Column(db.String(200))
    address_number = db.Column(db.String(20))
    address_complement = db.Column(db.String(100))
    address_neighborhood = db.Column(db.String(100))
    address_city = db.Column(db.String(100))
    address_state = db.Column(db.String(2))
    address_zipcode = db.Column(db.String(10))
    
    # Informações Médicas
    allergies = db.Column(db.Text)  # JSON string com lista de alergias
    chronic_diseases = db.Column(db.Text)  # JSON string com lista de doenças crônicas
    previous_surgeries = db.Column(db.Text)  # JSON string com lista de cirurgias
    family_history = db.Column(db.Text)  # JSON string com histórico familiar
    current_medications = db.Column(db.Text)  # JSON string com medicações atuais
    
    # Hábitos de Vida
    smoking = db.Column(db.String(20))  # 'never', 'former', 'current'
    alcohol_consumption = db.Column(db.String(20))  # 'never', 'occasional', 'regular', 'heavy'
    physical_activity = db.Column(db.String(20))  # 'sedentary', 'light', 'moderate', 'intense'
    
    # Informações de Controle
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        # Converte listas para JSON strings
        for field in ['allergies', 'chronic_diseases', 'previous_surgeries', 'family_history', 'current_medications']:
            if field in kwargs and isinstance(kwargs[field], list):
                kwargs[field] = json.dumps(kwargs[field])
        
        super(Patient, self).__init__(**kwargs)
    
    def get_allergies(self):
        """Retorna lista de alergias"""
        if self.allergies:
            try:
                return json.loads(self.allergies)
            except:
                return []
        return []
    
    def set_allergies(self, allergies_list):
        """Define lista de alergias"""
        self.allergies = json.dumps(allergies_list) if allergies_list else None
    
    def get_chronic_diseases(self):
        """Retorna lista de doenças crônicas"""
        if self.chronic_diseases:
            try:
                return json.loads(self.chronic_diseases)
            except:
                return []
        return []
    
    def set_chronic_diseases(self, diseases_list):
        """Define lista de doenças crônicas"""
        self.chronic_diseases = json.dumps(diseases_list) if diseases_list else None
    
    def get_previous_surgeries(self):
        """Retorna lista de cirurgias prévias"""
        if self.previous_surgeries:
            try:
                return json.loads(self.previous_surgeries)
            except:
                return []
        return []
    
    def set_previous_surgeries(self, surgeries_list):
        """Define lista de cirurgias prévias"""
        self.previous_surgeries = json.dumps(surgeries_list) if surgeries_list else None
    
    def get_family_history(self):
        """Retorna histórico familiar"""
        if self.family_history:
            try:
                return json.loads(self.family_history)
            except:
                return []
        return []
    
    def set_family_history(self, history_list):
        """Define histórico familiar"""
        self.family_history = json.dumps(history_list) if history_list else None
    
    def get_current_medications(self):
        """Retorna medicações atuais"""
        if self.current_medications:
            try:
                return json.loads(self.current_medications)
            except:
                return []
        return []
    
    def set_current_medications(self, medications_list):
        """Define medicações atuais"""
        self.current_medications = json.dumps(medications_list) if medications_list else None
    
    def get_age(self):
        """Calcula idade do paciente"""
        if self.birth_date:
            today = datetime.now().date()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None
    
    def get_full_address(self):
        """Retorna endereço completo formatado"""
        address_parts = []
        
        if self.address_street:
            street_part = self.address_street
            if self.address_number:
                street_part += f", {self.address_number}"
            if self.address_complement:
                street_part += f", {self.address_complement}"
            address_parts.append(street_part)
        
        if self.address_neighborhood:
            address_parts.append(self.address_neighborhood)
        
        if self.address_city and self.address_state:
            address_parts.append(f"{self.address_city}/{self.address_state}")
        
        if self.address_zipcode:
            address_parts.append(f"CEP: {self.address_zipcode}")
        
        return " - ".join(address_parts) if address_parts else ""
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'cpf': self.cpf,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'age': self.get_age(),
            'gender': self.gender,
            'phone': self.phone,
            'email': self.email,
            'address': {
                'street': self.address_street,
                'number': self.address_number,
                'complement': self.address_complement,
                'neighborhood': self.address_neighborhood,
                'city': self.address_city,
                'state': self.address_state,
                'zipcode': self.address_zipcode,
                'full_address': self.get_full_address()
            },
            'medical_info': {
                'allergies': self.get_allergies(),
                'chronic_diseases': self.get_chronic_diseases(),
                'previous_surgeries': self.get_previous_surgeries(),
                'family_history': self.get_family_history(),
                'current_medications': self.get_current_medications()
            },
            'lifestyle': {
                'smoking': self.smoking,
                'alcohol_consumption': self.alcohol_consumption,
                'physical_activity': self.physical_activity
            },
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_summary_dict(self):
        """Converte para dicionário resumido (para listas)"""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'cpf': self.cpf,
            'age': self.get_age(),
            'gender': self.gender,
            'phone': self.phone,
            'email': self.email,
            'city': self.address_city,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def search(query, active_only=True):
        """Busca pacientes por nome ou CPF"""
        search_filter = Patient.query
        
        if active_only:
            search_filter = search_filter.filter(Patient.active == True)
        
        if query:
            search_pattern = f"%{query}%"
            search_filter = search_filter.filter(
                db.or_(
                    Patient.full_name.ilike(search_pattern),
                    Patient.cpf.like(search_pattern)
                )
            )
        
        return search_filter.order_by(Patient.full_name).all()


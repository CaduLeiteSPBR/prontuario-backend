from .db import db
from datetime import datetime
import json
import os

class Exam(db.Model):
    __tablename__ = 'exams'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relacionamento com paciente
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    
    # Informações do arquivo
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # em bytes
    file_type = db.Column(db.String(50))  # 'image' ou 'pdf'
    mime_type = db.Column(db.String(100))
    
    # Informações do exame
    exam_type = db.Column(db.String(100))  # Tipo do exame (hemograma, glicemia, etc.)
    exam_date = db.Column(db.Date)  # Data do exame
    lab_name = db.Column(db.String(200))  # Nome do laboratório
    doctor_name = db.Column(db.String(200))  # Médico solicitante
    
    # Dados extraídos pela IA
    extracted_text = db.Column(db.Text)  # Texto extraído do arquivo
    ai_analysis = db.Column(db.Text)  # Análise da IA em JSON
    extracted_values = db.Column(db.Text)  # Valores extraídos em JSON
    ai_summary = db.Column(db.Text)  # Resumo gerado pela IA
    
    # Status do processamento
    processing_status = db.Column(db.String(50), default='pending')  # pending, processing, completed, error
    processing_error = db.Column(db.Text)  # Erro de processamento, se houver
    
    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = db.Column(db.DateTime)  # Quando foi processado
    
    def __init__(self, **kwargs):
        # Converte dicionários para JSON strings
        for field in ['ai_analysis', 'extracted_values']:
            if field in kwargs and isinstance(kwargs[field], (dict, list)):
                kwargs[field] = json.dumps(kwargs[field])
        
        super(Exam, self).__init__(**kwargs)
    
    def get_ai_analysis(self):
        """Retorna análise da IA como dicionário"""
        if self.ai_analysis:
            try:
                return json.loads(self.ai_analysis)
            except:
                return {}
        return {}
    
    def set_ai_analysis(self, analysis_dict):
        """Define análise da IA"""
        self.ai_analysis = json.dumps(analysis_dict) if analysis_dict else None
    
    def get_extracted_values(self):
        """Retorna valores extraídos como dicionário"""
        if self.extracted_values:
            try:
                return json.loads(self.extracted_values)
            except:
                return {}
        return {}
    
    def set_extracted_values(self, values_dict):
        """Define valores extraídos"""
        self.extracted_values = json.dumps(values_dict) if values_dict else None
    
    def get_file_size_formatted(self):
        """Retorna tamanho do arquivo formatado"""
        if not self.file_size:
            return "Desconhecido"
        
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
    
    def get_status_display(self):
        """Retorna status formatado para exibição"""
        status_map = {
            'pending': 'Aguardando processamento',
            'processing': 'Processando...',
            'completed': 'Processado',
            'error': 'Erro no processamento'
        }
        return status_map.get(self.processing_status, self.processing_status)
    
    def is_image(self):
        """Verifica se o arquivo é uma imagem"""
        return self.file_type == 'image'
    
    def is_pdf(self):
        """Verifica se o arquivo é um PDF"""
        return self.file_type == 'pdf'
    
    def file_exists(self):
        """Verifica se o arquivo ainda existe no sistema"""
        return os.path.exists(self.file_path) if self.file_path else False
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_size_formatted': self.get_file_size_formatted(),
            'file_type': self.file_type,
            'mime_type': self.mime_type,
            'exam_type': self.exam_type,
            'exam_date': self.exam_date.isoformat() if self.exam_date else None,
            'lab_name': self.lab_name,
            'doctor_name': self.doctor_name,
            'extracted_text': self.extracted_text,
            'ai_analysis': self.get_ai_analysis(),
            'extracted_values': self.get_extracted_values(),
            'ai_summary': self.ai_summary,
            'processing_status': self.processing_status,
            'status_display': self.get_status_display(),
            'processing_error': self.processing_error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'file_exists': self.file_exists()
        }
    
    def to_summary_dict(self):
        """Converte para dicionário resumido (para listas)"""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size_formatted': self.get_file_size_formatted(),
            'exam_type': self.exam_type,
            'exam_date': self.exam_date.isoformat() if self.exam_date else None,
            'lab_name': self.lab_name,
            'processing_status': self.processing_status,
            'status_display': self.get_status_display(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'has_results': bool(self.extracted_values or self.ai_summary)
        }
    
    @staticmethod
    def get_by_patient(patient_id, limit=None):
        """Retorna exames de um paciente específico"""
        query = Exam.query.filter_by(patient_id=patient_id).order_by(Exam.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def get_recent_exams(limit=10):
        """Retorna exames mais recentes"""
        return Exam.query.order_by(Exam.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_pending_processing():
        """Retorna exames pendentes de processamento"""
        return Exam.query.filter_by(processing_status='pending').order_by(Exam.created_at.asc()).all()
    
    @staticmethod
    def get_processing_stats():
        """Retorna estatísticas de processamento"""
        total = Exam.query.count()
        pending = Exam.query.filter_by(processing_status='pending').count()
        processing = Exam.query.filter_by(processing_status='processing').count()
        completed = Exam.query.filter_by(processing_status='completed').count()
        error = Exam.query.filter_by(processing_status='error').count()
        
        return {
            'total': total,
            'pending': pending,
            'processing': processing,
            'completed': completed,
            'error': error
        }


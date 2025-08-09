import os
import uuid
from werkzeug.utils import secure_filename

class FileService:
    def __init__(self, upload_folder='uploads'):
        self.upload_folder = upload_folder
        self.allowed_extensions = {'png', 'jpg', 'jpeg', 'pdf'}
        
        # Cria pasta de upload se não existir
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
    
    def allowed_file(self, filename):
        """Verifica se o arquivo tem extensão permitida"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def save_file(self, file, patient_id):
        """Salva arquivo no sistema"""
        if not file or not self.allowed_file(file.filename):
            return None, "Tipo de arquivo não permitido"
        
        # Gera nome único para o arquivo
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Cria pasta do paciente se não existir
        patient_folder = os.path.join(self.upload_folder, str(patient_id))
        if not os.path.exists(patient_folder):
            os.makedirs(patient_folder)
        
        # Salva o arquivo
        file_path = os.path.join(patient_folder, unique_filename)
        file.save(file_path)
        
        return file_path, None
    
    def extract_text_from_file(self, file_path):
        """Extrai texto do arquivo (versão simplificada)"""
        try:
            file_extension = file_path.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                return self._extract_text_from_pdf(file_path)
            elif file_extension in ['png', 'jpg', 'jpeg']:
                return "Texto extraído da imagem (OCR não disponível em produção)", None
            else:
                return None, "Tipo de arquivo não suportado"
        
        except Exception as e:
            return None, f"Erro ao extrair texto: {str(e)}"
    
    def _extract_text_from_pdf(self, file_path):
        """Extrai texto de PDF"""
        try:
            import PyPDF2
            
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            
            return text.strip(), None
        
        except Exception as e:
            return None, f"Erro ao processar PDF: {str(e)}"
    
    def delete_file(self, file_path):
        """Remove arquivo do sistema"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False


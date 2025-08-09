import os
import uuid
import mimetypes
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import io

class FileService:
    def __init__(self, upload_folder='uploads'):
        self.upload_folder = upload_folder
        self.allowed_extensions = {
            'image': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'},
            'pdf': {'pdf'}
        }
        self.max_file_size = 10 * 1024 * 1024  # 10MB por padrão
        
        # Cria diretório de upload se não existir
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def is_allowed_file(self, filename):
        """Verifica se o arquivo é permitido"""
        if not filename or '.' not in filename:
            return False, None
        
        extension = filename.rsplit('.', 1)[1].lower()
        
        for file_type, extensions in self.allowed_extensions.items():
            if extension in extensions:
                return True, file_type
        
        return False, None
    
    def get_file_info(self, file):
        """Obtém informações do arquivo"""
        filename = file.filename
        if not filename:
            return None
        
        # Verifica se é permitido
        is_allowed, file_type = self.is_allowed_file(filename)
        if not is_allowed:
            raise ValueError(f"Tipo de arquivo não permitido: {filename}")
        
        # Obtém tamanho do arquivo
        file.seek(0, 2)  # Vai para o final
        file_size = file.tell()
        file.seek(0)  # Volta para o início
        
        # Verifica tamanho
        if file_size > self.max_file_size:
            raise ValueError(f"Arquivo muito grande. Máximo permitido: {self.max_file_size / (1024*1024):.1f}MB")
        
        # Obtém MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        
        return {
            'original_filename': filename,
            'file_size': file_size,
            'file_type': file_type,
            'mime_type': mime_type or 'application/octet-stream'
        }
    
    def save_file(self, file, patient_id):
        """Salva arquivo no sistema"""
        file_info = self.get_file_info(file)
        
        # Gera nome único para o arquivo
        file_extension = file_info['original_filename'].rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Cria subdiretório por paciente
        patient_folder = os.path.join(self.upload_folder, f"patient_{patient_id}")
        os.makedirs(patient_folder, exist_ok=True)
        
        # Caminho completo do arquivo
        file_path = os.path.join(patient_folder, unique_filename)
        
        # Salva o arquivo
        file.save(file_path)
        
        # Atualiza informações
        file_info['file_path'] = file_path
        file_info['saved_filename'] = unique_filename
        
        return file_info
    
    def extract_text_from_image(self, image_path):
        """Extrai texto de imagem usando OCR"""
        try:
            # Abre a imagem
            image = Image.open(image_path)
            
            # Converte para RGB se necessário
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extrai texto usando Tesseract
            text = pytesseract.image_to_string(image, lang='por')
            
            return text.strip()
        
        except Exception as e:
            raise Exception(f"Erro ao extrair texto da imagem: {str(e)}")
    
    def extract_text_from_pdf(self, pdf_path):
        """Extrai texto de PDF"""
        try:
            text = ""
            
            # Abre o PDF
            pdf_document = fitz.open(pdf_path)
            
            # Extrai texto de cada página
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                text += page.get_text()
                text += "\n\n"  # Separador entre páginas
            
            pdf_document.close()
            
            return text.strip()
        
        except Exception as e:
            raise Exception(f"Erro ao extrair texto do PDF: {str(e)}")
    
    def extract_text_from_file(self, file_path, file_type):
        """Extrai texto do arquivo baseado no tipo"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        if file_type == 'image':
            return self.extract_text_from_image(file_path)
        elif file_type == 'pdf':
            return self.extract_text_from_pdf(file_path)
        else:
            raise ValueError(f"Tipo de arquivo não suportado para extração de texto: {file_type}")
    
    def process_image_for_analysis(self, image_path):
        """Processa imagem para melhorar OCR"""
        try:
            # Abre a imagem
            image = Image.open(image_path)
            
            # Converte para escala de cinza
            if image.mode != 'L':
                image = image.convert('L')
            
            # Redimensiona se muito pequena
            width, height = image.size
            if width < 1000 or height < 1000:
                # Aumenta a imagem mantendo proporção
                scale_factor = max(1000 / width, 1000 / height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Salva imagem processada temporariamente
            processed_path = image_path.replace('.', '_processed.')
            image.save(processed_path)
            
            return processed_path
        
        except Exception as e:
            print(f"Erro ao processar imagem: {e}")
            return image_path  # Retorna original se der erro
    
    def delete_file(self, file_path):
        """Remove arquivo do sistema"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception as e:
            print(f"Erro ao deletar arquivo {file_path}: {e}")
        
        return False
    
    def get_file_url(self, file_path):
        """Gera URL para acesso ao arquivo"""
        # Remove o prefixo do diretório de upload
        relative_path = os.path.relpath(file_path, self.upload_folder)
        return f"/api/files/{relative_path}"
    
    def validate_image_quality(self, image_path):
        """Valida qualidade da imagem para OCR"""
        try:
            image = Image.open(image_path)
            width, height = image.size
            
            issues = []
            
            # Verifica resolução mínima
            if width < 300 or height < 300:
                issues.append("Resolução muito baixa (mínimo 300x300)")
            
            # Verifica se não é muito grande
            if width > 4000 or height > 4000:
                issues.append("Resolução muito alta (máximo 4000x4000)")
            
            # Verifica formato
            if image.mode not in ['RGB', 'L', 'RGBA']:
                issues.append("Formato de cor não suportado")
            
            return len(issues) == 0, issues
        
        except Exception as e:
            return False, [f"Erro ao validar imagem: {str(e)}"]
    
    def get_storage_stats(self):
        """Retorna estatísticas de armazenamento"""
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(self.upload_folder):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                    file_count += 1
                except:
                    pass
        
        return {
            'total_files': file_count,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'upload_folder': self.upload_folder
        }


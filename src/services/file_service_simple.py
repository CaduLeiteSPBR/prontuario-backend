import os
import uuid
from werkzeug.utils import secure_filename

class FileService:
    def __init__(self, upload_folder="uploads"):
        self.upload_folder = upload_folder
        self.allowed_extensions = {"pdf", "png", "jpg", "jpeg"}

    def allowed_file(self, filename):
        return "." in filename and filename.rsplit(".", 1)[1].lower() in self.allowed_extensions

    def save_file(self, file, patient_id):
        """Salva arquivo no sistema e retorna metadados compatíveis com exam.py"""
        if not file or not self.allowed_file(file.filename):
            raise ValueError("Tipo de arquivo não permitido")

        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()

        # Cria pasta uploads/<patient_id>
        patient_folder = os.path.join(self.upload_folder, str(patient_id))
        if not os.path.exists(patient_folder):
            os.makedirs(patient_folder)

        # Salva com nome único
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(patient_folder, unique_filename)
        file.save(file_path)

        # Monta metadados
        info = {
            "original_filename": filename,
            "file_path": file_path,
            "file_size": os.path.getsize(file_path),
            "file_type": "pdf" if ext == "pdf" else "image",
            "mime_type": "application/pdf" if ext == "pdf" else f"image/{ext}"
        }
        return info

    def extract_text_from_file(self, file_path, file_type):
        """Extrai texto do arquivo (simplificado, sem OCR real para imagens)"""
        try:
            if file_type == "pdf":
                return self._extract_text_from_pdf(file_path)
            elif file_type == "image":
                # Sem OCR real no ambiente Render
                return "Texto extraído da imagem (OCR não disponível em produção)", None
            else:
                return None, "Tipo de arquivo não suportado"
        except Exception as e:
            return None, f"Erro ao extrair texto: {str(e)}"

    def _extract_text_from_pdf(self, file_path):
        try:
            import PyPDF2
            text = ""
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
            return text, None
        except Exception as e:
            return None, f"Erro ao extrair texto do PDF: {str(e)}"
    
    def delete_file(self, file_path):
        """Remove arquivo do sistema"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False


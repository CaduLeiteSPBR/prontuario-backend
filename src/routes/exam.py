from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from src.models.exam import Exam
from src.models import db
from src.models.patient import Patient
from src.services.file_service_simple import FileService
from src.services.ai_service_simple import AIService
from datetime import datetime
import os
import threading

exam_bp = Blueprint('exam', __name__)

# Inicializa serviços
file_service = FileService(upload_folder='uploads')
ai_service = AIService()

def _process_exam_now(exam: Exam):
    """
    Processa o exame imediatamente:
    - Extrai texto do arquivo (PDF/Imagem) usando FileService (versão 'simple')
    - Atualiza status e timestamps
    - Preenche campos básicos (summary/análise placeholders)
    """
    try:
        exam.processing_status = "processing"
        db.session.commit()

        text, err = file_service.extract_text_from_file(exam.file_path, exam.file_type)
        if err:
            exam.processing_status = "error"
            exam.processing_error = err
            exam.processed_at = datetime.utcnow()
            db.session.commit()
            return

        # Campos básicos (ajuste se o seu AIService tiver métodos reais)
        exam.extracted_text = text or ""
        exam.extracted_values = {}   # implementar parsing depois, se quiser
        exam.ai_analysis = {}        # idem
        exam.ai_summary = "Resumo automático: texto extraído disponível." if text else "Sem texto extraído."
        exam.processing_status = "completed"
        exam.processing_error = None
        exam.processed_at = datetime.utcnow()
        db.session.commit()

    except Exception as e:
        exam.processing_status = "error"
        exam.processing_error = str(e)
        exam.processed_at = datetime.utcnow()
        db.session.commit()

@exam_bp.route('/patients/<int:patient_id>/exams', methods=['GET'])
def get_patient_exams(patient_id):
    """Lista exames de um paciente"""
    try:
        # Verifica se paciente existe
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({
                'success': False,
                'error': 'Paciente não encontrado'
            }), 404
        
        # Parâmetros de consulta
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        status_filter = request.args.get('status', '')
        
        # Query base
        query = Exam.query.filter_by(patient_id=patient_id)
        
        # Filtro por status
        if status_filter:
            query = query.filter_by(processing_status=status_filter)
        
        # Ordenação e paginação
        query = query.order_by(Exam.created_at.desc())
        total = query.count()
        
        # Paginação manual
        offset = (page - 1) * per_page
        exams = query.offset(offset).limit(per_page).all()
        
        return jsonify({
            'success': True,
            'exams': [exam.to_summary_dict() for exam in exams],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            },
            'patient': patient.to_summary_dict()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@exam_bp.route('/patients/<int:patient_id>/exams', methods=['POST'])
def upload_exam(patient_id):
    """Upload de novo exame"""
    try:
        # Verifica se paciente existe
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({
                'success': False,
                'error': 'Paciente não encontrado'
            }), 404
        
        # Verifica se arquivo foi enviado
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo enviado'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo selecionado'
            }), 400
        
        # Salva arquivo
        try:
            file_info = file_service.save_file(file, patient_id)
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        
        # Cria registro do exame
        exam_data = {
            'patient_id': patient_id,
            'original_filename': file_info['original_filename'],
            'file_path': file_info['file_path'],
            'file_size': file_info['file_size'],
            'file_type': file_info['file_type'],
            'mime_type': file_info['mime_type'],
            'processing_status': 'pending'
        }
        
        # Adiciona informações opcionais do formulário
        if 'exam_type' in request.form:
            exam_data['exam_type'] = request.form['exam_type']
        
        if 'exam_date' in request.form and request.form['exam_date']:
            try:
                exam_data['exam_date'] = datetime.strptime(request.form['exam_date'], '%Y-%m-%d').date()
            except:
                pass
        
        if 'lab_name' in request.form:
            exam_data['lab_name'] = request.form['lab_name']
        
        if 'doctor_name' in request.form:
            exam_data['doctor_name'] = request.form['doctor_name']
        
        exam = Exam(**exam_data)
        db.session.add(exam)
        db.session.commit()
        
        # Processa imediatamente (síncrono) – mais simples e confiável no Render
        _process_exam_now(exam)
        
        return jsonify({
            'success': True,
            'message': 'Exame enviado com sucesso. Processamento iniciado.',
            'exam': exam.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@exam_bp.route('/exams/<int:exam_id>', methods=['GET'])
def get_exam(exam_id):
    """Retorna dados completos de um exame"""
    try:
        exam = Exam.query.get(exam_id)
        
        if not exam:
            return jsonify({
                'success': False,
                'error': 'Exame não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'exam': exam.to_dict()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@exam_bp.route('/exams/<int:exam_id>/reprocess', methods=['POST'])
def reprocess_exam(exam_id):
    """Reprocessa um exame"""
    try:
        exam = Exam.query.get(exam_id)
        
        if not exam:
            return jsonify({
                'success': False,
                'error': 'Exame não encontrado'
            }), 404
        
        # Reset status
        exam.processing_status = 'pending'
        exam.processing_error = None
        exam.extracted_text = None
        exam.ai_analysis = None
        exam.extracted_values = None
        exam.ai_summary = None
        exam.processed_at = None
        exam.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Inicia processamento assíncrono
        thread = threading.Thread(target=process_exam_async, args=(exam.id,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Reprocessamento iniciado'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@exam_bp.route('/exams/<int:exam_id>', methods=['DELETE'])
def delete_exam(exam_id):
    """Remove um exame"""
    try:
        exam = Exam.query.get(exam_id)
        
        if not exam:
            return jsonify({
                'success': False,
                'error': 'Exame não encontrado'
            }), 404
        
        # Remove arquivo do sistema
        if exam.file_path and os.path.exists(exam.file_path):
            file_service.delete_file(exam.file_path)
        
        # Remove registro do banco
        db.session.delete(exam)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Exame removido com sucesso'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@exam_bp.route('/files/<path:filename>')
def serve_file(filename):
    """Serve arquivos de exames"""
    try:
        file_path = os.path.join(file_service.upload_folder, filename)
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'Arquivo não encontrado'
            }), 404
        
        return send_file(file_path)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@exam_bp.route('/exams/stats', methods=['GET'])
def get_exam_stats():
    """Retorna estatísticas de exames"""
    try:
        # Estatísticas de processamento
        processing_stats = Exam.get_processing_stats()
        
        # Estatísticas de armazenamento
        storage_stats = file_service.get_storage_stats()
        
        # Exames recentes
        recent_exams = Exam.get_recent_exams(5)
        
        # Status da IA
        ai_available = ai_service.is_available()
        
        return jsonify({
            'success': True,
            'stats': {
                'processing': processing_stats,
                'storage': storage_stats,
                'ai_service': {
                    'available': ai_available,
                    'status': 'Configurado' if ai_available else 'Não configurado'
                },
                'recent_exams': [exam.to_summary_dict() for exam in recent_exams]
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@exam_bp.route('/ai/test', methods=['POST'])
def test_ai_service():
    """Testa serviço de IA"""
    try:
        success, message = ai_service.test_connection()
        
        return jsonify({
            'success': success,
            'message': message,
            'available': ai_service.is_available()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


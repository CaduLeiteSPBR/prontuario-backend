from flask import Blueprint, request, jsonify
from src.models.patient import Patient, db
from datetime import datetime
import re

patient_bp = Blueprint('patient', __name__)

def validate_cpf(cpf):
    """Valida formato do CPF"""
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verifica se não são todos os dígitos iguais
    if cpf == cpf[0] * 11:
        return False
    
    return True

def format_cpf(cpf):
    """Formata CPF para padrão XXX.XXX.XXX-XX"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) == 11:
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    return cpf

@patient_bp.route('/patients', methods=['GET'])
def get_patients():
    """Lista todos os pacientes com opção de busca"""
    try:
        query = request.args.get('search', '').strip()
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Busca pacientes
        patients = Patient.search(query, active_only)
        
        # Paginação
        total = len(patients)
        start = (page - 1) * per_page
        end = start + per_page
        patients_page = patients[start:end]
        
        return jsonify({
            'success': True,
            'patients': [patient.to_summary_dict() for patient in patients_page],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@patient_bp.route('/patients/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    """Retorna dados completos de um paciente"""
    try:
        patient = Patient.query.get(patient_id)
        
        if not patient:
            return jsonify({
                'success': False,
                'error': 'Paciente não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'patient': patient.to_dict()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@patient_bp.route('/patients', methods=['POST'])
def create_patient():
    """Cria um novo paciente"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados não fornecidos'
            }), 400
        
        # Validações obrigatórias
        required_fields = ['full_name', 'cpf', 'birth_date', 'gender']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório: {field}'
                }), 400
        
        # Valida CPF
        cpf = data['cpf']
        if not validate_cpf(cpf):
            return jsonify({
                'success': False,
                'error': 'CPF inválido'
            }), 400
        
        # Formata CPF
        formatted_cpf = format_cpf(cpf)
        
        # Verifica se CPF já existe
        existing_patient = Patient.query.filter_by(cpf=formatted_cpf).first()
        if existing_patient:
            return jsonify({
                'success': False,
                'error': 'CPF já cadastrado'
            }), 400
        
        # Converte data de nascimento
        try:
            birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Data de nascimento inválida. Use o formato YYYY-MM-DD'
            }), 400
        
        # Cria novo paciente
        patient_data = {
            'full_name': data['full_name'].strip(),
            'cpf': formatted_cpf,
            'birth_date': birth_date,
            'gender': data['gender'],
            'phone': data.get('phone', '').strip() or None,
            'email': data.get('email', '').strip() or None,
            'address_street': data.get('address_street', '').strip() or None,
            'address_number': data.get('address_number', '').strip() or None,
            'address_complement': data.get('address_complement', '').strip() or None,
            'address_neighborhood': data.get('address_neighborhood', '').strip() or None,
            'address_city': data.get('address_city', '').strip() or None,
            'address_state': data.get('address_state', '').strip() or None,
            'address_zipcode': data.get('address_zipcode', '').strip() or None,
            'allergies': data.get('allergies', []),
            'chronic_diseases': data.get('chronic_diseases', []),
            'previous_surgeries': data.get('previous_surgeries', []),
            'family_history': data.get('family_history', []),
            'current_medications': data.get('current_medications', []),
            'smoking': data.get('smoking', 'never'),
            'alcohol_consumption': data.get('alcohol_consumption', 'never'),
            'physical_activity': data.get('physical_activity', 'sedentary')
        }
        
        patient = Patient(**patient_data)
        db.session.add(patient)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Paciente cadastrado com sucesso',
            'patient': patient.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@patient_bp.route('/patients/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    """Atualiza dados de um paciente"""
    try:
        patient = Patient.query.get(patient_id)
        
        if not patient:
            return jsonify({
                'success': False,
                'error': 'Paciente não encontrado'
            }), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados não fornecidos'
            }), 400
        
        # Atualiza campos básicos
        if 'full_name' in data:
            patient.full_name = data['full_name'].strip()
        
        if 'cpf' in data:
            cpf = data['cpf']
            if not validate_cpf(cpf):
                return jsonify({
                    'success': False,
                    'error': 'CPF inválido'
                }), 400
            
            formatted_cpf = format_cpf(cpf)
            
            # Verifica se CPF já existe (exceto o próprio paciente)
            existing_patient = Patient.query.filter(
                Patient.cpf == formatted_cpf,
                Patient.id != patient_id
            ).first()
            
            if existing_patient:
                return jsonify({
                    'success': False,
                    'error': 'CPF já cadastrado para outro paciente'
                }), 400
            
            patient.cpf = formatted_cpf
        
        if 'birth_date' in data:
            try:
                patient.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Data de nascimento inválida. Use o formato YYYY-MM-DD'
                }), 400
        
        # Atualiza outros campos
        simple_fields = [
            'gender', 'phone', 'email', 'address_street', 'address_number',
            'address_complement', 'address_neighborhood', 'address_city',
            'address_state', 'address_zipcode', 'smoking', 'alcohol_consumption',
            'physical_activity'
        ]
        
        for field in simple_fields:
            if field in data:
                value = data[field].strip() if isinstance(data[field], str) else data[field]
                setattr(patient, field, value or None)
        
        # Atualiza listas médicas
        if 'allergies' in data:
            patient.set_allergies(data['allergies'])
        
        if 'chronic_diseases' in data:
            patient.set_chronic_diseases(data['chronic_diseases'])
        
        if 'previous_surgeries' in data:
            patient.set_previous_surgeries(data['previous_surgeries'])
        
        if 'family_history' in data:
            patient.set_family_history(data['family_history'])
        
        if 'current_medications' in data:
            patient.set_current_medications(data['current_medications'])
        
        if 'active' in data:
            patient.active = bool(data['active'])
        
        patient.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Paciente atualizado com sucesso',
            'patient': patient.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@patient_bp.route('/patients/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    """Desativa um paciente (soft delete)"""
    try:
        patient = Patient.query.get(patient_id)
        
        if not patient:
            return jsonify({
                'success': False,
                'error': 'Paciente não encontrado'
            }), 404
        
        patient.active = False
        patient.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Paciente desativado com sucesso'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@patient_bp.route('/patients/<int:patient_id>/activate', methods=['POST'])
def activate_patient(patient_id):
    """Reativa um paciente"""
    try:
        patient = Patient.query.get(patient_id)
        
        if not patient:
            return jsonify({
                'success': False,
                'error': 'Paciente não encontrado'
            }), 404
        
        patient.active = True
        patient.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Paciente reativado com sucesso'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


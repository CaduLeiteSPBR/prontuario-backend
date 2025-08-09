from flask import Blueprint, request, jsonify
from src.models.patient import Patient
from src.models.exam import Exam
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import json

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/patients/<int:patient_id>/medical-record', methods=['GET'])
def get_patient_medical_record(patient_id):
    """Retorna prontuário completo do paciente"""
    try:
        # Verifica se paciente existe
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({
                'success': False,
                'error': 'Paciente não encontrado'
            }), 404
        
        # Parâmetros de consulta
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        exam_type = request.args.get('exam_type')
        
        # Query base para exames
        exams_query = Exam.query.filter_by(patient_id=patient_id)
        
        # Filtros opcionais
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                exams_query = exams_query.filter(Exam.exam_date >= start_date_obj)
            except:
                pass
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                exams_query = exams_query.filter(Exam.exam_date <= end_date_obj)
            except:
                pass
        
        if exam_type:
            exams_query = exams_query.filter(Exam.exam_type.ilike(f'%{exam_type}%'))
        
        # Busca exames ordenados por data
        exams = exams_query.order_by(Exam.exam_date.desc(), Exam.created_at.desc()).all()
        
        # Estatísticas gerais
        total_exams = len(exams)
        completed_exams = len([e for e in exams if e.processing_status == 'completed'])
        recent_exams = len([e for e in exams if e.created_at >= datetime.utcnow() - timedelta(days=30)])
        
        # Tipos de exames únicos
        exam_types = list(set([e.exam_type for e in exams if e.exam_type]))
        
        # Laboratórios únicos
        labs = list(set([e.lab_name for e in exams if e.lab_name]))
        
        return jsonify({
            'success': True,
            'patient': patient.to_dict(),
            'exams': [exam.to_dict() for exam in exams],
            'statistics': {
                'total_exams': total_exams,
                'completed_exams': completed_exams,
                'recent_exams': recent_exams,
                'processing_rate': round((completed_exams / total_exams * 100) if total_exams > 0 else 0, 1),
                'exam_types': exam_types,
                'labs': labs
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/patients/<int:patient_id>/timeline', methods=['GET'])
def get_patient_timeline(patient_id):
    """Retorna timeline de eventos do paciente"""
    try:
        # Verifica se paciente existe
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({
                'success': False,
                'error': 'Paciente não encontrado'
            }), 404
        
        # Busca exames do paciente
        exams = Exam.query.filter_by(patient_id=patient_id).order_by(Exam.created_at.desc()).all()
        
        # Cria timeline de eventos
        timeline = []
        
        # Adiciona cadastro do paciente
        timeline.append({
            'id': f'patient_{patient.id}',
            'type': 'patient_created',
            'title': 'Paciente Cadastrado',
            'description': f'Cadastro de {patient.full_name} no sistema',
            'date': patient.created_at.isoformat() if patient.created_at else None,
            'icon': 'user-plus',
            'color': 'blue'
        })
        
        # Adiciona exames
        for exam in exams:
            timeline.append({
                'id': f'exam_{exam.id}',
                'type': 'exam_uploaded',
                'title': f'Exame Enviado: {exam.original_filename}',
                'description': f'Tipo: {exam.exam_type or "Não especificado"} | Status: {exam.get_status_display()}',
                'date': exam.created_at.isoformat() if exam.created_at else None,
                'exam_date': exam.exam_date.isoformat() if exam.exam_date else None,
                'icon': 'file-text',
                'color': 'green' if exam.processing_status == 'completed' else 'yellow' if exam.processing_status == 'pending' else 'red',
                'exam_id': exam.id,
                'has_results': bool(exam.ai_summary or exam.extracted_values)
            })
        
        # Ordena por data (mais recente primeiro)
        timeline.sort(key=lambda x: x['date'] or '', reverse=True)
        
        return jsonify({
            'success': True,
            'patient': patient.to_summary_dict(),
            'timeline': timeline
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/patients/<int:patient_id>/trends', methods=['GET'])
def get_patient_trends(patient_id):
    """Retorna dados para gráficos de tendências"""
    try:
        # Verifica se paciente existe
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({
                'success': False,
                'error': 'Paciente não encontrado'
            }), 404
        
        # Parâmetros
        parameter = request.args.get('parameter', '')  # Nome do parâmetro a analisar
        months = int(request.args.get('months', 12))  # Últimos X meses
        
        # Data limite
        start_date = datetime.utcnow() - timedelta(days=months * 30)
        
        # Busca exames com resultados processados
        exams = Exam.query.filter(
            and_(
                Exam.patient_id == patient_id,
                Exam.processing_status == 'completed',
                Exam.extracted_values.isnot(None),
                Exam.created_at >= start_date
            )
        ).order_by(Exam.exam_date.asc(), Exam.created_at.asc()).all()
        
        # Extrai dados para gráficos
        trends_data = []
        parameter_values = []
        
        for exam in exams:
            try:
                values = exam.get_extracted_values()
                if 'valores' in values:
                    for valor in values['valores']:
                        # Se parâmetro específico foi solicitado
                        if parameter and parameter.lower() in valor.get('nome', '').lower():
                            try:
                                numeric_value = float(valor.get('valor', '').replace(',', '.'))
                                trends_data.append({
                                    'date': exam.exam_date.isoformat() if exam.exam_date else exam.created_at.date().isoformat(),
                                    'value': numeric_value,
                                    'parameter': valor.get('nome'),
                                    'unit': valor.get('unidade'),
                                    'reference': valor.get('referencia'),
                                    'exam_id': exam.id,
                                    'exam_type': exam.exam_type
                                })
                            except:
                                pass
                        
                        # Coleta todos os parâmetros disponíveis
                        param_name = valor.get('nome', '').strip()
                        if param_name and param_name not in parameter_values:
                            parameter_values.append(param_name)
            except:
                continue
        
        # Se nenhum parâmetro específico, retorna os mais comuns
        if not parameter and parameter_values:
            # Conta frequência dos parâmetros
            param_count = {}
            for exam in exams:
                try:
                    values = exam.get_extracted_values()
                    if 'valores' in values:
                        for valor in values['valores']:
                            param_name = valor.get('nome', '').strip()
                            if param_name:
                                param_count[param_name] = param_count.get(param_name, 0) + 1
                except:
                    continue
            
            # Pega os 5 parâmetros mais frequentes
            common_params = sorted(param_count.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Gera dados para cada parâmetro comum
            trends_by_param = {}
            for param_name, count in common_params:
                param_data = []
                for exam in exams:
                    try:
                        values = exam.get_extracted_values()
                        if 'valores' in values:
                            for valor in values['valores']:
                                if valor.get('nome', '').strip() == param_name:
                                    try:
                                        numeric_value = float(valor.get('valor', '').replace(',', '.'))
                                        param_data.append({
                                            'date': exam.exam_date.isoformat() if exam.exam_date else exam.created_at.date().isoformat(),
                                            'value': numeric_value,
                                            'unit': valor.get('unidade'),
                                            'reference': valor.get('referencia'),
                                            'exam_id': exam.id
                                        })
                                    except:
                                        pass
                    except:
                        continue
                
                if param_data:
                    trends_by_param[param_name] = sorted(param_data, key=lambda x: x['date'])
            
            return jsonify({
                'success': True,
                'patient': patient.to_summary_dict(),
                'trends_by_parameter': trends_by_param,
                'available_parameters': parameter_values,
                'period_months': months
            })
        
        return jsonify({
            'success': True,
            'patient': patient.to_summary_dict(),
            'trends_data': sorted(trends_data, key=lambda x: x['date']),
            'available_parameters': parameter_values,
            'selected_parameter': parameter,
            'period_months': months
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/patients/<int:patient_id>/summary', methods=['GET'])
def get_patient_summary(patient_id):
    """Retorna resumo executivo do paciente"""
    try:
        # Verifica se paciente existe
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({
                'success': False,
                'error': 'Paciente não encontrado'
            }), 404
        
        # Estatísticas de exames
        total_exams = Exam.query.filter_by(patient_id=patient_id).count()
        completed_exams = Exam.query.filter_by(patient_id=patient_id, processing_status='completed').count()
        pending_exams = Exam.query.filter_by(patient_id=patient_id, processing_status='pending').count()
        error_exams = Exam.query.filter_by(patient_id=patient_id, processing_status='error').count()
        
        # Exames recentes (últimos 30 dias)
        recent_date = datetime.utcnow() - timedelta(days=30)
        recent_exams = Exam.query.filter(
            and_(
                Exam.patient_id == patient_id,
                Exam.created_at >= recent_date
            )
        ).count()
        
        # Último exame
        last_exam = Exam.query.filter_by(patient_id=patient_id).order_by(Exam.created_at.desc()).first()
        
        # Tipos de exames únicos
        exam_types_query = Exam.query.filter_by(patient_id=patient_id).with_entities(Exam.exam_type).distinct()
        exam_types = [t[0] for t in exam_types_query.all() if t[0]]
        
        # Laboratórios únicos
        labs_query = Exam.query.filter_by(patient_id=patient_id).with_entities(Exam.lab_name).distinct()
        labs = [l[0] for l in labs_query.all() if l[0]]
        
        # Valores alterados recentes
        altered_values = []
        recent_completed_exams = Exam.query.filter(
            and_(
                Exam.patient_id == patient_id,
                Exam.processing_status == 'completed',
                Exam.created_at >= recent_date
            )
        ).order_by(Exam.created_at.desc()).limit(5).all()
        
        for exam in recent_completed_exams:
            try:
                analysis = exam.get_ai_analysis()
                if 'valores_alterados' in analysis and analysis['valores_alterados']:
                    for valor in analysis['valores_alterados']:
                        altered_values.append({
                            'parameter': valor.get('parametro'),
                            'value': valor.get('valor'),
                            'reference': valor.get('referencia'),
                            'alteration_type': valor.get('tipo_alteracao'),
                            'exam_date': exam.exam_date.isoformat() if exam.exam_date else None,
                            'exam_type': exam.exam_type,
                            'exam_id': exam.id
                        })
            except:
                continue
        
        return jsonify({
            'success': True,
            'patient': patient.to_dict(),
            'summary': {
                'exams_statistics': {
                    'total': total_exams,
                    'completed': completed_exams,
                    'pending': pending_exams,
                    'error': error_exams,
                    'recent': recent_exams,
                    'completion_rate': round((completed_exams / total_exams * 100) if total_exams > 0 else 0, 1)
                },
                'last_exam': last_exam.to_summary_dict() if last_exam else None,
                'exam_types': exam_types,
                'laboratories': labs,
                'recent_altered_values': altered_values[:10],  # Últimos 10 valores alterados
                'alerts': {
                    'pending_exams': pending_exams > 0,
                    'error_exams': error_exams > 0,
                    'no_recent_exams': recent_exams == 0 and total_exams > 0,
                    'altered_values': len(altered_values) > 0
                }
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Retorna estatísticas gerais do sistema"""
    try:
        # Estatísticas de pacientes
        total_patients = Patient.query.count()
        active_patients = Patient.query.filter_by(is_active=True).count()
        
        # Estatísticas de exames
        total_exams = Exam.query.count()
        completed_exams = Exam.query.filter_by(processing_status='completed').count()
        pending_exams = Exam.query.filter_by(processing_status='pending').count()
        error_exams = Exam.query.filter_by(processing_status='error').count()
        
        # Exames recentes (últimos 7 dias)
        recent_date = datetime.utcnow() - timedelta(days=7)
        recent_exams = Exam.query.filter(Exam.created_at >= recent_date).count()
        
        # Exames por dia (últimos 30 dias)
        exams_by_day = []
        for i in range(30):
            day = datetime.utcnow() - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            count = Exam.query.filter(
                and_(
                    Exam.created_at >= day_start,
                    Exam.created_at < day_end
                )
            ).count()
            
            exams_by_day.append({
                'date': day.date().isoformat(),
                'count': count
            })
        
        exams_by_day.reverse()  # Ordem cronológica
        
        return jsonify({
            'success': True,
            'stats': {
                'patients': {
                    'total': total_patients,
                    'active': active_patients,
                    'inactive': total_patients - active_patients
                },
                'exams': {
                    'total': total_exams,
                    'completed': completed_exams,
                    'pending': pending_exams,
                    'error': error_exams,
                    'recent': recent_exams,
                    'completion_rate': round((completed_exams / total_exams * 100) if total_exams > 0 else 0, 1)
                },
                'exams_by_day': exams_by_day
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


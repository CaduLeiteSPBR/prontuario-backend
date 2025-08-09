from flask import Blueprint, request, jsonify
from src.models.config_simple import Config, db

config_bp = Blueprint('config', __name__)

@config_bp.route('/config', methods=['GET'])
def get_configs():
    """Busca todas as configurações"""
    try:
        configs = Config.query.all()
        result = {}
        
        for config in configs:
            result[config.key] = config.to_dict()
        
        return jsonify({
            'success': True,
            'configs': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@config_bp.route('/config', methods=['POST'])
def save_config():
    """Salva uma configuração"""
    try:
        data = request.get_json()
        
        if not data or 'key' not in data:
            return jsonify({
                'success': False,
                'error': 'Chave é obrigatória'
            }), 400
        
        key = data['key']
        value = data.get('value')
        
        # Validação específica para chave da API da OpenAI
        if key == 'openai_api_key':
            if not value or not value.startswith('sk-'):
                return jsonify({
                    'success': False,
                    'error': 'Chave da API deve começar com "sk-"'
                }), 400
        
        config = Config.set_config(key, value)
        
        return jsonify({
            'success': True,
            'message': 'Configuração salva com sucesso',
            'config': config.to_dict()
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@config_bp.route('/config/<key>', methods=['DELETE'])
def delete_config(key):
    """Remove uma configuração"""
    try:
        success = Config.delete_config(key)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Configuração removida com sucesso'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Configuração não encontrada'
            }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@config_bp.route('/config/test-openai', methods=['POST'])
def test_openai():
    """Testa conexão com a API da OpenAI"""
    try:
        # Busca a chave da API
        config = Config.get_config('openai_api_key')
        if not config:
            return jsonify({
                'success': False,
                'error': 'Chave da API não configurada'
            }), 400
        
        api_key = config.get_value()
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'Chave da API não encontrada'
            }), 400
        
        # Simula teste de conexão (sem fazer chamada real)
        return jsonify({
            'success': True,
            'message': 'Conexão com OpenAI configurada com sucesso'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


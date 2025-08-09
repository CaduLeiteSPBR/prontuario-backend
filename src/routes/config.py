from flask import Blueprint, request, jsonify
from src.models.config import Config, db
import openai
import os

config_bp = Blueprint('config', __name__)

@config_bp.route('/config', methods=['GET'])
def get_configs():
    """Retorna todas as configurações (sem valores sensíveis)"""
    try:
        configs = Config.query.all()
        config_dict = {}
        
        for config in configs:
            if config.is_encrypted:
                # Para configurações criptografadas, apenas indica se está configurada
                config_dict[config.key] = {
                    'configured': bool(config.get_value()),
                    'is_encrypted': True
                }
            else:
                config_dict[config.key] = {
                    'value': config.get_value(),
                    'is_encrypted': False
                }
        
        return jsonify({
            'success': True,
            'configs': config_dict
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@config_bp.route('/config/<key>', methods=['GET'])
def get_config(key):
    """Retorna uma configuração específica"""
    try:
        config = Config.query.filter_by(key=key).first()
        
        if not config:
            return jsonify({
                'success': False,
                'error': 'Configuração não encontrada'
            }), 404
        
        if config.is_encrypted:
            # Para configurações criptografadas, apenas indica se está configurada
            return jsonify({
                'success': True,
                'key': key,
                'configured': bool(config.get_value()),
                'is_encrypted': True
            })
        else:
            return jsonify({
                'success': True,
                'key': key,
                'value': config.get_value(),
                'is_encrypted': False
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@config_bp.route('/config/<key>', methods=['POST'])
def set_config(key):
    """Define uma configuração"""
    try:
        data = request.get_json()
        
        if not data or 'value' not in data:
            return jsonify({
                'success': False,
                'error': 'Valor é obrigatório'
            }), 400
        
        value = data['value']
        is_encrypted = data.get('is_encrypted', False)
        
        # Validações específicas para chave da API
        if key == 'openai_api_key':
            if not value.startswith('sk-'):
                return jsonify({
                    'success': False,
                    'error': 'A chave da API deve começar com "sk-"'
                }), 400
            is_encrypted = True  # Sempre criptografar chaves da API
        
        # Salva a configuração
        Config.set_config(key, value, is_encrypted)
        
        return jsonify({
            'success': True,
            'message': 'Configuração salva com sucesso',
            'key': key,
            'is_encrypted': is_encrypted
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@config_bp.route('/config/test-openai', methods=['POST'])
def test_openai_connection():
    """Testa a conexão com a API da OpenAI"""
    try:
        # Recupera a chave da API
        api_key = Config.get_config('openai_api_key')
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'Chave da API não configurada'
            }), 400
        
        # Configura o cliente OpenAI
        client = openai.OpenAI(api_key=api_key)
        
        # Faz uma chamada simples para testar a conexão
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Responda apenas 'OK' para testar a conexão."}
            ],
            max_tokens=10
        )
        
        if response.choices and response.choices[0].message:
            return jsonify({
                'success': True,
                'message': 'Conexão com a API da OpenAI testada com sucesso!',
                'response': response.choices[0].message.content.strip()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Resposta inválida da API da OpenAI'
            }), 500
    
    except openai.AuthenticationError:
        return jsonify({
            'success': False,
            'error': 'Chave da API inválida ou expirada'
        }), 401
    
    except openai.RateLimitError:
        return jsonify({
            'success': False,
            'error': 'Limite de taxa excedido. Tente novamente mais tarde.'
        }), 429
    
    except openai.APIError as e:
        return jsonify({
            'success': False,
            'error': f'Erro da API da OpenAI: {str(e)}'
        }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro inesperado: {str(e)}'
        }), 500

@config_bp.route('/config/<key>', methods=['DELETE'])
def delete_config(key):
    """Remove uma configuração"""
    try:
        config = Config.query.filter_by(key=key).first()
        
        if not config:
            return jsonify({
                'success': False,
                'error': 'Configuração não encontrada'
            }), 404
        
        db.session.delete(config)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Configuração removida com sucesso'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


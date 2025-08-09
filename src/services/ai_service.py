import openai
import json
import re
from datetime import datetime
from flask import current_app

class AIService:
    def __init__(self):
        self.client = None
    
    def _initialize_client(self):
        """Inicializa cliente da OpenAI com chave da configuração"""
        try:
            # Importa dentro da função para evitar circular import
            from src.models.config import Config
            
            config = Config.get_config('openai_api_key')
            if config and config.value:
                openai.api_key = config.value
                self.client = openai
                return True
        except Exception as e:
            print(f"Erro ao inicializar cliente OpenAI: {e}")
        
        return False
    
    def is_available(self):
        """Verifica se o serviço de IA está disponível"""
        if self.client is None:
            self._initialize_client()
        return self.client is not None
    
    def analyze_exam_text(self, text, exam_type=None):
        """Analisa texto de exame usando IA"""
        if not self.is_available():
            raise Exception("Serviço de IA não está configurado")
        
        try:
            # Prompt específico para análise de exames médicos
            system_prompt = """Você é um assistente médico especializado em análise de laudos de exames laboratoriais e de imagem. 
            Sua tarefa é extrair informações estruturadas de laudos médicos e fornecer uma análise clara e objetiva.
            
            Para cada exame, você deve:
            1. Identificar o tipo de exame
            2. Extrair todos os valores numéricos com suas unidades e referências
            3. Identificar valores alterados (acima ou abaixo da referência)
            4. Fornecer um resumo clínico objetivo
            5. Sugerir possíveis interpretações clínicas (sem diagnóstico definitivo)
            
            Responda sempre em português brasileiro e em formato JSON estruturado."""
            
            user_prompt = f"""Analise o seguinte laudo de exame médico e extraia as informações estruturadas:

TEXTO DO EXAME:
{text}

Retorne um JSON com a seguinte estrutura:
{{
    "tipo_exame": "tipo identificado do exame",
    "data_exame": "data do exame se encontrada (formato YYYY-MM-DD)",
    "laboratorio": "nome do laboratório se encontrado",
    "medico_solicitante": "nome do médico se encontrado",
    "valores_extraidos": [
        {{
            "parametro": "nome do parâmetro",
            "valor": "valor encontrado",
            "unidade": "unidade de medida",
            "referencia": "valores de referência",
            "status": "normal/alterado/critico"
        }}
    ],
    "valores_alterados": [
        {{
            "parametro": "nome do parâmetro alterado",
            "valor": "valor encontrado",
            "referencia": "valores de referência",
            "tipo_alteracao": "alto/baixo/critico"
        }}
    ],
    "resumo_clinico": "resumo objetivo dos principais achados",
    "interpretacao_sugerida": "possíveis interpretações clínicas dos resultados",
    "observacoes": "observações adicionais importantes"
}}"""
            
            response = self.client.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Extrai o conteúdo da resposta
            content = response.choices[0].message.content.strip()
            
            # Tenta extrair JSON da resposta
            try:
                # Remove possíveis marcadores de código
                content = re.sub(r'```json\s*', '', content)
                content = re.sub(r'```\s*$', '', content)
                
                analysis = json.loads(content)
                return analysis
            
            except json.JSONDecodeError:
                # Se não conseguir parsear como JSON, retorna estrutura básica
                return {
                    "tipo_exame": exam_type or "Não identificado",
                    "resumo_clinico": content,
                    "erro": "Resposta da IA não está em formato JSON válido"
                }
        
        except Exception as e:
            raise Exception(f"Erro na análise da IA: {str(e)}")
    
    def extract_exam_values(self, text):
        """Extrai valores numéricos de exames usando regex e IA"""
        if not self.is_available():
            return self._extract_values_regex(text)
        
        try:
            system_prompt = """Você é um especialista em extração de dados de laudos médicos.
            Extraia TODOS os valores numéricos encontrados no texto, incluindo suas unidades e valores de referência.
            Seja preciso e não invente valores que não estão no texto."""
            
            user_prompt = f"""Extraia todos os valores numéricos deste laudo médico:

{text}

Retorne um JSON com esta estrutura:
{{
    "valores": [
        {{
            "nome": "nome do parâmetro exato como aparece no texto",
            "valor": "valor numérico",
            "unidade": "unidade de medida",
            "referencia": "valores de referência se disponíveis",
            "linha_original": "linha completa onde foi encontrado"
        }}
    ]
}}"""
            
            response = self.client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            content = re.sub(r'```json\s*', '', content)
            content = re.sub(r'```\s*$', '', content)
            
            return json.loads(content)
        
        except Exception as e:
            print(f"Erro na extração de valores pela IA: {e}")
            return self._extract_values_regex(text)
    
    def _extract_values_regex(self, text):
        """Extração de valores usando regex como fallback"""
        values = []
        
        # Padrões regex para diferentes tipos de valores
        patterns = [
            # Padrão: Nome: Valor Unidade (Referência)
            r'([A-Za-zÀ-ÿ\s]+):\s*([0-9,\.]+)\s*([a-zA-Z\/\%µ]*)\s*(?:\(([^)]+)\))?',
            # Padrão: Nome Valor Unidade
            r'([A-Za-zÀ-ÿ\s]+)\s+([0-9,\.]+)\s+([a-zA-Z\/\%µ]+)',
            # Padrão mais flexível
            r'([A-Za-zÀ-ÿ\s]{3,})\s*[:\-]\s*([0-9,\.]+)\s*([a-zA-Z\/\%µ]*)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                value = match.group(2).strip()
                unit = match.group(3).strip() if len(match.groups()) > 2 else ""
                reference = match.group(4).strip() if len(match.groups()) > 3 and match.group(4) else ""
                
                # Filtros para evitar falsos positivos
                if len(name) > 2 and len(value) > 0:
                    values.append({
                        "nome": name,
                        "valor": value,
                        "unidade": unit,
                        "referencia": reference,
                        "linha_original": match.group(0)
                    })
        
        return {"valores": values}
    
    def generate_summary(self, analysis_data):
        """Gera resumo executivo da análise"""
        if not self.is_available():
            return "Resumo automático não disponível - serviço de IA não configurado"
        
        try:
            prompt = f"""Com base na análise do exame médico abaixo, gere um resumo executivo claro e objetivo em português:

{json.dumps(analysis_data, indent=2, ensure_ascii=False)}

O resumo deve:
1. Destacar os principais achados
2. Mencionar valores alterados se houver
3. Ser compreensível para profissionais de saúde
4. Ter no máximo 200 palavras
5. Não fazer diagnósticos definitivos"""
            
            response = self.client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            return f"Erro ao gerar resumo: {str(e)}"
    
    def test_connection(self):
        """Testa conexão com a API da OpenAI"""
        if not self.is_available():
            return False, "Cliente OpenAI não inicializado"
        
        try:
            response = self.client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Teste de conexão. Responda apenas 'OK'."}
                ],
                max_tokens=10
            )
            
            return True, "Conexão estabelecida com sucesso"
        
        except Exception as e:
            return False, f"Erro na conexão: {str(e)}"


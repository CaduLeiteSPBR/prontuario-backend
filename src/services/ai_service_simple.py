import re
import json
from datetime import datetime

class AIService:
    def __init__(self):
        self.api_key = None
    
    def set_api_key(self, api_key):
        """Define a chave da API"""
        self.api_key = api_key
    
    def analyze_exam_text(self, text, exam_type=None):
        """Analisa texto do exame usando regex (fallback sem IA)"""
        try:
            # Análise básica usando regex
            analysis = self._analyze_with_regex(text, exam_type)
            
            return {
                'success': True,
                'analysis': analysis,
                'method': 'regex_fallback'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'method': 'regex_fallback'
            }
    
    def _analyze_with_regex(self, text, exam_type):
        """Análise básica usando expressões regulares"""
        analysis = {
            'exam_type': exam_type or self._detect_exam_type(text),
            'laboratory': self._extract_laboratory(text),
            'doctor': self._extract_doctor(text),
            'exam_date': self._extract_date(text),
            'values': self._extract_values(text),
            'summary': self._generate_summary(text),
            'altered_values': []
        }
        
        # Identifica valores alterados
        analysis['altered_values'] = self._identify_altered_values(analysis['values'])
        
        return analysis
    
    def _detect_exam_type(self, text):
        """Detecta tipo de exame baseado no texto"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['hemograma', 'hemácias', 'leucócitos', 'plaquetas']):
            return 'Hemograma'
        elif any(word in text_lower for word in ['glicose', 'colesterol', 'triglicérides', 'ureia']):
            return 'Bioquímica'
        elif any(word in text_lower for word in ['urina', 'urocultura', 'sedimento']):
            return 'Urina'
        elif any(word in text_lower for word in ['raio-x', 'radiografia', 'tomografia', 'ressonância']):
            return 'Imagem'
        else:
            return 'Exame Laboratorial'
    
    def _extract_laboratory(self, text):
        """Extrai nome do laboratório"""
        # Padrões comuns para laboratórios
        lab_patterns = [
            r'laboratório\s+([^\\n]+)',
            r'lab\.\s+([^\\n]+)',
            r'centro\s+de\s+análises\s+([^\\n]+)'
        ]
        
        for pattern in lab_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_doctor(self, text):
        """Extrai nome do médico"""
        # Padrões comuns para médicos
        doctor_patterns = [
            r'dr\.?\s+([^\\n]+)',
            r'dra\.?\s+([^\\n]+)',
            r'médico\s*:\s*([^\\n]+)',
            r'solicitante\s*:\s*([^\\n]+)'
        ]
        
        for pattern in doctor_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_date(self, text):
        """Extrai data do exame"""
        # Padrões de data
        date_patterns = [
            r'(\\d{1,2}[/\\-]\\d{1,2}[/\\-]\\d{4})',
            r'(\\d{1,2}\\s+de\\s+\\w+\\s+de\\s+\\d{4})',
            r'data\s*:\s*(\\d{1,2}[/\\-]\\d{1,2}[/\\-]\\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_values(self, text):
        """Extrai valores numéricos do exame"""
        values = []
        
        # Padrão para valores com unidades
        value_pattern = r'([a-záêçõ\\s]+)\\s*:?\\s*(\\d+[,.]?\\d*)\\s*([a-z/%]+)?'
        
        matches = re.findall(value_pattern, text, re.IGNORECASE)
        
        for match in matches:
            parameter = match[0].strip()
            value = match[1].replace(',', '.')
            unit = match[2] if match[2] else ''
            
            if parameter and value:
                values.append({
                    'parameter': parameter,
                    'value': float(value) if '.' in value else int(value),
                    'unit': unit,
                    'raw_text': f"{parameter}: {value} {unit}".strip()
                })
        
        return values
    
    def _identify_altered_values(self, values):
        """Identifica valores alterados baseado em referências comuns"""
        altered = []
        
        # Referências básicas (valores aproximados)
        references = {
            'glicose': {'min': 70, 'max': 99, 'unit': 'mg/dl'},
            'colesterol': {'min': 0, 'max': 200, 'unit': 'mg/dl'},
            'triglicérides': {'min': 0, 'max': 150, 'unit': 'mg/dl'},
            'hemoglobina': {'min': 12, 'max': 16, 'unit': 'g/dl'},
            'hematócrito': {'min': 36, 'max': 48, 'unit': '%'}
        }
        
        for value in values:
            param_lower = value['parameter'].lower()
            
            for ref_param, ref_range in references.items():
                if ref_param in param_lower:
                    if value['value'] < ref_range['min'] or value['value'] > ref_range['max']:
                        altered.append({
                            'parameter': value['parameter'],
                            'value': value['value'],
                            'unit': value['unit'],
                            'reference_min': ref_range['min'],
                            'reference_max': ref_range['max'],
                            'status': 'alto' if value['value'] > ref_range['max'] else 'baixo'
                        })
                    break
        
        return altered
    
    def _generate_summary(self, text):
        """Gera resumo básico do exame"""
        # Resumo simples baseado no tamanho do texto
        if len(text) < 200:
            return "Exame com poucos parâmetros analisados."
        elif len(text) < 500:
            return "Exame com múltiplos parâmetros laboratoriais."
        else:
            return "Exame completo com análise detalhada de diversos parâmetros."


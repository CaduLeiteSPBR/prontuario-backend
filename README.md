# Sistema de Prontuário Médico - Backend

API Flask para gerenciamento de prontuários médicos com processamento inteligente de exames.

## 🚀 Deploy no Render

### Configuração Automática
Este repositório está configurado para deploy automático no Render.

### Variáveis de Ambiente Necessárias
- `SECRET_KEY`: Chave secreta do Flask (será gerada automaticamente)
- `DATABASE_URL`: URL do banco de dados (opcional, usa SQLite por padrão)

### Arquivos de Configuração
- `render.yaml`: Configuração do serviço Render
- `Procfile`: Comando de inicialização
- `requirements.txt`: Dependências Python

## 🛠️ Funcionalidades

### APIs Disponíveis
- `/api/config` - Gerenciamento de configurações
- `/api/patients` - CRUD de pacientes
- `/api/exams` - Upload e processamento de exames
- `/api/reports` - Relatórios e análises
- `/health` - Health check

### Recursos Implementados
- ✅ Criptografia de dados sensíveis
- ✅ Processamento de arquivos (PDF/Imagens)
- ✅ Análise inteligente de exames
- ✅ APIs RESTful com CORS
- ✅ Validações de entrada
- ✅ Sistema de logs

## 🔧 Desenvolvimento Local

### Pré-requisitos
- Python 3.11+
- pip

### Instalação
```bash
# Clonar repositório
git clone <seu-repo>
cd prontuario-backend

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
python src/main.py
```

### Estrutura do Projeto
```
src/
├── models/          # Modelos de dados
├── routes/          # Rotas da API
├── services/        # Serviços (IA, arquivos)
└── main.py         # Aplicação principal
```

## 📋 Tecnologias

- **Flask**: Framework web
- **SQLAlchemy**: ORM para banco de dados
- **Flask-CORS**: Suporte a CORS
- **PyPDF2**: Processamento de PDFs
- **Gunicorn**: Servidor WSGI para produção

## 🔒 Segurança

- Criptografia de chaves da API
- Validação de entrada de dados
- CORS configurado adequadamente
- Sanitização de uploads de arquivos

## 📝 Licença

Este projeto é de uso pessoal para fins médicos.


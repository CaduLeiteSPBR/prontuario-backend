# 🚀 Deploy no Render - Backend

## Configuração Automática

Este repositório está configurado para deploy automático no Render usando o arquivo `render.yaml`.

## Passos para Deploy

### 1. Conectar Repositório
1. Acesse [render.com](https://render.com)
2. Clique em **"New +"** → **"Web Service"**
3. Conecte sua conta do GitHub
4. Selecione este repositório
5. Clique em **"Connect"**

### 2. Configuração Automática
O Render detectará automaticamente o arquivo `render.yaml` e configurará:
- **Runtime**: Python 3.11
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn -w 4 -b 0.0.0.0:$PORT src.main:app`
- **Health Check**: `/health`
- **Plan**: Free

### 3. Variáveis de Ambiente
Serão configuradas automaticamente:
- `PYTHON_VERSION`: 3.11.0
- `SECRET_KEY`: Gerada automaticamente
- `FLASK_ENV`: production

### 4. Aguardar Deploy
- O deploy levará 3-5 minutos
- Você pode acompanhar os logs em tempo real
- Quando concluído, você receberá uma URL

### 5. Testar
Acesse `https://sua-url.onrender.com/health` para verificar se está funcionando.

## Estrutura de Arquivos Importantes

```
├── src/
│   ├── main.py              # Aplicação principal
│   ├── models/              # Modelos de dados
│   ├── routes/              # Rotas da API
│   └── services/            # Serviços (IA, arquivos)
├── requirements.txt         # Dependências Python
├── render.yaml             # Configuração do Render
├── Procfile               # Comando de inicialização
└── README.md              # Documentação
```

## APIs Disponíveis

- `GET /health` - Health check
- `GET /api/config` - Configurações
- `POST /api/config` - Salvar configurações
- `GET /api/patients` - Listar pacientes
- `POST /api/patients` - Criar paciente
- `GET /api/exams` - Listar exames
- `POST /api/exams` - Upload de exame
- `GET /api/reports` - Relatórios

## Logs e Monitoramento

No painel do Render você pode:
- Ver logs em tempo real
- Monitorar performance
- Configurar alertas
- Ver métricas de uso

## Atualizações

Para atualizar o sistema:
1. Faça push para o repositório GitHub
2. O Render fará deploy automático
3. Acompanhe os logs para verificar sucesso


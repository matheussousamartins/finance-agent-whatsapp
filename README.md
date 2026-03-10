# Finza — Agente Financeiro Pessoal via WhatsApp

Controle financeiro pessoal via WhatsApp com **Inteligência Artificial**. Registre gastos, entradas e comprovantes em linguagem natural — por texto, áudio ou foto. Sem planilhas, sem apps, sem fricção.

---

## Funcionalidades

- 💬 **Texto natural** — _"gastei 47 no mercado"_, _"recebi 3200 de salário"_
- 🎙️ **Áudio** — manda um áudio e o Whisper transcreve automaticamente
- 📸 **Foto de comprovante** — envia a foto e a IA extrai valor e categoria
- 📊 **Resumos inteligentes** — _"quanto gastei esse mês?"_, _"detalha meus gastos em alimentação"_
- 🏷️ **Categorização automática** — Alimentação, Transporte, Lazer, Saúde, etc.
- 👤 **Onboarding automático** — coleta nome e orçamento mensal na primeira conversa
- ⏳ **Trial de 7 dias** — novos usuários têm acesso gratuito por 7 dias
- 💳 **Sistema de planos** — Mensal, Trimestral e Semestral

---

## Arquitetura

```
WhatsApp → Z-API → FastAPI (Webhook)
                        ↓
                 [access_check]     ← verifica trial/plano
                        ↓
                  [onboarding]      ← coleta nome e orçamento
                        ↓
           ┌────────────┴──────────────┐
        texto                       imagem/áudio
           ↓                           ↓
      [classifier]            [image_extractor]
           ↓                  [audio → Whisper → texto]
   expense/income → [extractor] → [saver] → PostgreSQL
   query          → [query]              → Resumo
   unknown        → [fallback]           → Ajuda
                        ↓
                  Z-API → WhatsApp
```

---

## Stack

| Tecnologia | Uso |
|---|---|
| [LangGraph](https://langchain-ai.github.io/langgraph/) | Orquestração do agente |
| [LangChain](https://python.langchain.com/) | Framework LLM |
| [OpenAI GPT-4o](https://openai.com/) | Classificação, extração e visão (imagens) |
| [OpenAI Whisper](https://openai.com/) | Transcrição de áudio |
| [FastAPI](https://fastapi.tiangolo.com/) | Servidor web + webhook |
| [SQLAlchemy](https://www.sqlalchemy.org/) | ORM |
| [PostgreSQL](https://www.postgresql.org/) | Banco de dados |
| [Z-API](https://z-api.io/) | Integração WhatsApp |
| [Railway](https://railway.app/) | Deploy e hospedagem |
| [ffmpeg](https://ffmpeg.org/) | Conversão de áudio .ogg → .mp3 |

---

## Como rodar localmente

### Pré-requisitos
- Python 3.11+
- ffmpeg instalado (`brew install ffmpeg` no Mac, `apt install ffmpeg` no Linux)
- Conta na [OpenAI](https://platform.openai.com/)
- Conta na [Z-API](https://z-api.io/)
- PostgreSQL rodando localmente ou via Docker
- [ngrok](https://ngrok.com/) para expor o servidor local

### 1. Clone o repositório
```bash
git clone https://github.com/matheussousamartins/finance-agent-whatsapp.git
cd finance-agent-whatsapp
```

### 2. Crie o ambiente virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais:
```env
OPENAI_API_KEY=sk-...
ZAPI_INSTANCE_ID=...
ZAPI_TOKEN=...
ZAPI_CLIENT_TOKEN=...
DATABASE_URL=postgresql://user:password@localhost:5432/finza
```

### 5. Inicie o banco com Docker (opcional)
```bash
docker-compose up -d
```

### 6. Inicie o servidor
```bash
uvicorn app.main:app --reload
```

### 7. Exponha com ngrok
```bash
ngrok http 8000
```

### 8. Configure o webhook na Z-API
No painel da Z-API → **Webhooks e configurações gerais** → **Ao receber**:
```
https://seu-id.ngrok.io/webhook
```

---

## Deploy (Railway)

O projeto está configurado para deploy automático no Railway via `Dockerfile`.

### Variáveis de ambiente no Railway
```env
OPENAI_API_KEY=
ZAPI_INSTANCE_ID=
ZAPI_TOKEN=
ZAPI_CLIENT_TOKEN=
DATABASE_URL=
```

O `Dockerfile` já instala o `ffmpeg` automaticamente:
```dockerfile
RUN apt-get update && apt-get install -y ffmpeg
```

---

## Estrutura do projeto

```
finance-agent-whatsapp/
├── app/
│   ├── agent/
│   │   ├── graph.py        # Grafo LangGraph + FinanceAgent
│   │   ├── nodes.py        # Nós: access_check, onboarding, classifier,
│   │   │                   #      extractor, image_extractor, saver, query, fallback
│   │   ├── prompts.py      # Prompts do LLM (proprietário, não versionado)
│   │   └── state.py        # AgentState + MessageIntent
│   ├── models/
│   │   ├── transaction.py  # Model Transaction + TransactionType
│   │   └── user.py         # Model User + OnboardingStep + PlanStatus
│   ├── services/
│   │   ├── audio.py        # Download, conversão e transcrição de áudio
│   │   ├── database.py     # Operações no banco
│   │   └── zapi.py         # Integração Z-API
│   └── main.py             # FastAPI + webhook
├── tests/
│   └── test_agent.py       # 12 testes unitários
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── nixpacks.toml
├── requirements.txt
└── README.md
```

---

## Exemplos de uso

| Mensagem | Resposta do agente |
|---|---|
| "gastei 47 no mercado" | 💸 Gasto registrado! Alimentação · R$ 47,00 |
| "paguei 200 de luz" | 💸 Gasto registrado! Moradia · R$ 200,00 |
| "recebi 3200 de salário" | 💰 Entrada registrada! Salário · R$ 3.200,00 |
| 🎤 áudio: "gastei 40 na Netflix" | 💸 Gasto registrado! Lazer · R$ 40,00 |
| 📸 foto do cupom fiscal | 💸 Gasto registrado! (extração automática) |
| "quanto gastei esse mês?" | 📊 Resumo completo com saldo e categorias |
| "detalha meus gastos em alimentação" | 📋 Lista cada transação com data e valor |

---

## Testes

```bash
pytest tests/ -v
```

---

## Sistema de planos

| Plano | Valor | Duração |
|---|---|---|
| Trial | Grátis | 7 dias |
| Mensal | R$ 19,90 | 30 dias |
| Trimestral | R$ 49,90 | 90 dias |
| Semestral | R$ 89,90 | 180 dias |

---

## Notas

> `app/agent/prompts.py` é proprietário e não está versionado neste repositório.

---

## Licença

Proprietário — todos os direitos reservados. © 2026 Matheus Sousa Martins.
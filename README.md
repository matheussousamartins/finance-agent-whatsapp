# Finza — Agente Financeiro Pessoal via WhatsApp

🌐 **Produto ao vivo:** [finza-landing-zp.vercel.app](https://finza-landing-zp.vercel.app)

> Controle financeiro pessoal por linguagem natural no WhatsApp — sem planilhas, sem apps, sem fricção.

Finza é um agente de IA que permite registrar gastos, entradas e comprovantes financeiros diretamente pelo WhatsApp, por texto, áudio ou foto. Construído com LangGraph para orquestração de agentes, GPT-4o para compreensão de linguagem natural e visão computacional, e Whisper para transcrição de áudio.

---

## Demonstração

| Entrada | Resposta |
|---|---|
| `"gastei 47 no mercado"` | 💸 Gasto registrado · Alimentação · R$ 47,00 |
| `"recebi 3200 de salário"` | 💰 Entrada registrada · Salário · R$ 3.200,00 |
| 🎤 áudio: `"paguei 40 na Netflix"` | 💸 Gasto registrado · Lazer · R$ 40,00 |
| 📸 foto do cupom fiscal | 💸 Extração automática de valor e categoria |
| `"quanto gastei esse mês?"` | 📊 Resumo com saldo e breakdown por categoria |
| `"detalha meus gastos em alimentação"` | 📋 Lista cada transação com data e valor |

---

## Funcionalidades

- **Linguagem natural** — entende o jeito que o usuário fala, sem comandos rígidos
- **Mensagens de voz** — transcrição automática via OpenAI Whisper
- **Foto de comprovante** — extração de valor e categoria via GPT-4o Vision
- **Resumos inteligentes** — consultas livres sobre gastos, categorias e saldo
- **Categorização automática** — Alimentação, Transporte, Lazer, Saúde e mais
- **Onboarding conversacional** — coleta nome e orçamento mensal na primeira interação
- **Sistema de trial e planos** — 7 dias grátis, com planos Mensal, Trimestral e Semestral
- **Histórico por usuário** — cada número de WhatsApp tem seu próprio contexto financeiro

---

## Arquitetura

O agente é implementado como um grafo de estados com LangGraph, onde cada nó tem uma responsabilidade isolada:

```
WhatsApp → Z-API → FastAPI (Webhook)
                        ↓
                 [access_check]     ← valida trial / plano ativo
                        ↓
                  [onboarding]      ← coleta nome e orçamento (primeira vez)
                        ↓
           ┌────────────┴──────────────────┐
        texto                         imagem / áudio
           ↓                               ↓
      [classifier]               [image_extractor]
           ↓                     [audio → Whisper → texto → classifier]
   expense/income → [extractor] → [saver] → PostgreSQL
   query          → [query]              → Resumo financeiro
   unknown        → [fallback]           → Mensagem de ajuda
                        ↓
                  Z-API → WhatsApp
```

**Decisões de design:**
- Cada nó do grafo é uma função pura com entrada e saída tipadas via `AgentState` (Pydantic)
- O nó `access_check` atua como middleware — bloqueia o fluxo se o trial expirou ou o plano está inativo
- Áudios em `.ogg` são convertidos para `.mp3` via `ffmpeg` antes da transcrição
- O nó `query` passa as últimas 20 transações individuais ao LLM, permitindo detalhamento por categoria

---

## Stack

| Tecnologia | Papel |
|---|---|
| [LangGraph](https://langchain-ai.github.io/langgraph/) | Orquestração do agente como grafo de estados |
| [OpenAI GPT-4o](https://openai.com/) | Classificação, extração de entidades e visão computacional |
| [OpenAI Whisper](https://openai.com/) | Transcrição de mensagens de voz |
| [FastAPI](https://fastapi.tiangolo.com/) | Servidor web e recepção de webhooks |
| [SQLAlchemy](https://www.sqlalchemy.org/) | ORM com modelos `User` e `Transaction` |
| [PostgreSQL](https://www.postgresql.org/) | Banco de dados relacional em produção |
| [Z-API](https://z-api.io/) | Gateway de integração com WhatsApp |
| [Railway](https://railway.app/) | Deploy, hosting e banco gerenciado |
| [ffmpeg](https://ffmpeg.org/) | Conversão de áudio `.ogg` → `.mp3` |

---

## Estrutura do projeto

```
finance-agent-whatsapp/
├── app/
│   ├── agent/
│   │   ├── graph.py        # Grafo LangGraph + classe FinanceAgent
│   │   ├── nodes.py        # Nós: access_check, onboarding, classifier,
│   │   │                   #      extractor, image_extractor, saver, query, fallback
│   │   ├── prompts.py      # Prompts do LLM 
│   │   └── state.py        # AgentState (Pydantic) + enum MessageIntent
│   ├── models/
│   │   ├── transaction.py  # Model Transaction + enum TransactionType
│   │   └── user.py         # Model User + enums OnboardingStep e PlanStatus
│   ├── services/
│   │   ├── audio.py        # Download, conversão e transcrição de áudio
│   │   ├── database.py     # CRUD: usuários, transações e resumos
│   │   └── zapi.py         # Envio de mensagens via Z-API
│   └── main.py             # FastAPI + webhook POST /webhook
├── tests/
│   └── test_agent.py       # Testes unitários
├── .env.example
├── Dockerfile              # Inclui instalação do ffmpeg
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Como rodar localmente

**Pré-requisitos:** Python 3.11+, ffmpeg, PostgreSQL, conta OpenAI e conta Z-API.

```bash
# 1. Clone e entre no projeto
git clone https://github.com/matheussousamartins/finance-agent-whatsapp.git
cd finance-agent-whatsapp

# 2. Ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Dependências
pip install -r requirements.txt

# 4. Variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# 5. Banco de dados (opcional, via Docker)
docker-compose up -d

# 6. Servidor
uvicorn app.main:app --reload

# 7. Exponha com ngrok
ngrok http 8000
# Cole a URL gerada no painel da Z-API → Webhooks → Ao receber
```

**.env necessário:**
```env
OPENAI_API_KEY=sk-...
ZAPI_INSTANCE_ID=...
ZAPI_TOKEN=...
ZAPI_CLIENT_TOKEN=...
DATABASE_URL=postgresql://user:password@localhost:5432/finza
```

---

## Deploy

O projeto está configurado para deploy contínuo no **Railway** via `Dockerfile`. O `Dockerfile` instala o `ffmpeg` automaticamente — sem necessidade de configuração adicional.

```dockerfile
RUN apt-get update && apt-get install -y ffmpeg
```

As variáveis de ambiente são gerenciadas diretamente no painel do Railway. O banco PostgreSQL também é provisionado pelo Railway.

---

## Testes

```bash
pytest tests/ -v
```

---

## Sistema de planos

| Plano | Valor | Período |
|---|---|---|
| Trial | Grátis | 7 dias |
| Mensal | R$ 19,90 | 30 dias |
| Trimestral | R$ 49,90 | 90 dias |
| Semestral | R$ 89,90 | 180 dias |

---

## Licença

Proprietário — todos os direitos reservados. © 2026 Matheus Sousa Martins.
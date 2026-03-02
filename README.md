# Finance Agent WhatsApp

Agente financeiro pessoal via WhatsApp construído com **LangGraph**, **FastAPI** e **Z-API**.

Envie mensagens em linguagem natural pelo WhatsApp para registrar gastos, entradas e consultar seu resumo financeiro — sem formulários, sem apps, sem fricção.

---

## Funcionalidades

- 💸 Registrar gastos: _"gastei 45 no ifood"_
- 💰 Registrar entradas: _"recebi 3200 de salário"_
- 📊 Consultar resumo: _"quanto gastei esse mês?"_
- 🏷️ Categorização automática por IA
- 👤 Histórico individual por número de WhatsApp

---

## Arquitetura

```
WhatsApp → Z-API → FastAPI (Webhook)
                        ↓
                  LangGraph Agent
                        ↓
          ┌─────────────┴─────────────┐
    [Classifier]                      │
          ↓                           │
    expense/income → [Extractor] → [Saver] → SQLite/PostgreSQL
    query          → [Query Node] → Resumo financeiro
    unknown        → [Fallback]   → Mensagem de ajuda
                        ↓
                  Z-API → WhatsApp
```

---

## Stack

| Tecnologia | Uso |
|---|---|
| [LangGraph](https://langchain-ai.github.io/langgraph/) | Orquestração do agente |
| [LangChain](https://python.langchain.com/) | Framework LLM |
| [OpenAI GPT-4o](https://openai.com/) | Classificação e extração |
| [FastAPI](https://fastapi.tiangolo.com/) | Servidor web + webhook |
| [SQLAlchemy](https://www.sqlalchemy.org/) | ORM + banco de dados |
| [Z-API](https://z-api.io/) | Integração WhatsApp |

---

## Como rodar localmente

### Pré-requisitos
- Python 3.11+
- Conta na [OpenAI](https://platform.openai.com/)
- Conta na [Z-API](https://z-api.io/)
- [ngrok](https://ngrok.com/) para expor o servidor local

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/finance-agent-whatsapp.git
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
DATABASE_URL=sqlite:///./finza.db
```

### 5. Inicie o servidor
```bash
uvicorn app.main:app --reload
```

### 6. Exponha com ngrok
```bash
ngrok http 8000
```

### 7. Configure o webhook na Z-API
No painel da Z-API → **Webhooks e configurações gerais** → **Ao receber**:
```
https://seu-id.ngrok.io/webhook
```

---

## Testes

```bash
pytest tests/ -v
```

---

## Estrutura do projeto

```
finance-agent-whatsapp/
├── app/
│   ├── agent/
│   │   ├── graph.py       # Grafo LangGraph
│   │   ├── nodes.py       # Nós do agente
│   │   ├── prompts.py     # Prompts do LLM
│   │   └── state.py       # Estado do grafo
│   ├── models/
│   │   └── transaction.py # Model do banco
│   ├── services/
│   │   ├── database.py    # Operações no banco
│   │   └── zapi.py        # Integração Z-API
│   └── main.py            # FastAPI + webhook
├── tests/
│   └── test_agent.py      # Testes unitários
├── .env.example
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Exemplos de uso

| Mensagem | Resposta do agente |
|---|---|
| "gastei 45 no ifood" | 💸 Gasto registrado! Alimentação · R$45,00 |
| "paguei 200 de luz" | 💸 Gasto registrado! Moradia · R$200,00 |
| "recebi 3200 de salário" | 💰 Entrada registrada! Salário · R$3.200,00 |
| "quanto gastei esse mês?" | 📊 Resumo completo com saldo e categorias |
| "to no vermelho?" | 📊 Análise do saldo atual |
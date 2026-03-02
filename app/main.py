from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
import logging

from app.services.zapi import ZAPIService
from app.services.database import init_db
from app.agent.graph import FinanceAgent

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Finance Agent WhatsApp",
    description="Agente financeiro pessoal via WhatsApp",
    version="1.0.0",
)

zapi = ZAPIService()
agent = FinanceAgent()


@app.on_event("startup")
async def startup():
    init_db()
    logger.info("Banco de dados inicializado")
    logger.info("Finance Agent WhatsApp rodando!")


@app.get("/")
async def root():
    return {"status": "ok", "message": "Finance Agent WhatsApp is running 💰"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/webhook")
async def webhook(request: Request):
    try:
        payload = await request.json()
        logger.info(f"Webhook recebido: {payload}")

        if payload.get("fromMe"):
            return {"status": "ignored"}

        phone = payload.get("phone")
        message_data = payload.get("text", {})
        message = message_data.get("message", "")

        if not phone or not message:
            return {"status": "ignored"}

        logger.info(f"Mensagem de {phone}: {message}")

        response = await agent.process(phone=phone, message=message)
        await zapi.send_text(phone=phone, message=response)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

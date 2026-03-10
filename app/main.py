from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
import logging
import os

from app.services.zapi import ZAPIService
from app.services.database import init_db, engine
from app.services.audio import process_audio
from app.agent.graph import FinanceAgent

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN", "")

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
    logger.info("✅ Banco de dados inicializado")
    logger.info("🚀 Finance Agent WhatsApp rodando!")


@app.get("/")
async def root():
    return {"status": "ok", "message": "Finance Agent WhatsApp is running 💰"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/webhook")
async def webhook(request: Request):
    phone = None
    try:
        payload = await request.json()

        logger.info(f"📩 Webhook recebido: {payload}")

        if payload.get("fromMe"):
            return {"status": "ignored"}

        phone = payload.get("phone")
        if not phone:
            return {"status": "ignored"}

        image_data = payload.get("image")
        audio_data = payload.get("audio")
        message_data = payload.get("text", {})
        message = message_data.get("message", "")

        if image_data:
            # Usuário mandou foto
            image_url = image_data.get("imageUrl", "") or image_data.get("url", "")
            caption = image_data.get("caption", "")
            logger.info(f"🖼️ Imagem recebida de {phone}: {image_url}")

            if not image_url:
                return {"status": "ignored"}

            response = await agent.process_image(
                phone=phone,
                image_url=image_url,
                caption=caption,
            )

        elif audio_data:
            # Usuário mandou áudio
            audio_url = audio_data.get("audioUrl", "") or audio_data.get("url", "")
            logger.info(f"🎙️ Áudio recebido de {phone}: {audio_url}")

            if not audio_url:
                return {"status": "ignored"}

            # Transcreve o áudio para texto
            transcribed_text = await process_audio(audio_url)

            if not transcribed_text:
                await zapi.send_text(
                    phone=phone,
                    message="Não consegui entender o áudio 😅 Tente novamente ou manda por texto!"
                )
                return {"status": "ok"}

            logger.info(f"📝 Áudio transcrito: {transcribed_text}")

            # Processa o texto transcrito normalmente
            response = await agent.process(phone=phone, message=transcribed_text)

        elif message:
            # Usuário mandou texto
            logger.info(f"📱 Mensagem de {phone}: {message}")
            response = await agent.process(phone=phone, message=message)

        else:
            return {"status": "ignored"}

        await zapi.send_text(phone=phone, message=response)
        return {"status": "ok"}

    except Exception as e:
        logger.error(f"❌ Erro no webhook: {e}")
        try:
            if phone:
                await zapi.send_text(
                    phone=phone,
                    message="Ops! 😅 Tive uma instabilidade aqui. Tente novamente em instantes 🙏"
                )
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))
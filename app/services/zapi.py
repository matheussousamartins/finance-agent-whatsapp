import httpx
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ZAPI_INSTANCE_ID = os.getenv("ZAPI_INSTANCE_ID")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN")

BASE_URL = f"https://api.z-api.io/instances/{ZAPI_INSTANCE_ID}/token/{ZAPI_TOKEN}"


class ZAPIService:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "Client-Token": ZAPI_CLIENT_TOKEN,
        }

    async def send_text(self, phone: str, message: str) -> bool:
        """Envia uma mensagem de texto via Z-API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url=f"{self.base_url}/send-text",
                    headers=self.headers,
                    json={"phone": phone, "message": message},
                )
                response.raise_for_status()
                logger.info(f"Mensagem enviada para {phone}")
                return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP ao enviar mensagem: {e.response.status_code} - {e.response.text}")
            return False

        except Exception as e:
            logger.error(f"Erro inesperado ao enviar mensagem: {e}")
            return False
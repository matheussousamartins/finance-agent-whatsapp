import os
import logging
import tempfile
import subprocess
import aiohttp
from openai import OpenAI

logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def download_audio(url: str) -> bytes:
    """Baixa o arquivo de áudio da URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception(f"Erro ao baixar áudio: {response.status}")
            return await response.read()


def convert_ogg_to_mp3(ogg_bytes: bytes) -> bytes:
    """Converte áudio .ogg/opus para .mp3 usando ffmpeg."""
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as ogg_file:
        ogg_file.write(ogg_bytes)
        ogg_path = ogg_file.name

    mp3_path = ogg_path.replace(".ogg", ".mp3")

    try:
        subprocess.run(
            ["ffmpeg", "-i", ogg_path, "-ar", "16000", "-ac", "1", "-b:a", "64k", mp3_path, "-y"],
            check=True,
            capture_output=True,
        )
        with open(mp3_path, "rb") as mp3_file:
            return mp3_file.read()
    finally:
        os.unlink(ogg_path)
        if os.path.exists(mp3_path):
            os.unlink(mp3_path)


def transcribe_audio(mp3_bytes: bytes) -> str:
    """Transcreve o áudio usando Whisper da OpenAI."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(mp3_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pt",
            )
        logger.info(f"🎙️ Transcrição: {transcription.text}")
        return transcription.text
    finally:
        os.unlink(tmp_path)


async def process_audio(url: str) -> str:
    """Pipeline completo: baixa → converte → transcreve."""
    logger.info(f"🎙️ Processando áudio: {url}")
    ogg_bytes = await download_audio(url)
    mp3_bytes = convert_ogg_to_mp3(ogg_bytes)
    return transcribe_audio(mp3_bytes)
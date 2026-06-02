"""Entrega das mensagens (e futuramente imagens) via Telegram Bot API."""
import time

import requests

from src import config

HEADER_TELEGRAM = "<blockquote>Resumidor Guilherme:</blockquote>\n"
LIMITE_BLOCO = 4096 - len(HEADER_TELEGRAM)


def dividir_em_blocos(texto: str, limite: int = 4096):
    if len(texto) <= limite:
        return [texto]

    blocos = []
    bloco_atual = ""
    for linha in texto.split("\n"):
        candidato = bloco_atual + "\n" + linha if bloco_atual else linha
        if len(candidato) <= limite:
            bloco_atual = candidato
        else:
            if bloco_atual:
                blocos.append(bloco_atual)
            # se a linha sozinha for maior que o limite, corta no limite
            while len(linha) > limite:
                blocos.append(linha[:limite])
                linha = linha[limite:]
            bloco_atual = linha

    if bloco_atual:
        blocos.append(bloco_atual)
    return blocos


def enviar_telegram(mensagem: str):
    mensagem_limpa = mensagem.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    mensagem_limpa = mensagem_limpa.replace("<p>", "").replace("</p>", "\n")

    partes = mensagem_limpa.split("---SECAO---")
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"

    for parte in partes:
        texto_final = parte.strip()
        if not texto_final:
            continue

        for bloco in dividir_em_blocos(texto_final, limite=LIMITE_BLOCO):
            payload = {
                "chat_id": config.CHAT_ID,
                "text": HEADER_TELEGRAM + bloco,
                "parse_mode": "HTML",
            }
            response = requests.post(url, json=payload)
            if response.status_code != 200:
                print(f"❌ Erro ao enviar parte: {response.text}")
                print(f"Trecho com erro: {bloco[:50]}...")
            time.sleep(1)


def enviar_foto(imagem, legenda: str = ""):
    """Envia uma imagem (BytesIO/bytes) ao Telegram via sendPhoto."""
    if imagem is None:
        return
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendPhoto"
    files = {"photo": ("grafico.png", imagem, "image/png")}
    data = {"chat_id": config.CHAT_ID, "caption": legenda[:1024]}
    response = requests.post(url, data=data, files=files)
    if response.status_code != 200:
        print(f"❌ Erro ao enviar foto: {response.text}")
    time.sleep(1)

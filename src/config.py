"""Configuração central: variáveis de ambiente, credenciais e fontes de notícias."""
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_KEY")
GROQ_KEY = os.getenv("GROQ_KEY")


def _normalizar_credenciais_telegram():
    """Retorna (token_do_bot, chat_id) de forma robusta à ordem das variáveis.

    O token de bot do Telegram tem o formato "<dígitos>:<hash>" (contém ':'),
    enquanto o chat_id é apenas numérico. No .env atual as variáveis aparecem
    trocadas; aqui detectamos qual é qual em vez de confiar na posição.
    """
    a = (os.getenv("TELEGRAM_TOKEN") or "").strip().strip('"')
    b = (os.getenv("CHAT_ID") or "").strip().strip('"')

    def parece_token(valor: str) -> bool:
        return ":" in valor

    if parece_token(b) and not parece_token(a):
        # Estavam trocados: o token estava em CHAT_ID.
        return b, a
    # Caso normal (ou ambíguo): usa como veio.
    return a, b


TELEGRAM_TOKEN, CHAT_ID = _normalizar_credenciais_telegram()

# Fontes de RSS usadas para coletar notícias do dia.
FONTES_RSS = [
    # Mercados e finanças Brasil
    "https://www.infomoney.com.br/feed/",
    "https://www.moneytimes.com.br/feed/",
    "https://valor.globo.com/rss/financas/",       # macro BR: câmbio, juros, Selic, Tesouro
    "https://www.poder360.com.br/economia/feed/",

    # Cenário global
    "https://valor.globo.com/rss/mundo/",           # mundo: EUA, China, geopolítica
    "https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml",  # governo/política BR

    # Agro
    "https://www.canalrural.com.br/feed/",
    "https://revistagloborural.globo.com/rss.xml",

    # Tecnologia
    "https://tecnoblog.net/feed/",
    "https://canaltech.com.br/rss/",
    "https://exame.com/tecnologia/feed/",
    "https://valor.globo.com/rss/tecnologia/",
]

import feedparser
import requests
from google import genai
from groq import Groq
import os
import time
from dotenv import load_dotenv
from leitor_wallet import extrair_carteira

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_KEY")
GROQ_KEY = os.getenv("GROQ_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

gemini_client = genai.Client(api_key=GEMINI_KEY, http_options={'api_version': 'v1'})
groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

def ler_carteira():
    carteira = os.getenv("CARTEIRA")

    if carteira :
        print("Carteira Lida pelo secrets!")
        return carteira
        
    else :
        carteira = extrair_carteira("wallet.pdf")
        print("Carteira Lida Localmente!")
        return carteira
      

def buscar_noticias(resumo_curto=False):
    fontes = [
        # Mercados e finanças Brasil
        "https://www.infomoney.com.br/feed/",
        "https://www.moneytimes.com.br/feed/",
        "https://valor.globo.com/rss/financas/",       # macro BR: câmbio, juros, Selic, Tesouro
        "https://www.poder360.com.br/economia/feed/",

        # Cenário global (gap anterior)
        "https://valor.globo.com/rss/mundo/",           # mundo: EUA, China, geopolítica
        "https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml",  # governo/política BR

        # Agro (gap anterior — antes só Canal Rural)
        "https://www.canalrural.com.br/feed/",
        "https://revistagloborural.globo.com/rss.xml",

        # Tecnologia
        "https://tecnoblog.net/feed/",
        "https://canaltech.com.br/rss/",
        "https://exame.com/tecnologia/feed/",
        "https://valor.globo.com/rss/tecnologia/",
    ]
    texto = ""
    for url in fontes:
        feed = feedparser.parse(url)
        for e in feed.entries[:5]:
            if resumo_curto:
                summary = (e.summary[:200] + "...") if len(e.summary) > 200 else e.summary
            else:
                summary = e.summary
            texto += f"Título: {e.title}\nResumo: {summary}\n\n"
    return texto

def _build_prompt(noticias, texto_carteira):
    return f"""
Você é um Analista de Investimentos Sênior. Gere um "Morning Call" completo e detalhado.

ANTES DE TUDO: Escreva em uma linha qual modelo de IA você está usando (ex: "Eu estou utilizando um modelo de linguagem avançado treinado pelo Google."). Depois escreva uma introdução de 2-3 frases dando as boas-vindas ao Morning Call do dia, com a data de hoje e panorama geral do cenário.

1. Notícias do momento: {noticias}
2. Minha carteira: {texto_carteira}

IMPORTANTE: Use o separador "---SECAO---" entre cada tópico.

### ESTRUTURA:
1. 🌎 <b>Cenário Global</b>: Notícias geopolíticas e econômicas de maior impacto global.
---SECAO---
2. 🇧🇷 <b>Cenário Nacional</b>: Política fiscal, juros, Brasília e economia doméstica.
---SECAO---
3. 🏢 <b>Empresas</b>: Fusões, balanços, fatos relevantes e recomendações de analistas.
---SECAO---
4. 🚜 <b>Radar Agro</b>: Commodities agrícolas, preços e clima.
---SECAO---
5. 💻 <b>Tecnologia e Inovação</b>: IA, Big Techs, semicondutores e startups. Máximo 4 itens, os de maior impacto.
---SECAO---
6. 💼 <b>Análise de Carteira</b>: Posicionamento atual, impacto das notícias do dia nos ativos e recomendações práticas. LIMITE ESTRITO: 4000 caracteres.
---SECAO---
7. 📊 <b>Bolsa e Sentimento</b>: Abertura/fechamento dos índices e "clima" geral do mercado.

### FORMATO DE CADA SEÇÃO:
Comece com o título da seção em negrito (ex: 🌎 <b>Cenário Global</b>) seguido de uma frase de contexto.
Para cada notícia/ponto, use exatamente este formato:
•   <b>Título do Ponto</b>: Descrição detalhada do evento ou dado. <b>Impacto:</b> Análise de como isso afeta o mercado ou os investimentos.

### REGRAS:
- CRÍTICO: Cada seção deve ter no máximo 4000 caracteres.
- Use tags HTML <b> e <i> para formatação. NUNCA use markdown (**, __, ##, *, -, etc.).
- Use • (bullet U+2022) para listas, nunca asterisco ou traço como bullet.
- Nunca use <br> ou <p>.
- NUNCA escreva "Não há notícias relevantes". Se uma área estiver calma, comente brevemente o cenário do dia.
- Inclua análise de impacto para cada ponto. Seja analítico como um profissional real.
"""

def gerar_resumo(noticias, texto_carteira):
    prompt = _build_prompt(noticias, texto_carteira)

    gemini_models = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-lite"]

    for model in gemini_models:
        try:
            response = gemini_client.models.generate_content(model=model, contents=prompt)
            print(f"Modelo utilizado: {model}")
            return response.text
        except Exception as e:
            print(f"Erro {e} no modelo:{model}")

    if groq_client:
        # Groq free tier tem limite de tokens por minuto (~6k TPM)
        # Busca versão compacta das notícias (summary limitado a 200 chars por artigo)
        noticias_curtas = buscar_noticias(resumo_curto=True)
        carteira_curta = texto_carteira[:2000]
        prompt_groq = _build_prompt(noticias_curtas, carteira_curta)

        groq_models = ["llama-3.3-70b-versatile", "gemma2-9b-it", "llama-3.1-8b-instant"]
        for model in groq_models:
            try:
                response = groq_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt_groq}],
                    max_tokens=4096
                )
                print(f"Modelo Groq utilizado: {model}")
                return response.choices[0].message.content
            except Exception as e:
                print(f"Erro Groq {e} no modelo:{model}")

    raise RuntimeError("Todos os modelos falharam. Verifique suas cotas e API keys.")

def dividir_em_blocos(texto, limite=4096):
    if len(texto) <= limite:
        return [texto]

    blocos = []
    linhas = texto.split("\n")
    bloco_atual = ""

    for linha in linhas:
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

HEADER_TELEGRAM = "<blockquote>Resumidor Guilherme:</blockquote>\n"
LIMITE_BLOCO = 4096 - len(HEADER_TELEGRAM)

def enviar_telegram(mensagem):
    mensagem_limpa = mensagem.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    mensagem_limpa = mensagem_limpa.replace("<p>", "").replace("</p>", "\n")

    partes = mensagem_limpa.split("---SECAO---")

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    for parte in partes:
        texto_final = parte.strip()
        if not texto_final:
            continue

        for bloco in dividir_em_blocos(texto_final, limite=LIMITE_BLOCO):
            payload = {
                "chat_id": CHAT_ID,
                "text": HEADER_TELEGRAM + bloco,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload)

            if response.status_code != 200:
                print(f"❌ Erro ao enviar parte: {response.text}")
                print(f"Trecho com erro: {bloco[:50]}...")

            time.sleep(1)

if __name__ == "__main__":
    try:
        print("🚀 Iniciando Morning Call...")
        raw_news = buscar_noticias()
        texto_carteira = ler_carteira()
        
        print("🤖 Inteligência Artificial processando...")
        resumo_completo = gerar_resumo(raw_news,texto_carteira)
        
        print("📲 Enviando blocos para o Telegram...")
        enviar_telegram(resumo_completo)
        
        print("✅ Tudo pronto!")
            
    except Exception as e:
        print(f"\n❌ OCORREU UM ERRO:\n{e}")

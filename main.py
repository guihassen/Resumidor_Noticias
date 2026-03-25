import feedparser
import requests
from google import genai
import os
import time

GEMINI_KEY = os.getenv("GEMINI_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

client = genai.Client(api_key=GEMINI_KEY, http_options={'api_version': 'v1'})

def buscar_noticias():
    fontes = [
        "https://www.infomoney.com.br/feed/",
        "https://www.moneytimes.com.br/feed/",
        "https://www.canalrural.com.br/feed/",
        "https://www.poder360.com.br/economia/feed/",
    ]
    texto = ""
    for url in fontes:
        feed = feedparser.parse(url)
        for e in feed.entries[:8]: # Aumentei para 8 notícias por fonte
            texto += f"Título: {e.title}\nResumo: {e.summary}\n\n"
    return texto

def gerar_resumo(noticias):
    prompt = f"""
Você é um Analista de Investimentos Sênior. Gere um "Morning Call" completo.
IMPORTANTE: Use o separador "---SECAO---" entre cada tópico.

### ESTRUTURA:
1. 🌎 **Cenário Global**: Foque em Fed, China e indicadores EUA.
---SECAO---
2. 🇧🇷 **Cenário Nacional**: Foque em política fiscal, juros e Brasília.
---SECAO---
3. 🏢 **Empresas**: Fusões, balanços e fatos relevantes.
---SECAO---
4. 🚜 **Radar Agro**: Commodities e clima.
---SECAO---
5. 📊 **Bolsa e Sentimento**: Fechamento/Abertura e o "clima" do mercado.

### REGRAS:
- Explique o impacto de cada notícia (ex: "Isso pode pressionar o dólar").
- Use apenas as tags HTML <b> e <i>.
- Nunca use <br> ou <p>.
- Faça a separação das noticias por tópicos para ficar mais facil de ler, busque facilitar a leitura o máximo e torna-la o mais dinamico possivel

Notícias: {noticias}
"""
    # Usando o modelo estável 2.5-flash
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text

def enviar_telegram(mensagem):
    # Quebra o texto em várias mensagens usando o separador que definimos
    partes = mensagem.split("---SECAO---")
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    for parte in partes:
        if parte.strip(): # Só envia se não estiver vazio
            payload = {
                "chat_id": CHAT_ID,
                "text": parte.strip(),
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload)
            
            if response.status_code != 200:
                print(f"❌ Erro ao enviar parte: {response.text}")
            
            # Pequena pausa para o Telegram não bloquear por excesso de velocidade
            time.sleep(1)

if __name__ == "__main__":
    try:
        print("🚀 Iniciando Morning Call...")
        raw_news = buscar_noticias()
        
        print("🤖 Inteligência Artificial processando...")
        resumo_completo = gerar_resumo(raw_news)
        
        print("📲 Enviando blocos para o Telegram...")
        enviar_telegram(resumo_completo)
        
        print("✅ Tudo pronto!")
            
    except Exception as e:
        print(f"\n❌ OCORREU UM ERRO:\n{e}")

import feedparser
import requests
from google import genai
import os

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
        for e in feed.entries:
            texto += f"Título: {e.title}\nResumo: {e.summary}\n\n"
    return texto

def gerar_resumo(noticias):
    prompt = f"""
    Você é um Analista de Investimentos Sênior e meu Assistente Financeiro Pessoal. 
Sua missão é processar as notícias abaixo e gerar um "Morning Call" para o Telegram.

### REQUISITOS DE CONTEÚDO:
1. SELEÇÃO: Escolha as 3 notícias mais impactantes para cada uma dos setores a seguir e para cada um dos setores priorize: 
   - Cenário Nacional: Impactos no mercado brasileiro, política fiscal e juros.
   - Cenário Global: Fed, economia chinesa e indicadores dos EUA.
   - Movimentações Corporativas: Balanços, fusões e fatos relevantes.
   - Bolsa de Valores : Noticias que me informem se a bolsa esta subindo ou descendo, noticias de abertura do pregão ou finalização.
   - Radar Agro : Commodities, Tempo, Safra,etc.
   
2. CONTEXTUALIZAÇÃO: Para cada notícia, explique brevemente o "PORQUÊ" (causa) e o "IMPACTO" (consequência para bolsa/dólar).
### REQUISITOS DE FORMATAÇÃO (ESTRITO PARA TELEGRAM):
- Divida em 4 seções claras: 
   1. 🌎 Cenário Global
   2. 🇧🇷 Cenário Nacional
   3. 🏢 Movimentações Empresariais
   4. 🗽 Bolsa de Valores
   4. 🚜 Radar Agro
   
- Finalize com: Sentimento do Mercado: [Otimista/Cauteloso/Pessimista].
- Essas 4 seções devem possuir as subseções separadas por cada uma das noticias

### RESTRIÇÕES TÉCNICAS:
- Resposta total deve ter no MÁXIMO 4.000 caracteres, então não ultrapasse esse limite! 
- Seja extremamente objetivo na sua resposta, não deixe que o limite de caracteres seja ultrapassado
- Mantenha sua atenção apenas nas noticias que você julgar importante!
- Se não houver notícia relevante para uma seção, apenas coloque "Nada relevante nessa seção".

Notícias: {noticias}
"""

    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML" 
    }
    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print(f"\n❌ ERRO NA API DO TELEGRAM:")
        print(f"Status: {response.status_code}")
        print(f"Resposta: {response.text}")
    
    return response.status_code

if __name__ == "__main__":
    try:
        print("Processando notícias...")
        raw_news = buscar_noticias()
        
        print("Gerando resumo...")
        resumo = gerar_resumo(raw_news)
        
        print("Enviando para o Telegram...")
        status = enviar_telegram(resumo)
        
        if status == 200:
            print("Concluído com sucesso!")
        else:
            print(f"Erro ao enviar para o Telegram. Status: {status}")
            
    except Exception as e:
        print(f"\n❌ OCORREU UM ERRO:\n{e}")

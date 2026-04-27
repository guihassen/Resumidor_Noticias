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
      

def buscar_noticias():
    fontes = [
        "https://www.infomoney.com.br/feed/",
        "https://www.moneytimes.com.br/feed/",
        "https://www.canalrural.com.br/feed/",
        "https://www.poder360.com.br/economia/feed/",
        "https://tecnoblog.net/feed/",
        "https://canaltech.com.br/rss/",
        "https://exame.com/tecnologia/feed/",
        "https://valor.globo.com/rss/tecnologia/"
    ]
    texto = ""
    for url in fontes:
        feed = feedparser.parse(url)
        for e in feed.entries[:5]: 
            texto += f"Título: {e.title}\nResumo: {e.summary}\n\n"
    return texto

def gerar_resumo(noticias, texto_carteira):
    prompt = f"""
Eu quero que a primeira mensagem antes de qualquer coisa seja o modelo que você está utilizando!
Você é um Analista de Investimentos Sênior. Gere um "Morning Call" completo.

1. As noticias do momento : {noticias}
2. Considere minha carteira: {texto_carteira}

IMPORTANTE: Use o separador "---SECAO---" entre cada tópico.

### ESTRUTURA:
1. 🌎 **Cenário Global**: Foque em Noticias impactantes em escala global, nessa seção quero as noticias geopolíticas e economicas mais importantes do cenario global.
---SECAO---
2. 🇧🇷 **Cenário Nacional**: Foque em política fiscal, juros e Brasília.
---SECAO---
3. 🏢 **Empresas**: Fusões, balanços e fatos relevantes.
---SECAO---
4. 🚜 **Radar Agro**: Commodities e clima.
---SECAO---
5. 💻 **Tecnologia e Inovação**: IA, Big Techs, semicondutores e startups. Pegue somente as noticias mais importantes, aquelas com mais impacto. No Máximo 4 para não ultrapassar o limite de 4096 carácteres.
---SECAO---
6. 💼 ** Análise de Carteira ** : Análise minha carteira, Me diga como estou posicionado no dia, me diga como as noticias podem afetar minha carteira e possíveis recomendações. LIMITE ESTRITO: esta seção deve ter no máximo 4000 caracteres. Seja objetivo e direto.
---SECAO---
7. 📊 **Bolsa e Sentimento**: Fechamento/Abertura e o "clima" do mercado.

### REGRAS:
- CRÍTICO: Cada seção separada por "---SECAO---" deve ter no máximo 4000 caracteres. O Telegram rejeita mensagens maiores. Ajuste o tamanho do texto de cada seção para respeitar esse limite.
- Para tecnologia: Explique como a tecnologia pode afetar o mercado (ex: "Alta da Nvidia puxa Nasdaq") e também foque em novas tecnologias, notícias impactantes e tendências do mercado.
- Explique o impacto de cada notícia (ex: "Isso pode pressionar o dólar").
- Use apenas as tags HTML <b> e <i>.
- Nunca use <br> ou <p>.
- Faça a separação das notícias por tópicos para ficar mais fácil de ler, busque facilitar a leitura o máximo e torná-la o mais dinâmica possível.


"""
    gemini_models = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-lite"]

    for model in gemini_models:
        try:
            response = gemini_client.models.generate_content(model=model, contents=prompt)
            print(f"Modelo utilizado: {model}")
            return response.text
        except Exception as e:
            print(f"Erro {e} no modelo:{model}")

    if groq_client:
        groq_models = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "llama-3.1-8b-instant"]
        for model in groq_models:
            try:
                response = groq_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4096
                )
                print(f"Modelo Groq utilizado: {model}")
                return response.choices[0].message.content
            except Exception as e:
                print(f"Erro Groq {e} no modelo:{model}")

    raise RuntimeError("Todos os modelos falharam. Verifique suas cotas e API keys.")

def enviar_telegram(mensagem):
    # 1. LIMPEZA GLOBAL: Remove as tags problemáticas que o Gemini insere (br, p, div)
    # Trocamos <br> por quebra de linha real (\n) e removemos o resto
    mensagem_limpa = mensagem.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    mensagem_limpa = mensagem_limpa.replace("<p>", "").replace("</p>", "\n")
    
    # 2. Quebra o texto em várias mensagens usando o separador
    partes = mensagem_limpa.split("---SECAO---")
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    for parte in partes:
        texto_final = parte.strip()
        if texto_final: 
            payload = {
                "chat_id": CHAT_ID,
                "text": texto_final,
                "parse_mode": "HTML"
            }
            response = requests.post(url, json=payload)
            
            if response.status_code != 200:
                print(f"❌ Erro ao enviar parte: {response.text}")
                # Log extra para você ver qual texto causou o erro:
                print(f"Trecho com erro: {texto_final[:50]}...") 
            
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

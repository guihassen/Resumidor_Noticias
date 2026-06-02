"""Geração do Morning Call com fallback entre modelos Gemini e Groq."""
from src.analysis.prompt import build_prompt
from src.clients import get_gemini, get_groq
from src.news.feeds import buscar_noticias

# 2.5-flash primeiro: o free tier do 2.0-flash foi zerado (limit: 0) para esta chave.
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash", "gemini-2.5-pro"]
GROQ_MODELS = ["llama-3.3-70b-versatile", "gemma2-9b-it", "llama-3.1-8b-instant"]


def gerar_resumo(
    noticias: str,
    texto_carteira: str,
    noticias_relevantes: str = "",
    projecoes: str = "",
) -> str:
    prompt = build_prompt(noticias, texto_carteira, noticias_relevantes, projecoes)
    client = get_gemini()

    for model in GEMINI_MODELS:
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            print(f"Modelo utilizado: {model}")
            return response.text
        except Exception as e:
            print(f"Erro {e} no modelo: {model}")

    groq_client = get_groq()
    if groq_client:
        # Groq free tier tem limite de tokens por minuto (~6k TPM):
        # usa versão compacta das notícias e da carteira.
        noticias_curtas = buscar_noticias(resumo_curto=True)
        carteira_curta = texto_carteira[:2000]
        prompt_groq = build_prompt(noticias_curtas, carteira_curta)

        for model in GROQ_MODELS:
            try:
                response = groq_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt_groq}],
                    max_tokens=4096,
                )
                print(f"Modelo Groq utilizado: {model}")
                return response.choices[0].message.content
            except Exception as e:
                print(f"Erro Groq {e} no modelo: {model}")

    raise RuntimeError("Todos os modelos falharam. Verifique suas cotas e API keys.")

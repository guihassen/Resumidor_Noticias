"""Orquestrador do Morning Call."""
from src.analysis import llm
from src.db import repo
from src.delivery import telegram
from src.market import bcb, quotes
from src.news import feeds, relevance, scraper
from src.wallet import parser


def _formatar_relevantes(relevantes) -> str:
    blocos = []
    for e in relevantes:
        ativos = ", ".join(e.get("ativos", []))
        blocos.append(
            f"[{ativos}] {e['titulo']} ({e.get('fonte', '')})\n{e.get('texto_completo', '')}"
        )
    return "\n\n".join(blocos)


def run():
    print("🚀 Iniciando Morning Call...")

    entradas = feeds.coletar_entradas()
    entradas = repo.filtrar_noticias_novas(entradas)  # dedupe (no-op sem DATABASE_URL)
    raw_news = feeds.formatar_entradas(entradas)

    print("🔮 Buscando projeções do Focus/Bacen...")
    projecoes = bcb.formatar_para_prompt(bcb.obter_projecoes())
    dolar = quotes.cambio_atual()
    if dolar:
        projecoes += f"\nCÂMBIO ATUAL (USD/BRL): R$ {dolar}"

    texto_carteira = parser.ler_carteira_texto()
    carteira = parser.estruturar_carteira(texto_carteira)
    holdings = carteira.get("holdings", [])

    noticias_relevantes = ""
    if holdings:
        print("📰 Filtrando notícias ligadas à carteira e extraindo texto completo...")
        relevantes = relevance.filtrar_relevantes(entradas, holdings, limite=8)
        relevantes = scraper.enriquecer(relevantes, limite=8)
        noticias_relevantes = _formatar_relevantes(relevantes)

    print("🤖 Inteligência Artificial processando...")
    resumo_completo = llm.gerar_resumo(raw_news, noticias_relevantes, projecoes)

    print("📲 Enviando blocos para o Telegram...")
    telegram.enviar_telegram(resumo_completo)

    print("✅ Tudo pronto!")


def run_resumo_dia():
    print("🌙 Gerando Resumo do Dia...")

    entradas = feeds.coletar_entradas(por_fonte=15)
    raw_news = feeds.formatar_entradas(entradas)

    print("🤖 Inteligência Artificial processando...")
    resumo = llm.gerar_resumo_dia(raw_news)

    print("📲 Enviando Resumo do Dia para o Telegram...")
    telegram.enviar_telegram(resumo)

    print("✅ Resumo do Dia enviado!")


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"\n❌ OCORREU UM ERRO:\n{e}")

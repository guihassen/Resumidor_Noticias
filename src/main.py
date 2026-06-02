"""Orquestrador do Morning Call."""
from src.analysis import llm, metrics
from src.charts import render
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
    raw_news = feeds.formatar_entradas(entradas)

    print("🔮 Buscando projeções do Focus/Bacen...")
    projecoes = bcb.formatar_para_prompt(bcb.obter_projecoes())

    texto_carteira = parser.ler_carteira_texto()
    carteira = parser.estruturar_carteira(texto_carteira)
    holdings = carteira.get("holdings", [])

    m = None
    historico_mensal = carteira.get("historico_mensal") or []
    noticias_relevantes = ""
    if holdings:
        print("📊 Buscando dados de mercado e calculando métricas...")
        dados_mercado = quotes.obter_dados_carteira(holdings)
        m = metrics.construir(holdings, dados_mercado, carteira)
        carteira_para_prompt = metrics.formatar_para_prompt(m)

        print("📰 Filtrando notícias ligadas à carteira e extraindo texto completo...")
        nomes = {tk: dm.get("nome") for tk, dm in dados_mercado.items()}
        relevantes = relevance.filtrar_relevantes(entradas, holdings, nomes, limite=8)
        relevantes = scraper.enriquecer(relevantes, limite=8)
        noticias_relevantes = _formatar_relevantes(relevantes)
    else:
        # Sem estruturação: cai para o texto bruto da carteira.
        carteira_para_prompt = texto_carteira

    print("🤖 Inteligência Artificial processando...")
    resumo_completo = llm.gerar_resumo(
        raw_news, carteira_para_prompt, noticias_relevantes, projecoes
    )

    print("📲 Enviando blocos para o Telegram...")
    telegram.enviar_telegram(resumo_completo)

    if m:
        _enviar_graficos(m, historico_mensal)

    print("✅ Tudo pronto!")


def _enviar_graficos(m: dict, historico_mensal):
    """Persiste o snapshot e envia os gráficos da carteira ao Telegram."""
    print("📈 Gerando gráficos da carteira...")

    # Persistência (no-op sem DATABASE_URL): snapshot do dia + histórico do relatório.
    repo.salvar_snapshot(m)
    repo.seed_historico_mensal(historico_mensal)

    # Série de evolução: do banco se disponível, senão direto do relatório.
    if repo.disponivel():
        serie = repo.historico_patrimonio()
    else:
        serie = repo.mensal_para_serie(historico_mensal)

    graficos = [
        ("📊 Alocação por classe de ativo", render.alocacao_por_classe(m)),
        (f"📈 Rentabilidade {m.get('rentab_label', '')} por ativo".strip(), render.momentum_por_ativo(m)),
        ("💹 Evolução do patrimônio", render.evolucao_patrimonio(serie)),
    ]
    for legenda, imagem in graficos:
        if imagem is not None:
            telegram.enviar_foto(imagem, legenda)


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"\n❌ OCORREU UM ERRO:\n{e}")

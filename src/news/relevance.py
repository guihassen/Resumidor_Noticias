"""Filtra e pontua notícias por relevância aos ativos da carteira.

Precisão > recall: é pior marcar como "ligada à carteira" uma notícia que não
é (ex: "Itaú BBA" aparece em recomendações sobre outras empresas) do que perder
uma. Por isso o gatilho é o TICKER (ex: ITUB4) ou a FRASE do nome da empresa
(ex: "itau unibanco" contígua), nunca uma palavra solta genérica.
"""
import re
import unicodedata

# Palavras genéricas demais para servir de gatilho isolado.
_STOPWORDS = {
    "holding", "sa", "fii", "fundo", "fundos", "investimento", "investimentos",
    "brasil", "companhia", "participacoes", "banco", "energia", "eletrica",
    "imobiliario", "imobiliarios", "logistica", "renda", "tesouro", "credito",
    "agro", "agricola",  # genéricos em manchetes de agronegócio
}

# Bancos/casas de research: aparecem em notícias de TERCEIROS (ex: "Itaú BBA
# corta preço da JBS"). Como token isolado geram falso positivo, então só
# casam via ticker ou via a frase completa do nome (ex: "itau unibanco").
_AMBIGUOS = {
    "itau", "bradesco", "santander", "btg", "bba", "safra", "genial",
    "guide", "ativa", "inter", "citi", "ubs", "goldman", "morgan", "bofa",
}


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower()


def _perfil_por_ativo(holdings, nomes_mercado=None):
    """Para cada ativo: gatilhos precisos (palavra inteira) e uma frase de nome."""
    nomes_mercado = nomes_mercado or {}
    perfis = {}
    for h in holdings:
        ticker = h.get("ticker")
        if not ticker:
            continue
        precisos = {_normalizar(ticker)}
        nome = _normalizar(nomes_mercado.get(ticker) or h.get("descricao") or "")
        tokens = [w for w in re.findall(r"[a-z0-9]{3,}", nome) if w not in _STOPWORDS]
        frase = " ".join(tokens[:2]) if len(tokens) >= 2 else None
        # Cada token distintivo vira gatilho; bancos/research só pela frase/ticker.
        for tok in tokens:
            if tok not in _AMBIGUOS:
                precisos.add(tok)
        perfis[ticker] = (precisos, frase)
    return perfis


def _ativos_citados(entrada, perfis) -> set:
    alvo = _normalizar(f"{entrada.get('titulo', '')} {entrada.get('resumo', '')}")
    citados = set()
    for ticker, (precisos, frase) in perfis.items():
        hit = any(re.search(rf"\b{re.escape(k)}\b", alvo) for k in precisos)
        if not hit and frase and frase in alvo:
            hit = True
        if hit:
            citados.add(ticker)
    return citados


def filtrar_relevantes(entradas, holdings, nomes_mercado=None, limite: int = 8):
    """Retorna as entradas que citam ativos da carteira, anotadas com 'ativos'."""
    perfis = _perfil_por_ativo(holdings, nomes_mercado)
    vistos = set()
    relevantes = []
    for e in entradas:
        link = e.get("link", "")
        if link and link in vistos:
            continue
        citados = _ativos_citados(e, perfis)
        if citados:
            vistos.add(link)
            anotada = dict(e)
            anotada["ativos"] = sorted(citados)
            relevantes.append(anotada)
    return relevantes[:limite]

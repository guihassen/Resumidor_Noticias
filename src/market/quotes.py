"""Dados de mercado para os ativos de renda variável.

Primário: yfinance (gratuito, sem token, sufixo .SA para a B3).
Opcional: brapi.dev quando BRAPI_TOKEN estiver definido (mais estável para a B3).
Cada ticker é tolerante a falha: retorna o que conseguir, sem derrubar o resto.
"""
import os

import requests

BRAPI_TOKEN = os.getenv("BRAPI_TOKEN")
TIPOS_RENDA_VARIAVEL = {"Ação", "ACAO", "FII", "ETF", "BDR"}


def _normalizar_dy(dy):
    """yfinance ora devolve fração (0.08), ora percentual (8.0). Normaliza p/ %."""
    if dy is None:
        return None
    try:
        dy = float(dy)
    except (TypeError, ValueError):
        return None
    return dy * 100 if dy < 1 else dy


def _via_yfinance(ticker: str) -> dict:
    import yfinance as yf

    t = yf.Ticker(f"{ticker}.SA")
    info = {}
    try:
        info = t.info or {}
    except Exception:
        info = {}

    preco = info.get("currentPrice") or info.get("regularMarketPrice")

    var_mes = None
    try:
        hist = t.history(period="1mo")
        if len(hist) > 1:
            ini = float(hist["Close"].iloc[0])
            fim = float(hist["Close"].iloc[-1])
            if not preco:
                preco = fim
            if ini:
                var_mes = round((fim / ini - 1) * 100, 2)
    except Exception:
        pass

    return {
        "ticker": ticker,
        "nome": info.get("longName") or info.get("shortName"),
        "preco": preco,
        "var_dia_pct": info.get("regularMarketChangePercent"),
        "var_mes_pct": var_mes,
        "pl": info.get("trailingPE"),
        "pvp": info.get("priceToBook"),
        "dy_pct": _normalizar_dy(info.get("dividendYield")),
        "setor": info.get("sector"),
        "industria": info.get("industry"),
        "preco_alvo": info.get("targetMeanPrice"),
        "n_analistas": info.get("numberOfAnalystOpinions"),
        "recomendacao": info.get("recommendationKey"),
        "min_52s": info.get("fiftyTwoWeekLow"),
        "max_52s": info.get("fiftyTwoWeekHigh"),
        "fonte": "yfinance",
    }


def _via_brapi(ticker: str) -> dict:
    url = f"https://brapi.dev/api/quote/{ticker}"
    params = {"range": "1mo", "interval": "1d", "fundamental": "true", "dividends": "true"}
    if BRAPI_TOKEN:
        params["token"] = BRAPI_TOKEN
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    res = r.json()["results"][0]

    var_mes = None
    hist = res.get("historicalDataPrice") or []
    if len(hist) > 1 and hist[0].get("close") and hist[-1].get("close"):
        var_mes = round((hist[-1]["close"] / hist[0]["close"] - 1) * 100, 2)

    return {
        "ticker": ticker,
        "nome": res.get("longName") or res.get("shortName"),
        "preco": res.get("regularMarketPrice"),
        "var_dia_pct": res.get("regularMarketChangePercent"),
        "var_mes_pct": var_mes,
        "pl": res.get("priceEarnings"),
        "pvp": None,
        "dy_pct": None,
        "setor": None,
        "industria": None,
        "preco_alvo": None,
        "n_analistas": None,
        "recomendacao": None,
        "min_52s": res.get("fiftyTwoWeekLow"),
        "max_52s": res.get("fiftyTwoWeekHigh"),
        "fonte": "brapi",
    }


def obter_dados(ticker: str) -> dict:
    """Tenta brapi (se houver token) e cai para yfinance; nunca lança exceção."""
    if BRAPI_TOKEN:
        try:
            return _via_brapi(ticker)
        except Exception as e:
            print(f"brapi falhou para {ticker}: {e}; tentando yfinance.")
    try:
        return _via_yfinance(ticker)
    except Exception as e:
        print(f"yfinance falhou para {ticker}: {e}")
        return {"ticker": ticker, "preco": None, "fonte": "indisponivel"}


def obter_dados_carteira(holdings) -> dict:
    """Busca dados de mercado para os ativos de renda variável da carteira."""
    dados = {}
    for h in holdings:
        ticker = h.get("ticker")
        if not ticker or h.get("tipo") not in TIPOS_RENDA_VARIAVEL:
            continue
        dados[ticker] = obter_dados(ticker)
    return dados

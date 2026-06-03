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


def _rsi(close, periodo: int = 14):
    """Índice de Força Relativa (RSI) clássico. Retorna o último valor ou None."""
    if len(close) <= periodo:
        return None
    delta = close.diff()
    ganho = delta.clip(lower=0).rolling(periodo).mean()
    perda = (-delta.clip(upper=0)).rolling(periodo).mean()
    rs = ganho / perda.replace(0, float("nan"))
    rsi = 100 - 100 / (1 + rs)
    valor = rsi.iloc[-1]
    return round(float(valor), 1) if valor == valor else None  # NaN-safe


def _tecnicos(close, preco: float) -> dict:
    """Médias móveis, tendência, RSI e volatilidade a partir da série de fechamento."""
    out = {"sma9": None, "sma21": None, "tendencia": None, "rsi": None, "volatilidade_pct": None}
    if len(close) >= 9:
        out["sma9"] = round(float(close.rolling(9).mean().iloc[-1]), 2)
    if len(close) >= 21:
        out["sma21"] = round(float(close.rolling(21).mean().iloc[-1]), 2)
    if out["sma9"] and out["sma21"] and preco:
        if preco > out["sma9"] > out["sma21"]:
            out["tendencia"] = "alta"
        elif preco < out["sma9"] < out["sma21"]:
            out["tendencia"] = "baixa"
        else:
            out["tendencia"] = "lateral"
    out["rsi"] = _rsi(close)
    retornos = close.pct_change().dropna()
    if len(retornos) >= 10:
        out["volatilidade_pct"] = round(float(retornos.tail(21).std() * (252 ** 0.5) * 100), 1)
    return out


def _ts_para_data(ts):
    """Converte timestamp/datetime/date em 'AAAA-MM-DD' (ou None). Vazio -> None."""
    if ts is None:
        return None
    try:
        from datetime import date, datetime
        if isinstance(ts, (list, tuple)):
            if not ts:
                return None
            ts = ts[0]
        if isinstance(ts, bool):
            return None
        if isinstance(ts, (int, float)):
            return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
        if isinstance(ts, datetime):
            return ts.strftime("%Y-%m-%d")
        if isinstance(ts, date):
            return ts.strftime("%Y-%m-%d")
        s = str(ts)[:10]
        return s if len(s) == 10 and s[4] == "-" else None
    except Exception:
        return None


def _so_futuro(data_iso):
    """Mantém a data só se for hoje ou no futuro (eventos passados não interessam)."""
    if not data_iso:
        return None
    from datetime import date
    try:
        return data_iso if data_iso >= date.today().isoformat() else None
    except Exception:
        return None


def _eventos(ticker_obj, info: dict) -> dict:
    """Próximos eventos FUTUROS: resultado e data-ex de dividendo (best-effort)."""
    resultado = dividendo = None
    try:
        cal = ticker_obj.calendar
        if isinstance(cal, dict):
            resultado = _ts_para_data(cal.get("Earnings Date"))
            dividendo = _ts_para_data(cal.get("Ex-Dividend Date"))
    except Exception:
        pass
    if not resultado:
        resultado = _ts_para_data(info.get("earningsTimestampStart") or info.get("earningsTimestamp"))
    if not dividendo:
        dividendo = _ts_para_data(info.get("exDividendDate"))
    return {"prox_resultado": _so_futuro(resultado), "prox_dividendo": _so_futuro(dividendo)}


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
    tecnicos = {"sma9": None, "sma21": None, "tendencia": None, "rsi": None, "volatilidade_pct": None}
    try:
        hist = t.history(period="3mo")
        close = hist["Close"].dropna()
        if len(close) > 1:
            if not preco:
                preco = float(close.iloc[-1])
            base = float(close.iloc[-22]) if len(close) > 21 else float(close.iloc[0])
            if base:
                var_mes = round((preco / base - 1) * 100, 2)
            tecnicos = _tecnicos(close, preco)
    except Exception:
        pass

    pos_52s = None
    low, high = info.get("fiftyTwoWeekLow"), info.get("fiftyTwoWeekHigh")
    if preco and low is not None and high is not None and high > low:
        pos_52s = round((preco - low) / (high - low) * 100, 1)

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
        "min_52s": low,
        "max_52s": high,
        "pos_52s_pct": pos_52s,
        "tendencia": tecnicos["tendencia"],
        "sma9": tecnicos["sma9"],
        "sma21": tecnicos["sma21"],
        "rsi": tecnicos["rsi"],
        "volatilidade_pct": tecnicos["volatilidade_pct"],
        "eventos": _eventos(t, info),
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


def cambio_atual():
    """Cotação atual do dólar (USD/BRL). Retorna float ou None."""
    try:
        import yfinance as yf

        hist = yf.Ticker("BRL=X").history(period="5d")
        close = hist["Close"].dropna()
        if len(close):
            return round(float(close.iloc[-1]), 4)
    except Exception:
        pass
    return None


def obter_dados_carteira(holdings) -> dict:
    """Busca dados de mercado para os ativos de renda variável da carteira."""
    dados = {}
    for h in holdings:
        ticker = h.get("ticker")
        if not ticker or h.get("tipo") not in TIPOS_RENDA_VARIAVEL:
            continue
        dados[ticker] = obter_dados(ticker)
    return dados

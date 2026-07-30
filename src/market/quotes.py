"""Cotação de câmbio para contextualizar as projeções macro."""


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

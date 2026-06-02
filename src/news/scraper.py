"""Extração do texto completo das matérias (scraping) com trafilatura."""

_MAX_CHARS = 2500  # limita tokens enviados à IA por matéria


def extrair_texto(url: str):
    """Baixa a URL e extrai o corpo principal da matéria. Retorna None se falhar."""
    if not url:
        return None
    try:
        import trafilatura
    except ImportError:
        return None
    try:
        baixado = trafilatura.fetch_url(url)
        if not baixado:
            return None
        texto = trafilatura.extract(
            baixado, include_comments=False, include_tables=False, favor_recall=True
        )
        if not texto:
            return None
        texto = texto.strip()
        return texto[:_MAX_CHARS] + ("..." if len(texto) > _MAX_CHARS else "")
    except Exception:
        return None


def enriquecer(entradas, limite: int = 8):
    """Adiciona 'texto_completo' às entradas (até `limite`), caindo no resumo."""
    enriquecidas = []
    sucesso = 0
    for e in entradas[:limite]:
        texto = extrair_texto(e.get("link", ""))
        e = dict(e)
        if texto:
            e["texto_completo"] = texto
            sucesso += 1
        else:
            e["texto_completo"] = e.get("resumo", "")
        enriquecidas.append(e)
    print(f"Scraping: {sucesso}/{len(enriquecidas)} matérias com texto completo.")
    return enriquecidas

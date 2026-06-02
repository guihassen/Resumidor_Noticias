"""Coleta de notícias via RSS."""
import feedparser

from src import config


def coletar_entradas(por_fonte: int = 5):
    """Retorna entradas estruturadas: {titulo, link, resumo, fonte}."""
    entradas = []
    for url in config.FONTES_RSS:
        feed = feedparser.parse(url)
        fonte = feed.feed.get("title", url) if getattr(feed, "feed", None) else url
        for e in feed.entries[:por_fonte]:
            entradas.append({
                "titulo": e.get("title", ""),
                "link": e.get("link", ""),
                "resumo": e.get("summary", ""),
                "fonte": fonte,
            })
    return entradas


def formatar_entradas(entradas, resumo_curto: bool = False) -> str:
    """Converte entradas em texto plano (título + resumo)."""
    texto = ""
    for e in entradas:
        resumo = e["resumo"]
        if resumo_curto and len(resumo) > 200:
            resumo = resumo[:200] + "..."
        texto += f"Título: {e['titulo']}\nResumo: {resumo}\n\n"
    return texto


def buscar_noticias(resumo_curto: bool = False, por_fonte: int = 5) -> str:
    """Versão em texto plano (título + resumo). Usada no fallback do Groq."""
    return formatar_entradas(coletar_entradas(por_fonte=por_fonte), resumo_curto=resumo_curto)

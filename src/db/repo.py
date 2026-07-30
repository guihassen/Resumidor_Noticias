"""Dedupe de notícias entre execuções (Postgres privado via DATABASE_URL).

Degradação graciosa: sem DATABASE_URL, todas as funções viram no-op e o
pipeline segue normalmente (apenas sem dedupe).
Os dados NUNCA ficam no repositório — vivem na base privada da nuvem.
"""
import os
from datetime import datetime

from sqlalchemy import (
    Column, DateTime, Integer, MetaData, String, Table, create_engine, insert, select,
)

_engine = None
_inicializado = False
_meta = MetaData()

news_seen = Table(
    "news_seen", _meta,
    Column("id", Integer, primary_key=True),
    Column("link", String(500), index=True),
    Column("titulo", String(500)),
    Column("visto_em", DateTime, default=datetime.utcnow, index=True),
)


def _normalizar_url(url: str) -> str:
    # Heroku/Supabase às vezes entregam "postgres://"; SQLAlchemy quer "postgresql://".
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


def get_engine():
    global _engine, _inicializado
    if _inicializado:
        return _engine
    _inicializado = True
    url = os.getenv("DATABASE_URL")
    if not url:
        print("DATABASE_URL não definido: dedupe de notícias desativado.")
        return None
    try:
        _engine = create_engine(_normalizar_url(url), pool_pre_ping=True)
        _meta.create_all(_engine)
    except Exception as e:
        print(f"Falha ao conectar no banco: {e}")
        _engine = None
    return _engine


def disponivel() -> bool:
    return get_engine() is not None


def filtrar_noticias_novas(entradas, horas: int = 20):
    """Remove notícias já vistas em runs recentes (janela `horas`) e registra as novas.

    Sem DATABASE_URL, retorna as entradas inalteradas (dedupe desativado).
    """
    eng = get_engine()
    if not eng or not entradas:
        return entradas
    from datetime import timedelta

    corte = datetime.utcnow() - timedelta(hours=horas)
    try:
        with eng.connect() as conn:
            vistos = {
                r[0]
                for r in conn.execute(
                    select(news_seen.c.link).where(news_seen.c.visto_em >= corte)
                ).all()
            }
        # Mantém quem não tem link (não dá pra deduplicar) ou cujo link é inédito.
        novas = [e for e in entradas if not e.get("link") or e["link"] not in vistos]
        with eng.begin() as conn:
            for e in novas:
                link = e.get("link")
                if link:
                    conn.execute(insert(news_seen).values(
                        link=link[:500], titulo=(e.get("titulo") or "")[:500]
                    ))
        removidas = len(entradas) - len(novas)
        if removidas:
            print(f"Dedupe: {removidas} notícias já vistas removidas; {len(novas)} novas.")
        return novas
    except Exception as e:
        print(f"Falha no dedupe de notícias: {e}")
        return entradas

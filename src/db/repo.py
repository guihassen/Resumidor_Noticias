"""Persistência de snapshots da carteira (Postgres privado via DATABASE_URL).

Degradação graciosa: sem DATABASE_URL, todas as funções viram no-op e o
pipeline segue normalmente (apenas sem histórico / gráfico de evolução).
Os dados NUNCA ficam no repositório — vivem na base privada da nuvem.
"""
import os
from calendar import monthrange
from collections import OrderedDict
from datetime import date, datetime

from sqlalchemy import (
    Column, Date, DateTime, Float, Integer, MetaData, String, Table,
    create_engine, insert, select,
)

_engine = None
_inicializado = False
_meta = MetaData()

portfolio_snapshots = Table(
    "portfolio_snapshots", _meta,
    Column("id", Integer, primary_key=True),
    Column("data", Date, index=True),
    Column("valor_total", Float),
    Column("criado_em", DateTime, default=datetime.utcnow),
)

asset_snapshots = Table(
    "asset_snapshots", _meta,
    Column("id", Integer, primary_key=True),
    Column("data", Date, index=True),
    Column("ticker", String(20)),
    Column("tipo", String(20)),
    Column("valor", Float),
    Column("preco", Float),
    Column("peso_pct", Float),
)

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
        print("DATABASE_URL não definido: persistência desativada.")
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


def salvar_snapshot(m: dict) -> bool:
    eng = get_engine()
    if not eng:
        return False
    hoje = date.today()
    try:
        with eng.begin() as conn:
            conn.execute(insert(portfolio_snapshots).values(
                data=hoje, valor_total=m.get("valor_total")
            ))
            for it in m.get("itens", []):
                if it.get("valor"):
                    conn.execute(insert(asset_snapshots).values(
                        data=hoje,
                        ticker=it.get("ticker"),
                        tipo=it.get("tipo"),
                        valor=it.get("valor"),
                        preco=it.get("preco"),
                        peso_pct=it.get("peso_pct"),
                    ))
        return True
    except Exception as e:
        print(f"Falha ao salvar snapshot: {e}")
        return False


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


def _mes_para_data(mes_str: str):
    """'2026-01' -> date(2026, 1, 31) (último dia do mês)."""
    ano, mes = (int(x) for x in mes_str.split("-"))
    return date(ano, mes, monthrange(ano, mes)[1])


def seed_historico_mensal(historico) -> int:
    """Insere o histórico mensal do relatório (idempotente: pula meses já gravados)."""
    eng = get_engine()
    if not eng or not historico:
        return 0
    try:
        with eng.connect() as conn:
            existentes = {r[0] for r in conn.execute(select(portfolio_snapshots.c.data)).all()}
        novos = 0
        with eng.begin() as conn:
            for item in historico:
                mes = item.get("mes")
                pat = item.get("patrimonio")
                if not mes or pat is None:
                    continue
                try:
                    d = _mes_para_data(mes)
                except (ValueError, AttributeError):
                    continue
                if d in existentes:
                    continue
                conn.execute(insert(portfolio_snapshots).values(data=d, valor_total=pat))
                existentes.add(d)
                novos += 1
        if novos:
            print(f"Histórico mensal semeado: {novos} meses novos.")
        return novos
    except Exception as e:
        print(f"Falha ao semear histórico mensal: {e}")
        return 0


def mensal_para_serie(historico):
    """Converte o histórico mensal do relatório em [(data, valor)] ordenado."""
    serie = []
    for item in historico or []:
        mes = item.get("mes")
        pat = item.get("patrimonio")
        if not mes or pat is None:
            continue
        try:
            serie.append((_mes_para_data(mes), pat))
        except (ValueError, AttributeError):
            continue
    return sorted(serie)


def historico_patrimonio():
    """Lista [(data, valor_total)] com um ponto por dia (o último de cada dia)."""
    eng = get_engine()
    if not eng:
        return []
    try:
        with eng.connect() as conn:
            rows = conn.execute(
                select(portfolio_snapshots.c.data, portfolio_snapshots.c.valor_total)
                .order_by(portfolio_snapshots.c.data, portfolio_snapshots.c.id)
            ).all()
    except Exception as e:
        print(f"Falha ao ler histórico: {e}")
        return []
    por_dia = OrderedDict()
    for data_, valor in rows:
        if valor is not None:
            por_dia[data_] = valor
    return list(por_dia.items())

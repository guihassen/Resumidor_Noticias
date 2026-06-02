"""Cálculo de métricas da carteira a partir dos holdings + dados de mercado.

Quando o relatório do XP traz patrimônio oficial e rentabilidade por ativo
(via `dados_carteira`), esses números são a fonte de verdade para valor e
ganho/perda; os dados de mercado ao vivo (P/L, P/VP, DY, setor, metas de
analistas) complementam a análise de valuation.
"""
from collections import defaultdict

from src.market.quotes import TIPOS_RENDA_VARIAVEL


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def construir(holdings, dados_mercado: dict, dados_carteira: dict = None) -> dict:
    dados_carteira = dados_carteira or {}
    itens = []
    total = 0.0

    for h in holdings:
        ticker = h.get("ticker")
        tipo = h.get("tipo", "Outro")
        qtd = _num(h.get("quantidade"))
        dm = dados_mercado.get(ticker, {})
        preco = _num(dm.get("preco"))

        # Valor: prioriza a posição oficial do extrato; senão, cotação ao vivo.
        valor = _num(h.get("valor_posicao"))
        if valor is None and tipo in TIPOS_RENDA_VARIAVEL and preco and qtd:
            valor = preco * qtd

        if valor:
            total += valor

        rent_mes = _num(h.get("rent_mes_pct"))
        rent_ano = _num(h.get("rent_ano_pct"))
        var_mes_mercado = _num(dm.get("var_mes_pct"))

        itens.append({
            "ticker": ticker,
            "tipo": tipo,
            "nome": dm.get("nome") or h.get("descricao"),
            "quantidade": qtd,
            "preco": preco,
            "valor": valor,
            "rent_mes_pct": rent_mes,
            "rent_ano_pct": rent_ano,
            "var_mes_mercado_pct": var_mes_mercado,
            # rentabilidade a exibir/plotar: prioriza o ano do XP, senão o mês do XP, senão mercado
            "rentab_pct": rent_ano if rent_ano is not None else (rent_mes if rent_mes is not None else var_mes_mercado),
            "pl": _num(dm.get("pl")),
            "pvp": _num(dm.get("pvp")),
            "dy_pct": _num(dm.get("dy_pct")),
            "setor": dm.get("setor"),
            "preco_alvo": _num(dm.get("preco_alvo")),
            "recomendacao": dm.get("recomendacao"),
        })

    # Patrimônio oficial do XP é a fonte de verdade; senão soma das posições.
    patrimonio_oficial = _num(dados_carteira.get("patrimonio_total"))
    total = patrimonio_oficial if patrimonio_oficial else round(total, 2)

    for it in itens:
        it["peso_pct"] = round(it["valor"] / total * 100, 2) if (it["valor"] and total) else None

    por_classe = defaultdict(float)
    por_setor = defaultdict(float)
    dy_ponderado_num = 0.0
    dy_ponderado_den = 0.0

    for it in itens:
        if not it["valor"]:
            continue
        por_classe[it["tipo"]] += it["valor"]
        if it["tipo"] in TIPOS_RENDA_VARIAVEL and it["setor"]:
            por_setor[it["setor"]] += it["valor"]
        if it["dy_pct"] is not None:
            dy_ponderado_num += it["dy_pct"] * it["valor"]
            dy_ponderado_den += it["valor"]

    def pct(d):
        return {k: round(v / total * 100, 2) for k, v in sorted(d.items(), key=lambda x: -x[1])} if total else {}

    # Rótulo da rentabilidade exibida (depende da fonte disponível).
    tem_xp_ano = any(i["rent_ano_pct"] is not None for i in itens)
    tem_xp_mes = any(i["rent_mes_pct"] is not None for i in itens)
    rentab_label = "no ano (XP)" if tem_xp_ano else ("no mês (XP)" if tem_xp_mes else "no mês (mercado)")

    com_rentab = [i for i in itens if i["rentab_pct"] is not None]
    maiores_altas = sorted(com_rentab, key=lambda i: -i["rentab_pct"])[:3]
    maiores_baixas = sorted(com_rentab, key=lambda i: i["rentab_pct"])[:3]

    observacoes = _observacoes(itens, pct(por_classe), pct(por_setor))

    return {
        "valor_total": total,
        "n_ativos": len(itens),
        "itens": sorted(itens, key=lambda i: -(i["valor"] or 0)),
        "alocacao_classe_pct": pct(por_classe),
        "alocacao_setor_pct": pct(por_setor),
        "dy_medio_ponderado_pct": round(dy_ponderado_num / dy_ponderado_den, 2) if dy_ponderado_den else None,
        "rentab_label": rentab_label,
        "maiores_altas": [(i["ticker"], i["rentab_pct"]) for i in maiores_altas],
        "maiores_baixas": [(i["ticker"], i["rentab_pct"]) for i in maiores_baixas],
        "rent_carteira": dados_carteira.get("rent_carteira") or {},
        "benchmarks": dados_carteira.get("benchmarks") or {},
        "observacoes": observacoes,
    }


def _observacoes(itens, classe_pct, setor_pct):
    """Sinais heurísticos para ancorar a análise da IA (não são recomendações)."""
    obs = []
    for it in itens:
        if it["peso_pct"] and it["peso_pct"] >= 25:
            obs.append(f"Concentração: {it['ticker']} representa {it['peso_pct']}% da carteira.")
    for setor, p in setor_pct.items():
        if p >= 40:
            obs.append(f"Concentração setorial: {setor} ~{p}% da carteira.")
    rv_total = sum(v for k, v in classe_pct.items() if k in TIPOS_RENDA_VARIAVEL)
    if rv_total and rv_total < 15:
        obs.append(f"Baixa exposição a renda variável (~{round(rv_total, 1)}%).")
    for it in itens:
        if it["pl"] and it["pl"] > 25:
            obs.append(f"Valuation alto: {it['ticker']} com P/L {round(it['pl'], 1)}.")
        if it["rent_ano_pct"] is not None and it["rent_ano_pct"] <= -10:
            obs.append(f"{it['ticker']} acumula {it['rent_ano_pct']}% no ano (maior perda relativa).")
        if it["preco"] and it["preco_alvo"]:
            upside = (it["preco_alvo"] / it["preco"] - 1) * 100
            if abs(upside) >= 15:
                obs.append(f"{it['ticker']}: preço-alvo de analistas implica {round(upside, 1)}% vs. atual.")
    return obs


def _fmt(v, suf="", casas=2):
    if v is None:
        return "n/d"
    if isinstance(v, float):
        return f"{v:.{casas}f}{suf}"
    return f"{v}{suf}"


def _bloco_resultado(m: dict):
    rent = m.get("rent_carteira") or {}
    if not rent:
        return []
    bench = m.get("benchmarks") or {}
    linhas = ["\nRESULTADO DA CARTEIRA (oficial XP):"]
    linhas.append(f"  • Rentabilidade: mês {_fmt(rent.get('mes'), '%')} | ano {_fmt(rent.get('ano'), '%')}")
    if bench:
        comp = " | ".join(
            f"{nome} mês {_fmt(v.get('mes'), '%')}/ano {_fmt(v.get('ano'), '%')}"
            for nome, v in bench.items()
        )
        linhas.append(f"  • Benchmarks: {comp}")
    return linhas


def formatar_para_prompt(m: dict) -> str:
    """Bloco de texto compacto e legível com as métricas, para alimentar a IA."""
    linhas = [f"PATRIMÔNIO TOTAL: R$ {m['valor_total']:.2f} ({m['n_ativos']} ativos)"]

    linhas += _bloco_resultado(m)

    linhas.append("\nALOCAÇÃO POR CLASSE:")
    for k, v in m["alocacao_classe_pct"].items():
        linhas.append(f"  • {k}: {v}%")

    if m["alocacao_setor_pct"]:
        linhas.append("\nEXPOSIÇÃO SETORIAL (renda variável):")
        for k, v in m["alocacao_setor_pct"].items():
            linhas.append(f"  • {k}: {v}%")

    if m["dy_medio_ponderado_pct"] is not None:
        linhas.append(f"\nDIVIDEND YIELD MÉDIO PONDERADO (RV): {m['dy_medio_ponderado_pct']}%")

    linhas.append("\nATIVOS (ordenados por valor):")
    for it in m["itens"]:
        peso = f"{it['peso_pct']}%" if it["peso_pct"] is not None else "n/d"
        det = f"valor R$ {_fmt(it['valor'])} ({peso})"
        if it["rent_mes_pct"] is not None or it["rent_ano_pct"] is not None:
            det += f" | rent mês {_fmt(it['rent_mes_pct'], '%')}/ano {_fmt(it['rent_ano_pct'], '%')}"
        if it["pl"] is not None or it["pvp"] is not None or it["dy_pct"] is not None:
            det += f" | P/L {_fmt(it['pl'])} | P/VP {_fmt(it['pvp'])} | DY {_fmt(it['dy_pct'], '%')}"
        if it["preco_alvo"]:
            det += f" | alvo {_fmt(it['preco_alvo'])}"
        if it["recomendacao"]:
            det += f" | rec: {it['recomendacao']}"
        setor = f" [{it['setor']}]" if it["setor"] else ""
        linhas.append(f"  • {it['ticker']} ({it['tipo']}){setor}: {det}")

    rotulo = m.get("rentab_label", "")
    if m["maiores_altas"]:
        linhas.append(f"\nRENTABILIDADE {rotulo} — melhores: " + ", ".join(f"{t} {v}%" for t, v in m["maiores_altas"]))
    if m["maiores_baixas"]:
        linhas.append(f"RENTABILIDADE {rotulo} — piores: " + ", ".join(f"{t} {v}%" for t, v in m["maiores_baixas"]))

    if m["observacoes"]:
        linhas.append("\nSINAIS DETECTADOS (use como base, não repita cru):")
        for o in m["observacoes"]:
            linhas.append(f"  • {o}")

    return "\n".join(linhas)

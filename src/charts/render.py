"""Geração de gráficos (PNG em memória) para enviar ao Telegram."""
import io

import matplotlib

matplotlib.use("Agg")  # backend headless (sem display), essencial no GitHub Actions
import matplotlib.pyplot as plt  # noqa: E402

_CORES = ["#2e86de", "#27ae60", "#e67e22", "#8e44ad", "#16a085", "#c0392b", "#f39c12"]


def _para_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
    plt.close(fig)
    buf.seek(0)
    return buf


def alocacao_por_classe(m: dict):
    dados = m.get("alocacao_classe_pct") or {}
    if not dados:
        return None
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(
        list(dados.values()),
        labels=list(dados.keys()),
        autopct="%1.1f%%",
        startangle=90,
        colors=_CORES,
        wedgeprops={"edgecolor": "white"},
    )
    ax.set_title("Alocação por classe de ativo")
    return _para_bytes(fig)


def momentum_por_ativo(m: dict):
    itens = [it for it in m.get("itens", []) if it.get("rentab_pct") is not None]
    if not itens:
        return None
    itens = sorted(itens, key=lambda i: i["rentab_pct"])
    tickers = [i["ticker"] for i in itens]
    valores = [i["rentab_pct"] for i in itens]
    cores = ["#c0392b" if v < 0 else "#27ae60" for v in valores]
    fig, ax = plt.subplots(figsize=(7, max(3, 0.6 * len(itens) + 1)))
    ax.barh(tickers, valores, color=cores)
    ax.axvline(0, color="#333", linewidth=0.8)
    ax.set_title(f"Rentabilidade {m.get('rentab_label', '')} por ativo (%)".strip())

    # Rótulos ancorados junto ao eixo zero (evita colidir com o nome do ticker).
    maxabs = max(abs(v) for v in valores) or 1
    ax.set_xlim(min(min(valores), 0) - maxabs * 0.05, max(max(valores), 0) + maxabs * 0.20)
    offset = maxabs * 0.02
    for i, v in enumerate(valores):
        if v < 0:
            ax.text(offset, i, f"{v:.1f}%", va="center", ha="left", fontsize=9)
        else:
            ax.text(-offset, i, f"{v:.1f}%", va="center", ha="right", fontsize=9)
    return _para_bytes(fig)


def evolucao_patrimonio(historico):
    if not historico or len(historico) < 2:
        return None
    import matplotlib.dates as mdates

    datas = [d for d, _ in historico]
    valores = [v for _, v in historico]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(datas, valores, marker="o", color="#2e86de")
    ax.fill_between(datas, valores, min(valores) * 0.98, alpha=0.1, color="#2e86de")
    ax.set_title("Evolução do patrimônio (R$)")
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    fig.autofmt_xdate()
    return _para_bytes(fig)

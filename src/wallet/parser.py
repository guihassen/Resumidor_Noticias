"""Leitura e estruturação da carteira.

Etapa 1: extrai o texto bruto do PDF (ou da variável de ambiente CARTEIRA).
Etapa 2: usa o Gemini para converter esse texto em uma lista estruturada de
ativos (holdings), robusta ao formato do extrato.
"""
import json
import os
import re

import PyPDF2

from src.clients import get_gemini


def extrair_texto_pdf(pdf_path: str = "wallet.pdf") -> str:
    texto = ""
    with open(pdf_path, "rb") as wallet:
        leitor = PyPDF2.PdfReader(wallet)
        for i, pagina in enumerate(leitor.pages):
            texto += f"--- PÁGINA {i + 1} ---\n{pagina.extract_text()}\n"
    return texto


def ler_carteira_texto() -> str:
    """Texto bruto da carteira: secret CARTEIRA em produção, senão PDF local."""
    carteira = os.getenv("CARTEIRA")
    if carteira:
        print("Carteira lida via secret CARTEIRA.")
        return carteira
    print("Carteira lida localmente (wallet.pdf).")
    return extrair_texto_pdf("wallet.pdf")


_PROMPT_PARSE = """Você recebe o texto extraído de um relatório/extrato de carteira de investimentos (B3/corretora).
Responda APENAS com um objeto JSON válido (nada fora do objeto), neste formato:

{{
  "patrimonio_total": 8743.78,
  "rent_carteira": {{"mes": -0.92, "ano": -0.53}},
  "benchmarks": {{"CDI": {{"mes": 0.91, "ano": 5.49}}, "Ibovespa": {{"mes": -5.73, "ano": 9.60}}, "IPCA": {{"mes": 0.42, "ano": 3.04}}, "Dolar": {{"mes": 0.65, "ano": -8.75}}}},
  "historico_mensal": [{{"mes": "2026-01", "patrimonio": 1800.0}}, {{"mes": "2026-02", "patrimonio": 3800.0}}],
  "holdings": [
    {{"ticker": "PETR4", "tipo": "Ação", "quantidade": 100, "valor_posicao": 3400.0, "rent_mes_pct": -1.2, "rent_ano_pct": 5.3, "descricao": "Petrobras PN"}}
  ]
}}

Regras:
- "holdings": TODOS os ativos. "tipo" ∈ {{"Ação","FII","ETF","BDR","Renda Fixa","Tesouro","Multimercado","Cripto","Outro"}}.
- "ticker" em MAIÚSCULAS sem ".SA". Para Renda Fixa/Tesouro/Fundos sem ticker, use um código curto e ponha o nome em "descricao".
- "valor_posicao" = valor atual da posição em reais (ex: "Saldo Bruto", "POSIÇÃO A MERCADO", "VALOR LÍQUIDO"). Se não houver, null.
- "rent_mes_pct"/"rent_ano_pct" = rentabilidade do ativo no mês/ano (coluna "Rent." do relatório), em %. Se não houver, null.
- "patrimonio_total" = patrimônio total bruto da carteira. "rent_carteira" = rentabilidade da carteira no mês/ano. Se não houver, null.
- "benchmarks" = CDI/Ibovespa/IPCA/Dólar (mês/ano), se houver; senão objeto vazio {{}}.
- "historico_mensal" = a partir da tabela de evolução por período: para cada mês, "mes" no formato "AAAA-MM" e "patrimonio" = patrimônio final do mês. Inclua só meses com patrimônio > 0. Se não houver tabela, lista vazia [].
- Campos numéricos como número (ponto decimal). NÃO invente: use só o que está no texto.

Texto da carteira:
{texto}
"""

_MODELOS_PARSE = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"]

_CARTEIRA_VAZIA = {
    "patrimonio_total": None,
    "rent_carteira": {},
    "benchmarks": {},
    "historico_mensal": [],
    "holdings": [],
}


def _extrair_json_objeto(texto: str):
    """Extrai o primeiro objeto JSON de uma resposta (tolerante a cercas ```)."""
    if not texto:
        return None
    limpo = texto.strip()
    limpo = re.sub(r"^```(?:json)?", "", limpo).strip()
    limpo = re.sub(r"```$", "", limpo).strip()
    inicio = limpo.find("{")
    fim = limpo.rfind("}")
    if inicio == -1 or fim == -1 or fim <= inicio:
        return None
    try:
        return json.loads(limpo[inicio : fim + 1])
    except json.JSONDecodeError:
        return None


def estruturar_carteira(texto_carteira: str) -> dict:
    """Extrai o objeto completo da carteira (holdings + patrimônio + histórico)."""
    prompt = _PROMPT_PARSE.format(texto=texto_carteira)
    client = get_gemini()
    for model in _MODELOS_PARSE:
        try:
            resp = client.models.generate_content(model=model, contents=prompt)
            dados = _extrair_json_objeto(resp.text)
            if dados and dados.get("holdings"):
                base = dict(_CARTEIRA_VAZIA)
                base.update(dados)
                print(
                    f"Carteira estruturada com {model}: {len(base['holdings'])} ativos, "
                    f"patrimônio {base.get('patrimonio_total')}, "
                    f"{len(base.get('historico_mensal') or [])} meses de histórico."
                )
                return base
        except Exception as e:
            print(f"Erro ao estruturar carteira no modelo {model}: {e}")
    print("Não foi possível estruturar a carteira; seguindo com texto bruto.")
    return dict(_CARTEIRA_VAZIA)


def estruturar_holdings(texto_carteira: str):
    """Compatibilidade: retorna apenas a lista de holdings."""
    return estruturar_carteira(texto_carteira).get("holdings", [])


def formatar_holdings(holdings) -> str:
    """Formata os holdings estruturados em texto legível para o prompt."""
    if not holdings:
        return ""
    linhas = []
    for h in holdings:
        ticker = h.get("ticker", "?")
        tipo = h.get("tipo", "?")
        qtd = h.get("quantidade")
        pm = h.get("preco_medio")
        desc = h.get("descricao", "")
        partes = [f"{ticker} ({tipo})"]
        if qtd is not None:
            partes.append(f"qtd {qtd}")
        if pm is not None:
            partes.append(f"PM R$ {pm}")
        if desc:
            partes.append(desc)
        linhas.append(" - ".join(partes))
    return "\n".join(linhas)

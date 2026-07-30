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
  "holdings": [
    {{"ticker": "PETR4", "tipo": "Ação", "descricao": "Petrobras PN"}}
  ]
}}

Regras:
- "holdings": TODOS os ativos. "tipo" ∈ {{"Ação","FII","ETF","BDR","Renda Fixa","Tesouro","Multimercado","Cripto","Outro"}}.
- "ticker" em MAIÚSCULAS sem ".SA". Para Renda Fixa/Tesouro/Fundos sem ticker, use um código curto e ponha o nome em "descricao".
- NÃO invente: use só o que está no texto.

Texto da carteira:
{texto}
"""

_MODELOS_PARSE = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"]

_CARTEIRA_VAZIA = {
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
    """Extrai os ativos (holdings) da carteira, para filtrar notícias relacionadas."""
    prompt = _PROMPT_PARSE.format(texto=texto_carteira)
    client = get_gemini()
    for model in _MODELOS_PARSE:
        try:
            resp = client.models.generate_content(model=model, contents=prompt)
            dados = _extrair_json_objeto(resp.text)
            if dados and dados.get("holdings"):
                base = dict(_CARTEIRA_VAZIA)
                base.update(dados)
                print(f"Carteira estruturada com {model}: {len(base['holdings'])} ativos.")
                return base
        except Exception as e:
            print(f"Erro ao estruturar carteira no modelo {model}: {e}")
    print("Não foi possível estruturar a carteira; seguindo sem filtro por ativos.")
    return dict(_CARTEIRA_VAZIA)

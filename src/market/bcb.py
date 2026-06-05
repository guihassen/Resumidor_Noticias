"""Projeções macroeconômicas do Boletim Focus (Banco Central — API pública gratuita).

Usa a API Olinda/Expectativas para pegar a mediana mais recente das projeções
de mercado (Selic, IPCA, Câmbio, PIB) para o ano corrente e o seguinte.
"""
from datetime import date
from urllib.parse import quote

import requests

_BASE = (
    "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/"
    "ExpectativasMercadoAnuais"
)
_INDICADORES = ["Selic", "IPCA", "Câmbio", "PIB Total"]
_SUFIXO = {"Selic": "%", "IPCA": "%", "PIB Total": "%", "Câmbio": ""}


def _focus(indicador: str, ano: int):
    # O OData do Olinda rejeita espaço codificado como '+'; montamos a URL
    # manualmente com %20 (quote) em vez de passar via params do requests.
    filtro = f"Indicador eq '{indicador}' and DataReferencia eq '{ano}'"
    url = (
        f"{_BASE}?$format=json&$top=1"
        f"&$orderby={quote('Data desc', safe='')}"
        f"&$select={quote('Indicador,DataReferencia,Data,Mediana', safe='')}"
        f"&$filter={quote(filtro, safe='')}"
    )
    r = requests.get(url, timeout=25)
    r.raise_for_status()
    valores = r.json().get("value", [])
    return valores[0] if valores else None

_SGS = {"Selic": 432, "IPCA (12m)": 13522, "Câmbio (R$/US$)": 1}


def obter_valores_atuais() -> dict :
    "Valores Recentes de cada Indicador via API SGS do BCB"
    atuais = {}
    for rotulo, codigo in _SGS.items():

        try :
            url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados/ultimos/1?formato=json"
            r = requests.get(url, timeout=25)
            r.raise_for_status()
            dados = r.json()

            if dados :
                atuais[rotulo] = dados[-1]["valor"]
        
        except Exception as e :
            print(f"SGS falhou ({rotulo}): {e}")

    return atuais 


def obter_projecoes() -> dict:
    """{'Selic': {2026: 9.0, 2027: 8.5}, ...}. Tolerante a falhas por indicador."""
    ano = date.today().year
    projecoes = {}
    for indicador in _INDICADORES:
        for a in (ano, ano + 1):
            try:
                d = _focus(indicador, a)
            except Exception as e:
                print(f"Focus falhou ({indicador} {a}): {e}")
                d = None
            if d and d.get("Mediana") is not None:
                projecoes.setdefault(indicador, {})[a] = d["Mediana"]
    return projecoes


def formatar_para_prompt(projecoes: dict) -> str:
    if not projecoes:
        return ""
    linhas = ["PROJEÇÕES DE MERCADO — Boletim Focus/BCB (mediana, fim de período):"]

    atuais = obter_valores_atuais()

    if atuais :
        linhas.append("\nVALORES ATUAIS (BCB/SGS):")
        for rotulo, valor in atuais.items() :
            sufixo = "%" if rotulo != "Câmbio (R$/US$)" else ""
            linhas.append(f"  • {rotulo}: {valor}{sufixo}")

    for indicador in _INDICADORES:
        anos = projecoes.get(indicador)
        if not anos:
            continue
        suf = _SUFIXO.get(indicador, "")
        partes = [f"{ano}: {valor}{suf}" for ano, valor in sorted(anos.items())]
        rotulo = "Câmbio (R$/US$)" if indicador == "Câmbio" else indicador
        linhas.append(f"  • {rotulo}: " + " | ".join(partes))
    return "\n".join(linhas)

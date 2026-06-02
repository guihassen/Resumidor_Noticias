"""Compatibilidade: a extração de PDF agora vive em src/wallet/parser.py.

Mantido para o passo do README ("rode python leitor_wallet.py e copie o texto").
"""
from src.wallet.parser import extrair_texto_pdf as extrair_carteira

if __name__ == "__main__":
    # Roda no seu PC para copiar o texto da carteira para o secret CARTEIRA.
    print(extrair_carteira("wallet.pdf"))

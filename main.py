"""Ponto de entrada. A lógica vive em src/ (ver src/main.py)."""
import os

from src.main import run, run_resumo_dia

if __name__ == "__main__":
    try:
        if os.getenv("RESUMO_DIA", "").lower() == "true":
            run_resumo_dia()
        else:
            run()
    except Exception as e:
        print(f"\n❌ OCORREU UM ERRO:\n{e}")

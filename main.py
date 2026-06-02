"""Ponto de entrada. A lógica vive em src/ (ver src/main.py)."""
from src.main import run

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"\n❌ OCORREU UM ERRO:\n{e}")

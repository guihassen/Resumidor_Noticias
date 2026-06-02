"""Clientes de LLM criados de forma preguiçosa (lazy) para não falhar no import."""
from functools import lru_cache

from google import genai
from groq import Groq

from src import config


@lru_cache(maxsize=1)
def get_gemini():
    return genai.Client(api_key=config.GEMINI_KEY, http_options={"api_version": "v1"})


@lru_cache(maxsize=1)
def get_groq():
    return Groq(api_key=config.GROQ_KEY) if config.GROQ_KEY else None

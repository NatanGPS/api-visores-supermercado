import os
import secrets
from dotenv import load_dotenv
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

# Carrega variáveis do .env para garantir que API_KEYS esteja disponível
load_dotenv()

def _carregar_keys() -> dict[str, str]:
    bruto = os.getenv("API_KEYS", "")
    keys = {}
    for par in bruto.split(","):
        if ":" in par:
            chave, nome = par.split(":", 1)
            keys[chave.strip()] = nome.strip()
    return keys

# Usa função para carregar as chaves de API do arquivo .env antes de validar a utilização da API
API_KEYS = _carregar_keys()

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def validar_api_key(key: str | None = Security(api_key_header)) -> str:
    if key:
        for valida, nome in API_KEYS.items():
            if secrets.compare_digest(key, valida):
                return nome
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="API key inválida ou ausente",
    )

# Função para obter o nome da API Key
def obter_nome_api_key(key: str) -> str | None:
    for valida, nome in API_KEYS.items():
        if secrets.compare_digest(key, valida):
            pass # Teste de segurança para evitar timing attacks mas ainda não está retornando nada (função está pausada)


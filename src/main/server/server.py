from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.main.logging_config import setup_logging
from src.main.middleware.request_logging import RequestLoggingMiddleware
from src.main.security.api_key import validar_api_key
from src.main.routes.inserir_produtos_no_banco import router as inserir_produtos_no_banco_router
from src.main.routes.listar_produtos import router as listar_produtos_router
from src.main.routes.listar_produto_visor import router as listar_produto_visor_router
from src.main.routes.remover_produto import router as remover_produto_router
from src.main.routes.mostrar_paineis import router as mostrar_paineis_router

# Inicializa logging antes de criar a app para garantir handlers disponíveis
setup_logging()

# Config API
app = FastAPI(
    title="API ShowCase Açougue",
    description="API para gerenciamento de produtos e preços do açougue nos visores de preços",
    version="0.0.1", # para controle de versão da API, útil para documentação unicamente
    dependencies=[Depends(validar_api_key)],
)

# Config CORS (ainda ta um pouco sem uso)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware customizado para log de requisições (grava chamadas da API todos os erros)
app.add_middleware(RequestLoggingMiddleware)

# Incluindo as rotas que configurei aqui
app.include_router(inserir_produtos_no_banco_router)
app.include_router(listar_produtos_router)
app.include_router(listar_produto_visor_router)
app.include_router(mostrar_paineis_router)
app.include_router(remover_produto_router)


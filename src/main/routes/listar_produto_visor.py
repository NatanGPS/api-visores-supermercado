from fastapi import APIRouter, HTTPException, status

from src.main.validators.listar_produto_visor_validators import (
    ListarProdutoVisorValidators,
)
from src.models.repository.database import (
    buscar_empresa_por_id_empresa,
    buscar_painel_por_id_e_empresa,
    buscar_produtos_do_painel,
)

router = APIRouter(prefix="/listar-produto-visor", tags=["Listar Produto Visor"])


@router.post("", status_code=status.HTTP_200_OK)
def listar_produto_visor(dados: ListarProdutoVisorValidators):
    """Lista os produtos que estão dentro de um visor da loja, na ordem do visor.

    Visor vazio devolve 200 com lista vazia; 404 fica reservado para loja ou
    visor que não existem.
    """
    # 1. Traduz o id externo da loja para o id interno (UUID) antes de qualquer busca
    empresa = buscar_empresa_por_id_empresa(dados.empresa_id)
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada para o identificador externo informado.",
        )

    empresa_id_interna = empresa[0]["id"]

    # 2. Mesma regra das outras rotas: visor desta loja e de preço (fnc_pnl 00/01)
    painel = buscar_painel_por_id_e_empresa(dados.painel_id, empresa_id_interna)
    if not painel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Visor não encontrado para esta empresa, ou não é painel de preço "
                "(fnc_pnl deve ser '00' ou '01')."
            ),
        )

    produtos = buscar_produtos_do_painel(dados.painel_id)

    return {
        "message": "Produtos do visor listados com sucesso.",
        "empresa": empresa[0],
        "painel": {
            "id": painel[0]["id"],
            "nme_pnl": painel[0]["nme_pnl"],
            "nip_pnl": painel[0]["nip_pnl"],
            "fnc_pnl": painel[0]["fnc_pnl"],
        },
        "total": len(produtos),
        "produtos": produtos,
    }

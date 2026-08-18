from fastapi import APIRouter, HTTPException, status

from src.main.validators.listar_produtos_validators import ListarProdutosValidators
from src.models.repository.database import (
    buscar_empresa_por_id_empresa,
    buscar_produtos_por_empresa_id,
)

router = APIRouter(prefix="/listar-produtos", tags=["Listar Produtos"])


@router.post("", status_code=status.HTTP_200_OK)
def listar_produtos(dados: ListarProdutosValidators):
    """Listar produtos de uma loja.

    No Swagger a requisição mostrará os campos do modelo e um exemplo, basta
    inserir os valores correspondentes e executar.
    """
    empresa = buscar_empresa_por_id_empresa(dados.loja_id)
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loja/empresa não encontrada para o id informado.",
        )

    # Obtemos o id interno da empresa a partir do resultado (codigo_externo -> id)
    empresa_id_interna = empresa[0]["id"]

    produtos = buscar_produtos_por_empresa_id(
        empresa_id_interna,
        dados.limite,
        dados.offset,
        dados.rfc_prd,
    )

    return {
        "message": "Produtos listados com sucesso.",
        "loja_id": dados.loja_id,
        "empresa": empresa[0],
        "filtro_rfc_prd": dados.rfc_prd,
        "produtos": produtos,
        "limite": dados.limite,
        "offset": dados.offset,
    }

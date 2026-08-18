from pydantic import AliasChoices, BaseModel, Field

from src.main.validators.produto_painel_validators import UUID_PATTERN

# Classe de validação para o endpoint de listar produtos do visor.
class ListarProdutoVisorValidators(BaseModel):
    """Payload para listar os produtos que estão num visor de uma loja."""
    empresa_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Código externo da empresa usado para buscar o id interno",
        validation_alias=AliasChoices("empresa_id", "loja_id", "empresa", "loja"),
    )
    # Inicialmente o endpoint de listar produtos do visor não precisa de ord_pdp, mas se no futuro for necessário, podemos adicionar aqui.
    painel_id: str = Field(
        ...,
        pattern=UUID_PATTERN,
        description="UUID do visor/painel (painel.id)",
        validation_alias=AliasChoices("painel_id", "visor_id", "visor", "painel"),
    )

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "empresa_id": "289",
                "painel_id": "0ee3af3a-b599-4295-968f-3cfd24cad63e",
            }
        },
    }

# Define as funções de validação para o endpoint de listar produtos do visor.
def validar_listar_produto_visor(payload: dict) -> ListarProdutoVisorValidators:
    return ListarProdutoVisorValidators.model_validate(payload)

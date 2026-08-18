from pydantic import AliasChoices, BaseModel, Field


class ListarProdutosValidators(BaseModel):
    loja_id: str = Field(
        ..., min_length=1, description="Código externo da loja/empresa (aceita 'loja_id' ou 'empresa_id')",
        validation_alias=AliasChoices("loja_id", "empresa_id"),
    )
    rfc_prd: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="RFC do produto para filtrar a listagem (opcional)",
    )
    limite: int = Field(default=50, ge=1, le=100, description="Número máximo de registros a retornar")
    offset: int = Field(default=0, ge=0, description="Offset para paginação")

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "loja_id": 123,
                "rfc_prd": "208210|AUTO SERVICO|2",
                "limite": 50,
                "offset": 0,
            }
        },
    }


# Validator que foi configurado anteriormente nas demais rotas, para manter consistencia e validação de dados
def validar_listar_produtos(payload: dict | None = None) -> ListarProdutosValidators:
    if payload is None:
        payload = {}
    return ListarProdutosValidators.model_validate(payload)

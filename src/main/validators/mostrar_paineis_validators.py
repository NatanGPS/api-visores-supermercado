from pydantic import AliasChoices, BaseModel, Field


class MostrarPaineisValidators(BaseModel):
    empresa: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Código externo da empresa (aceita 'empresa' ou 'loja_id')",
        validation_alias=AliasChoices("empresa", "loja_id"),
    )

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {"example": {"empresa": "266"}},
    }

# Mostrar paineis de uma empresa. A validação é simples, só precisa do id externo da loja.
def validar_mostrar_paineis(payload: dict) -> MostrarPaineisValidators:
    return MostrarPaineisValidators.model_validate(payload)

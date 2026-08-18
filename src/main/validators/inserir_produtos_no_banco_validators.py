from src.main.validators.produto_painel_validators import ProdutoPainelPayload


class InserirProdutosNoBancoValidators(ProdutoPainelPayload):
    """Payload para vincular um ou mais produtos a um painel.

    Formato idêntico ao da remoção (ver `ProdutoPainelPayload`): aqui o `ord_pdp`
    de cada item é a posição que o produto vai passar a ocupar, e ela precisa
    estar livre no painel.
    """

    # Exemplo com posições livres, que é o que a inserção exige
    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "empresa_id": "289",
                "painel_id": "0ee3af3a-b599-4295-968f-3cfd24cad63e",
                "produtos": [
                    {"produto_id": "29733252-57ce-49f8-9783-fc89cb6aa064", "ord_pdp": 73},
                    {"produto_id": "533ec608-9ceb-4510-a482-9615c95973a4", "ord_pdp": 74},
                ],
            }
        },
    }


# Vaidator que foi configurado anteriormente
def validar_inserir_produtos_no_banco(payload: dict) -> InserirProdutosNoBancoValidators:
    return InserirProdutosNoBancoValidators.model_validate(payload)

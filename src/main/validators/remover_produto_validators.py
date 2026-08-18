from src.main.validators.produto_painel_validators import ProdutoPainelPayload


class RemoverProdutoValidators(ProdutoPainelPayload):
    """Payload para desvincular um ou mais produtos de um painel.

    Formato idêntico ao da inserção (ver `ProdutoPainelPayload`): aqui o `ord_pdp`
    de cada item é a posição que o produto ocupa hoje, e ela precisa conferir com
    o que está gravado — se divergir, a remoção é barrada.
    """


def validar_remover_produto(payload: dict) -> RemoverProdutoValidators:
    return RemoverProdutoValidators.model_validate(payload)

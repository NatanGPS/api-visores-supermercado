"""Contrato de payload compartilhado pelas rotas que mexem em `produto_painel`.

Inserir e remover recebem exatamente o mesmo corpo: a loja, o painel e a lista de
produtos com a posição de cada um. O que muda é o que cada rota faz com isso, então
o formato mora aqui e as duas herdam.
"""
# Importações
from pydantic import AliasChoices, BaseModel, Field, model_validator

# Todos os ids do banco são UUID canônico de 36 caracteres (validado em produtos,
# painel e produto_painel). Aceita maiúsculas porque a comparação no MySQL é
# case-insensitive na collation em uso.
UUID_PATTERN = (
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

# ord_pdp é int(11) com sinal no banco
ORD_PDP_MAXIMO = 2147483647

# Teto de itens por requisição, para não deixar um lote absurdo abrir transação gigante
MAXIMO_PRODUTOS_POR_LOTE = 500

EXEMPLO_PAYLOAD = {
    "empresa_id": "289",
    "painel_id": "0ee3af3a-b599-4295-968f-3cfd24cad63e",
    "produtos": [
        {"produto_id": "29733252-57ce-49f8-9783-fc89cb6aa064", "ord_pdp": 1},
        {"produto_id": "533ec608-9ceb-4510-a482-9615c95973a4", "ord_pdp": 2},
    ],
}


class ProdutoPainelItem(BaseModel):
    """Um produto e a posição que ele ocupa (ou vai ocupar) no painel."""

    produto_id: str = Field(
        ...,
        pattern=UUID_PATTERN,
        description="UUID do produto (produtos.id)",
    )
    ord_pdp: int = Field(
        ...,
        ge=1,
        le=ORD_PDP_MAXIMO,
        description="Posição do produto dentro do painel; única por painel",
    )

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {"produto_id": "29733252-57ce-49f8-9783-fc89cb6aa064", "ord_pdp": 1}
        },
    }


class ProdutoPainelPayload(BaseModel):
    """Loja + painel + produtos. Pedido unitário é uma lista com um único item."""

    empresa_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Código externo da empresa usado para buscar o id interno",
        validation_alias=AliasChoices("empresa_id", "loja_id", "empresa"),
    )
    painel_id: str = Field(
        ...,
        pattern=UUID_PATTERN,
        description="UUID do painel (painel.id)",
    )
    produtos: list[ProdutoPainelItem] = Field(
        ...,
        min_length=1,
        max_length=MAXIMO_PRODUTOS_POR_LOTE,
        description="Produtos do pedido; um item para unitário, vários para lote",
    )

    @model_validator(mode="after")
    def _sem_repetidos_no_payload(self) -> "ProdutoPainelPayload":
        """Barra repetição dentro da própria requisição.

        O banco não tem constraint única nem para (produto_id, painel_id) nem para
        (painel_id, ord_pdp), então um payload com o mesmo produto duas vezes
        passaria batido.
        """
        ids_vistos: set[str] = set()
        ids_repetidos: set[str] = set()
        ords_vistos: set[int] = set()
        ords_repetidos: set[int] = set()

        for item in self.produtos:
            chave = item.produto_id.lower()
            if chave in ids_vistos:
                ids_repetidos.add(chave)
            ids_vistos.add(chave)

            if item.ord_pdp in ords_vistos:
                ords_repetidos.add(item.ord_pdp)
            ords_vistos.add(item.ord_pdp)

        if ids_repetidos:
            raise ValueError(f"produto_id repetido no payload: {sorted(ids_repetidos)}")
        if ords_repetidos:
            raise ValueError(f"ord_pdp repetido no payload: {sorted(ords_repetidos)}")

        return self
# Poderiamos configurar o modelo de formas diferentes, mas aqui é mais simples e direto. A validação de repetidos é feita
    model_config = {
        "extra": "forbid",
        "json_schema_extra": {"example": EXEMPLO_PAYLOAD},
    }

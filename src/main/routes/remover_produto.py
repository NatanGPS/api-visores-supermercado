from fastapi import APIRouter, HTTPException, status

from src.main.validators.remover_produto_validators import RemoverProdutoValidators
from src.models.repository.database import (
    buscar_empresa_por_id_empresa,
    buscar_painel_por_id_e_empresa,
    buscar_vinculos_no_painel,
    remover_vinculos_do_painel,
)

router = APIRouter(prefix="/remover-produto", tags=["Remover Produto"])


@router.post("", status_code=status.HTTP_200_OK)
def remover_produto(dados: RemoverProdutoValidators):
    """Desvincula um ou mais produtos de um painel, apagando de `produto_painel`.

    É o inverso do `/inserir-produtos-no-banco` e recebe o mesmo payload. O
    produto continua existindo no cadastro; só sai do visor. Cada `ord_pdp`
    enviado precisa conferir com a posição gravada — se divergir, nada é
    removido, para um payload desatualizado não apagar a linha errada.
    """


    # 1. Traduz o id externo da loja para o id interno (UUID) antes de qualquer busca
    empresa = buscar_empresa_por_id_empresa(dados.empresa_id)
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada para o identificador externo informado.",
        )
# Declarando a variavel responsável por armazenar o id interno da empresa, que será usado para buscar o painel e os produtos.
    empresa_id_interna = empresa[0]["id"]

    # 2. Mesma regra do insert: painel desta loja e de preço (fnc_pnl 00/01)
    painel = buscar_painel_por_id_e_empresa(dados.painel_id, empresa_id_interna)
    if not painel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Painel não encontrado para esta empresa, ou não é painel de preço "
                "(fnc_pnl deve ser '00' ou '01')."
            ),
        )

    produto_ids = [item.produto_id for item in dados.produtos]
    ord_pedido_por_produto = {
        item.produto_id.lower(): item.ord_pdp for item in dados.produtos
    }

    #---#
    #---#
    #---#

    # 3. Resolve os vínculos que existem hoje neste painel
    vinculos_atuais = buscar_vinculos_no_painel(dados.painel_id, produto_ids)
    vinculo_por_produto = {v["produto_id"].lower(): v for v in vinculos_atuais}


    # 4. Conflitos: produto que não está no painel, ou está em outra posição
    conflitos = []
    alvos = []

    for produto_id in produto_ids:
        chave = produto_id.lower()
        vinculo = vinculo_por_produto.get(chave)

        if vinculo is None:
            conflitos.append(
                {
                    "motivo": "produto não está vinculado a este painel",
                    "produto_id": produto_id,
                }
            )
            continue

        ord_enviado = ord_pedido_por_produto[chave]
        if vinculo["ord_pdp"] != ord_enviado:
            conflitos.append(
                {
                    "motivo": "ord_pdp divergente do gravado",
                    "produto_id": produto_id,
                    "ord_pdp_enviado": ord_enviado,
                    "ord_pdp_atual": vinculo["ord_pdp"],
                }
            )
            continue
# Quais são os nosso níveis principais
        alvos.append(
            {
                "id": vinculo["id"],
                "produto_id": vinculo["produto_id"],
                "ord_pdp": vinculo["ord_pdp"],
            }
        )

    if conflitos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Conflitos impedem a remoção; nada foi removido.",
                "painel_id": dados.painel_id,
                "conflitos": conflitos,
            },
        )

    # 5. Nenhum conflito: apaga o lote inteiro numa única transação
    linhas_removidas = remover_vinculos_do_painel(
        dados.painel_id,
        [alvo["id"] for alvo in alvos],
    )

    return {
        "message": "Produtos desvinculados do painel com sucesso.",
        "empresa": empresa[0],
        "painel": {
            "id": painel[0]["id"],
            "nme_pnl": painel[0]["nme_pnl"],
            "fnc_pnl": painel[0]["fnc_pnl"],
        },
        "total_removido": linhas_removidas,
        "vinculos_removidos": alvos,
    }

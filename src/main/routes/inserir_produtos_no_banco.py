from fastapi import APIRouter, HTTPException, status

from src.main.validators.inserir_produtos_no_banco_validators import (
    InserirProdutosNoBancoValidators,
)
from src.models.repository.database import (
    buscar_empresa_por_id_empresa,
    buscar_maior_ord_no_painel,
    buscar_ords_ocupados_no_painel,
    buscar_painel_por_id_e_empresa,
    buscar_produtos_por_ids,
    buscar_vinculos_no_painel,
    inserir_produtos_no_painel,
)

router = APIRouter(prefix="/inserir-produtos-no-banco", tags=["Inserir Produtos no Banco"])


@router.post("", status_code=status.HTTP_201_CREATED)
def inserir_produtos_no_banco(dados: InserirProdutosNoBancoValidators):
    """Vincula um ou mais produtos a um painel, gravando em `produto_painel`.

    Aceita pedido unitário (lista `produtos` com um item) ou em lote. A inserção
    é tudo ou nada: qualquer conflito barra a requisição inteira antes de
    escrever, e uma falha no meio do lote faz rollback de todas as linhas.
    """
    # 1. Traduz o id externo da loja para o id interno (UUID) antes de qualquer busca
    empresa = buscar_empresa_por_id_empresa(dados.empresa_id)
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada para o identificador externo informado.",
        )

    empresa_id_interna = empresa[0]["id"]

    # 2. O painel precisa existir E pertencer a esta loja
    painel = buscar_painel_por_id_e_empresa(dados.painel_id, empresa_id_interna)
    if not painel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Painel não encontrado para esta empresa.",
        )

    produto_ids = [item.produto_id for item in dados.produtos]
    ords_pedidos = [item.ord_pdp for item in dados.produtos]

    # 3. Todos os produtos precisam existir e ser da mesma loja do painel.
    #    Nos dados atuais nenhum vínculo cruza empresas, então mantemos a regra.
    encontrados = buscar_produtos_por_ids(produto_ids)
    por_id = {produto["id"].lower(): produto for produto in encontrados}

    inexistentes = [pid for pid in produto_ids if pid.lower() not in por_id]
    de_outra_empresa = [
        pid
        for pid in produto_ids
        if pid.lower() in por_id and por_id[pid.lower()]["empresa_id"] != empresa_id_interna
    ]

    if inexistentes or de_outra_empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Produtos inválidos para esta empresa.",
                "produtos_inexistentes": inexistentes,
                "produtos_de_outra_empresa": de_outra_empresa,
            },
        )

    # 4. Conflitos com o que já está no painel. O banco não tem constraint única
    #    para nenhum dos dois casos, então a checagem tem que ser feita aqui.
    conflitos = []

    for vinculo in buscar_vinculos_no_painel(dados.painel_id, produto_ids):
        conflitos.append(
            {
                "motivo": "produto já está vinculado a este painel",
                "produto_id": vinculo["produto_id"],
                "ord_pdp_atual": vinculo["ord_pdp"],
            }
        )


    for ocupado in buscar_ords_ocupados_no_painel(dados.painel_id, ords_pedidos):
        conflitos.append(
            {
                "motivo": "ord_pdp já ocupado neste painel",
                "ord_pdp": ocupado["ord_pdp"],
                "produto_id_ocupante": ocupado["produto_id"],
            }
        )
# /
# /
    if conflitos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Conflitos impedem a inserção; nada foi gravado.",
                "painel_id": dados.painel_id,
                "proximo_ord_pdp_livre": buscar_maior_ord_no_painel(dados.painel_id) + 1,
                "conflitos": conflitos,
            },
        )

    # 5. Nenhum conflito: grava o lote inteiro numa única transação
    linhas = inserir_produtos_no_painel(
        dados.painel_id,
        [{"produto_id": item.produto_id, "ord_pdp": item.ord_pdp} for item in dados.produtos],
    )

    vinculos = [
        {
            "id": linha["id"],
            "produto_id": linha["produto_id"],
            "dsc_prd": por_id[linha["produto_id"].lower()]["DSC_PRD"],
            "ord_pdp": linha["ord_pdp"],
        }
        for linha in linhas
    ]
# 6. Retorna o resultado da inserção, incluindo a lista de vinculos criados
    return {
        "message": "Produtos vinculados ao painel com sucesso.",
        "empresa": empresa[0],
        "painel": {
            "id": painel[0]["id"],
            "nme_pnl": painel[0]["nme_pnl"],
            "fnc_pnl": painel[0]["fnc_pnl"],
        },
        "total_inserido": len(vinculos),
        "vinculos": vinculos,
    }

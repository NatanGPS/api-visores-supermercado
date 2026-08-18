import os
import uuid
from typing import Any

from dotenv import load_dotenv
from fastapi import HTTPException, status
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote_plus

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

if not all([DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME]):
    raise RuntimeError("Configurações de banco ausentes no .env")

_pw_escaped = quote_plus(DB_PASSWORD)
engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{_pw_escaped}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    echo=False,
    future=True,
)


def executar_select(query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), params or {})
            return [dict(row._mapping) for row in result.fetchall()]
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro ao conectar no banco de dados: {e}",
        )


def executar_insert_em_lote(query: str, lista_params: list[dict[str, Any]]) -> int:
    """Insere várias linhas numa única transação (tudo ou nada).

    Se qualquer linha falhar, o `engine.begin()` faz rollback de todas — nunca
    fica um lote inserido pela metade.
    """
    if not lista_params:
        return 0
    try:
        with engine.begin() as connection:
            result = connection.execute(text(query), lista_params)
            return result.rowcount
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro ao inserir no banco de dados: {e}",
        )


def _placeholders_nomeados(prefixo: str, valores: list[Any]) -> tuple[str, dict[str, Any]]:
    """Monta placeholders nomeados (:pref_0, :pref_1, ...) para uma cláusula IN.

    Mantém os valores como parâmetros ligados, sem interpolar nada na query.
    """
    nomes = [f"{prefixo}_{indice}" for indice in range(len(valores))]
    marcadores = ", ".join(f":{nome}" for nome in nomes)
    return marcadores, dict(zip(nomes, valores))


def buscar_empresa_por_id_empresa(empresa_id: str) -> list[dict[str, Any]]:
    query = """
    SELECT id, codigo_externo
    FROM empresas
    WHERE codigo_externo = :codigo_externo
    LIMIT 1
    """
    return executar_select(query, {"codigo_externo": empresa_id})


def buscar_produtos_por_empresa_id(
    empresa_id: int,
    limite: int,
    offset: int,
    rfc_prd: str | None = None,
) -> list[dict[str, Any]]:
    query = """
    SELECT id, empresa_id, rfc_prd, dsc_prd, unm_prd
    FROM produtos
    WHERE empresa_id = :empresa_id
    """
    params: dict[str, Any] = {"empresa_id": empresa_id}

    if rfc_prd:
        query += "\n      AND rfc_prd = :rfc_prd"
        params["rfc_prd"] = rfc_prd

    query += "\n    ORDER BY id ASC\n    LIMIT :limite OFFSET :offset"
    params.update({"limite": limite, "offset": offset})

    return executar_select(query, params)


def buscar_paineis_por_empresa_id(empresa_id: str) -> list[dict[str, Any]]:
    query = """
    SELECT id, nme_pnl, nip_pnl, fnc_pnl
    FROM painel
    WHERE empresa_id = :empresa_id
      AND fnc_pnl IN ('00', '01')
    ORDER BY nme_pnl ASC, id ASC
    """
    return executar_select(query, {"empresa_id": empresa_id})


def buscar_produto_por_rfc_e_empresa(empresa_id: int, rfc_prd: str) -> list[dict[str, Any]]:
    query = """
    SELECT id, empresa_id, rfc_prd, dsc_prd, unm_prd
    FROM produtos
    WHERE empresa_id = :empresa_id
      AND rfc_prd = :rfc_prd
    LIMIT 1
    """
    return executar_select(query, {"empresa_id": empresa_id, "rfc_prd": rfc_prd})


def buscar_painel_por_id_e_empresa(painel_id: str, empresa_id: str) -> list[dict[str, Any]]:
    """Confirma que o painel existe, pertence à empresa E é painel de preço.

    O filtro `fnc_pnl IN ('00', '01')` é o mesmo de `buscar_paineis_por_empresa_id`:
    só entram painéis que o `mostrar_paineis` expõe ao cliente. Painel de outra
    função (02, 08, NULL) não é aceito para receber produtos.
    """
    query = """
    SELECT id, nme_pnl, nip_pnl, fnc_pnl, empresa_id
    FROM painel
    WHERE id = :painel_id
      AND empresa_id = :empresa_id
      AND fnc_pnl IN ('00', '01')
    LIMIT 1
    """
    return executar_select(query, {"painel_id": painel_id, "empresa_id": empresa_id})


def buscar_produtos_por_ids(produto_ids: list[str]) -> list[dict[str, Any]]:
    """Busca produtos por uma lista de UUIDs, trazendo o empresa_id de cada um.

    Não filtra por empresa de propósito: a rota compara o `empresa_id` retornado
    para distinguir "produto não existe" de "produto é de outra loja".
    """
    if not produto_ids:
        return []
    marcadores, params = _placeholders_nomeados("pid", produto_ids)
    query = f"""
    SELECT id, empresa_id, DSC_PRD, UNM_PRD
    FROM produtos
    WHERE id IN ({marcadores})
    """
    return executar_select(query, params)


def buscar_produtos_do_painel(painel_id: str) -> list[dict[str, Any]]:
    """Lista os produtos que estão num painel, na ordem em que aparecem no visor.

    `vinculo_id` e `ord_pdp` vêm juntos de propósito: são o que o cliente precisa
    devolver para o `/remover-produto` desvincular um item.
    """
    query = """
    SELECT
        pp.id AS vinculo_id,
        pp.ord_pdp,
        pr.id AS produto_id,
        pr.RFC_PRD AS rfc_prd,
        pr.DSC_PRD AS dsc_prd,
        pr.UNM_PRD AS unm_prd,
        pr.legenda_forma_venda,
        pr.esconder_produto
    FROM produto_painel pp
    JOIN produtos pr ON pr.id = pp.produto_id
    WHERE pp.painel_id = :painel_id
    ORDER BY pp.ord_pdp ASC
    """
    return executar_select(query, {"painel_id": painel_id})


def buscar_vinculos_no_painel(painel_id: str, produto_ids: list[str]) -> list[dict[str, Any]]:
    """Retorna os produtos da lista que JÁ estão vinculados a este painel."""
    if not produto_ids:
        return []
    marcadores, params = _placeholders_nomeados("pid", produto_ids)
    query = f"""
    SELECT id, produto_id, ord_pdp
    FROM produto_painel
    WHERE painel_id = :painel_id
      AND produto_id IN ({marcadores})
    """
    params["painel_id"] = painel_id
    return executar_select(query, params)


def buscar_ords_ocupados_no_painel(painel_id: str, ords: list[int]) -> list[dict[str, Any]]:
    """Retorna quais `ord_pdp` da lista já estão ocupados neste painel."""
    if not ords:
        return []
    marcadores, params = _placeholders_nomeados("ord", ords)
    query = f"""
    SELECT id, produto_id, ord_pdp
    FROM produto_painel
    WHERE painel_id = :painel_id
      AND ord_pdp IN ({marcadores})
    """
    params["painel_id"] = painel_id
    return executar_select(query, params)


def buscar_maior_ord_no_painel(painel_id: str) -> int:
    """Maior `ord_pdp` já usado no painel (0 se o painel estiver vazio).

    Serve para informar ao cliente a próxima posição livre.
    """
    query = """
    SELECT COALESCE(MAX(ord_pdp), 0) AS maior_ord
    FROM produto_painel
    WHERE painel_id = :painel_id
    """
    resultado = executar_select(query, {"painel_id": painel_id})
    return int(resultado[0]["maior_ord"]) if resultado else 0


def inserir_produtos_no_painel(
    painel_id: str,
    itens: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Vincula produtos a um painel em `produto_painel`, tudo ou nada.

    `produto_painel.id` é PK varchar(38) sem default e sem auto_increment no
    banco, então o UUID de cada vínculo é gerado aqui na aplicação.

    Cada item de `itens` deve ter as chaves `produto_id` e `ord_pdp`.
    Retorna as linhas efetivamente gravadas, já com o `id` gerado.
    """
    linhas = [
        {
            "id": str(uuid.uuid4()),
            "produto_id": item["produto_id"],
            "painel_id": painel_id,
            "ord_pdp": item["ord_pdp"],
        }
        for item in itens
    ]

    query = """
    INSERT INTO produto_painel (
        id,
        produto_id,
        painel_id,
        ord_pdp
    ) VALUES (
        :id,
        :produto_id,
        :painel_id,
        :ord_pdp
    )
    """
    linhas_inseridas = executar_insert_em_lote(query, linhas)

    if linhas_inseridas != len(linhas):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Inserção inconsistente: {linhas_inseridas} linhas gravadas "
                f"para {len(linhas)} produtos enviados."
            ),
        )

    return linhas


def remover_vinculos_do_painel(painel_id: str, vinculo_ids: list[str]) -> int:
    """Remove vínculos de `produto_painel` pelos ids (PK), tudo ou nada.

    Deleta por PK porque a rota já resolveu exatamente quais linhas remover; o
    `painel_id` no WHERE é defesa extra para nunca alcançar outro painel.

    A conferência de linhas afetadas acontece DENTRO da transação de propósito:
    levantar ali faz o `engine.begin()` dar rollback, então uma contagem
    inesperada não deixa remoção parcial gravada.
    """

    
    if not vinculo_ids:
        return 0

    marcadores, params = _placeholders_nomeados("vid", vinculo_ids)
    params["painel_id"] = painel_id

    query = f"""
    DELETE FROM produto_painel
    WHERE painel_id = :painel_id
      AND id IN ({marcadores})
    """

    try:
        with engine.begin() as connection:
            resultado = connection.execute(text(query), params)
            if resultado.rowcount != len(vinculo_ids):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=(
                        f"Remoção inconsistente: {resultado.rowcount} linhas afetadas "
                        f"para {len(vinculo_ids)} vínculos selecionados; "
                        "a transação foi desfeita e nada foi removido."
                    ),
                )
            return resultado.rowcount
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Erro ao remover do banco de dados: {e}",
        )

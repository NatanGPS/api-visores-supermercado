from fastapi import APIRouter, HTTPException, status

from src.main.validators.mostrar_paineis_validators import MostrarPaineisValidators
from src.models.repository.database import (
    buscar_empresa_por_id_empresa,
    buscar_paineis_por_empresa_id,
)

router = APIRouter(prefix="/mostrar-paineis", tags=["Mostrar Paineis"])

# Tradução dos códigos de função do painel para um texto legível ao cliente
TIPOS_PAINEL = {
    "00": "Vídeo com preço",
    "01": "Preço",
}


@router.post("", status_code=status.HTTP_200_OK)
def mostrar_paineis(dados: MostrarPaineisValidators):
    """Retorna os paineis da empresa filtrando `fnc_pnl` em '00' ou '01'."""
    empresa = buscar_empresa_por_id_empresa(dados.empresa)
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada para o identificador informado.",
        )

    empresa_id_interna = empresa[0]["id"]

    paineis = buscar_paineis_por_empresa_id(empresa_id_interna)

    resultado = []
    for p in paineis:
        fnc = p.get("fnc_pnl")
        resultado.append(
            {
                "id": p.get("id"),
                "nme_pnl": p.get("nme_pnl"),
                "nip_pnl": p.get("nip_pnl"),
                "fnc_pnl": fnc,
                # A query já restringe a '00'/'01'; o fallback fica como defesa
                "tipo": TIPOS_PAINEL.get(fnc, "Desconhecido"),
            }
        )

    return {
        "message": "Paineis listados com sucesso.",
        "empresa": empresa[0],
        "total": len(resultado),
        "paineis": resultado,
    }

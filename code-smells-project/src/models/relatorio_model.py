from src.config.constants import FAIXAS_DESCONTO
from src.database.connection import get_db


def calcular_desconto(faturamento):
    for minimo, percentual in FAIXAS_DESCONTO:
        if faturamento > minimo:
            return faturamento * percentual
    return 0


def relatorio_vendas():
    rows = get_db().execute(
        "SELECT status, COUNT(*) AS qtd, COALESCE(SUM(total), 0) AS soma FROM pedidos GROUP BY status"
    ).fetchall()
    por_status = {row["status"]: row["qtd"] for row in rows}
    total_pedidos = sum(row["qtd"] for row in rows)
    faturamento = sum(row["soma"] for row in rows)
    desconto = calcular_desconto(faturamento)

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": por_status.get("pendente", 0),
        "pedidos_aprovados": por_status.get("aprovado", 0),
        "pedidos_cancelados": por_status.get("cancelado", 0),
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }

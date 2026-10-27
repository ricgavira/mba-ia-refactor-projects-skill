import logging

logger = logging.getLogger(__name__)


def pedido_criado(pedido_id, usuario_id):
    """Integrações de e-mail/SMS/push ainda são simuladas por log."""
    logger.info("ENVIANDO EMAIL: Pedido %s criado para usuario %s", pedido_id, usuario_id)
    logger.info("ENVIANDO SMS: Seu pedido foi recebido!")
    logger.info("ENVIANDO PUSH: Novo pedido recebido pelo sistema")


def status_pedido_alterado(pedido_id, novo_status):
    if novo_status == "aprovado":
        logger.info("NOTIFICAÇÃO: Pedido %s foi aprovado! Preparar envio.", pedido_id)
    elif novo_status == "cancelado":
        logger.info("NOTIFICAÇÃO: Pedido %s cancelado. Devolver estoque.", pedido_id)

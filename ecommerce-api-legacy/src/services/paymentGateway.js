const { PAYMENT_STATUS, APPROVED_CARD_PREFIX } = require('../config/constants');

const maskCard = (cardNumber) => `**** **** **** ${cardNumber.slice(-4)}`;

/**
 * Gateway de pagamento simulado. `apiKey` fica reservada para a integração real
 * e nunca é logada.
 */
function createPaymentGateway({ apiKey, logger }) {
    return {
        charge(cardNumber, amount) {
            logger.info(`Processando cartão ${maskCard(cardNumber)} no valor de ${amount}`);
            const status = cardNumber.startsWith(APPROVED_CARD_PREFIX)
                ? PAYMENT_STATUS.PAID
                : PAYMENT_STATUS.DENIED;
            return { status };
        },
    };
}

module.exports = { createPaymentGateway };

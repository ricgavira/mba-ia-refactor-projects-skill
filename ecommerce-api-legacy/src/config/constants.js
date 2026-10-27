module.exports = {
    PAYMENT_STATUS: Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' }),
    // Regra do gateway simulado: cartões iniciados em "4" são aprovados.
    APPROVED_CARD_PREFIX: '4',
    EMAIL_PATTERN: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    UNKNOWN_STUDENT: 'Unknown',
};

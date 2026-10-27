const crypto = require('crypto');
const { ForbiddenError } = require('../errors');

/**
 * Proteção opt-in das rotas administrativas: se `adminToken` estiver configurado,
 * exige o header X-Admin-Token; sem token configurado a rota segue aberta (o boot avisa).
 */
function createAdminAuth({ adminToken }) {
    return function requireAdminToken(req, res, next) {
        if (!adminToken) return next();

        const received = Buffer.from(req.get('X-Admin-Token') || '');
        const expected = Buffer.from(adminToken);
        const valid = received.length === expected.length && crypto.timingSafeEqual(received, expected);
        return valid ? next() : next(new ForbiddenError('Acesso negado'));
    };
}

module.exports = { createAdminAuth };

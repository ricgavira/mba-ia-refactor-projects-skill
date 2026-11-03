const crypto = require('crypto');
const { ForbiddenError, UnauthorizedError } = require('../errors');

/**
 * Proteção das rotas administrativas/destrutivas (falha fechada).
 * A API não tem sistema de login, então o acesso é por token de serviço:
 *  - sem ADMIN_TOKEN configurado: rotas desabilitadas (403);
 *  - sem header X-Admin-Token: 401; token incorreto: 403.
 */
function createAdminAuth({ adminToken }) {
    return function requireAdminToken(req, res, next) {
        if (!adminToken) {
            return next(new ForbiddenError('Rotas administrativas desabilitadas: configure ADMIN_TOKEN'));
        }

        const header = req.get('X-Admin-Token');
        if (!header) return next(new UnauthorizedError('Autenticação necessária'));

        const received = Buffer.from(header);
        const expected = Buffer.from(adminToken);
        const valid = received.length === expected.length && crypto.timingSafeEqual(received, expected);
        return valid ? next() : next(new ForbiddenError('Acesso negado'));
    };
}

module.exports = { createAdminAuth };

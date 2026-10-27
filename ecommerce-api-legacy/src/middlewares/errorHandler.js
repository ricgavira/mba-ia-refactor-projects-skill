const logger = require('../utils/logger');

function notFoundHandler(req, res) {
    res.status(404).json({ error: 'Rota não encontrada' });
}

// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, next) {
    const status = err.statusCode || err.status || 500;
    if (status >= 500) {
        logger.error(err); // detalhe apenas no log
        return res.status(500).json({ error: 'Erro interno do servidor' });
    }
    return res.status(status).json({ error: err.message });
}

module.exports = { errorHandler, notFoundHandler };

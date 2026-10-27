// Encaminha rejeições de handlers async para o errorHandler do Express.
module.exports = (handler) => (req, res, next) =>
    Promise.resolve(handler(req, res, next)).catch(next);

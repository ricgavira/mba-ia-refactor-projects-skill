// Erros de domínio: controllers/services lançam, o errorHandler converte em resposta HTTP.
class AppError extends Error {
    constructor(message, statusCode = 500) {
        super(message);
        this.name = this.constructor.name;
        this.statusCode = statusCode;
    }
}

class ValidationError extends AppError {
    constructor(message) { super(message, 400); }
}

class ForbiddenError extends AppError {
    constructor(message) { super(message, 403); }
}

class NotFoundError extends AppError {
    constructor(message) { super(message, 404); }
}

module.exports = { AppError, ValidationError, ForbiddenError, NotFoundError };

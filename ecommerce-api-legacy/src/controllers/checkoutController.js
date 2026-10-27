const { EMAIL_PATTERN } = require('../config/constants');
const { ValidationError } = require('../errors');

const isNonEmptyString = (value) => typeof value === 'string' && value.trim() !== '';

function createCheckoutController({ checkoutService }) {
    return {
        async checkout(req, res) {
            // O contrato HTTP mantém usr/eml/pwd/c_id/card; internamente usamos nomes claros.
            const { usr: name, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body || {};

            if (!isNonEmptyString(name) || !isNonEmptyString(email) || !courseId || !isNonEmptyString(cardNumber)) {
                throw new ValidationError('Bad Request');
            }
            if (!EMAIL_PATTERN.test(email)) throw new ValidationError('E-mail inválido');
            if (password !== undefined && !isNonEmptyString(password)) throw new ValidationError('Senha inválida');

            const { enrollmentId } = await checkoutService.checkout({ name, email, password, courseId, cardNumber });
            res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
        },
    };
}

module.exports = { createCheckoutController };

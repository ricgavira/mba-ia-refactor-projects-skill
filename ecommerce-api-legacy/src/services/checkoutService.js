const { PAYMENT_STATUS } = require('../config/constants');
const { AppError, NotFoundError, ValidationError } = require('../errors');

/**
 * Fluxo de checkout: valida curso → decide o pagamento → grava tudo em uma transação.
 * O usuário só é criado se o pagamento for aprovado (sem usuários órfãos).
 */
function createCheckoutService({ db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel,
    paymentGateway, passwordHasher, logger }) {
    return {
        async checkout({ name, email, password, courseId, cardNumber }) {
            const course = await courseModel.findActiveById(courseId);
            if (!course) throw new NotFoundError('Curso não encontrado');

            const existingUser = await userModel.findByEmail(email);
            if (!existingUser && !password) {
                throw new ValidationError('Senha é obrigatória para novos usuários');
            }

            const payment = paymentGateway.charge(cardNumber, course.price);
            if (payment.status === PAYMENT_STATUS.DENIED) throw new AppError('Pagamento recusado', 400);

            const passwordHash = existingUser ? null : await passwordHasher.hash(password);

            const { userId, enrollmentId } = await db.transaction(async (tx) => {
                const id = existingUser
                    ? existingUser.id
                    : await userModel.create({ name, email, passwordHash }, tx);
                const enrId = await enrollmentModel.create({ userId: id, courseId }, tx);
                await paymentModel.create({ enrollmentId: enrId, amount: course.price, status: payment.status }, tx);
                await auditLogModel.record(`Checkout curso ${courseId} por ${id}`, tx);
                return { userId: id, enrollmentId: enrId };
            });

            logger.info(`Checkout concluído: curso "${course.title}" para usuário ${userId}`);
            return { enrollmentId };
        },
    };
}

module.exports = { createCheckoutService };

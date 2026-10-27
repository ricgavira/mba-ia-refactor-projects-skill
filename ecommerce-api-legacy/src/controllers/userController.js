const { NotFoundError, ValidationError } = require('../errors');

function createUserController({ userModel }) {
    return {
        async remove(req, res) {
            const userId = Number(req.params.id);
            if (!Number.isInteger(userId) || userId <= 0) throw new ValidationError('ID de usuário inválido');

            const removed = await userModel.removeCascade(userId);
            if (!removed) throw new NotFoundError('Usuário não encontrado');
            res.send('Usuário deletado com sucesso, junto com suas matrículas e pagamentos.');
        },
    };
}

module.exports = { createUserController };

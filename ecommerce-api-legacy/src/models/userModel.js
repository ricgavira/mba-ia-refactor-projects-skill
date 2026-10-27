// Cada model recebe o `db` (ou um `tx` dentro de transação) por injeção.
function createUserModel(db) {
    return {
        findByEmail: (email, exec = db) =>
            exec.get('SELECT id FROM users WHERE email = ?', [email]),

        async create({ name, email, passwordHash }, exec = db) {
            const { lastID } = await exec.run(
                'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);
            return lastID;
        },

        /** Remove o usuário e tudo que depende dele (pagamentos → matrículas → usuário), atomicamente. */
        async removeCascade(userId) {
            return db.transaction(async (tx) => {
                await tx.run(
                    'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
                    [userId]);
                await tx.run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
                const { changes } = await tx.run('DELETE FROM users WHERE id = ?', [userId]);
                return changes > 0;
            });
        },
    };
}

module.exports = { createUserModel };

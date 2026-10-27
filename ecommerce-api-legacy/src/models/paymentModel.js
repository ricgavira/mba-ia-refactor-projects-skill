function createPaymentModel(db) {
    return {
        async create({ enrollmentId, amount, status }, exec = db) {
            const { lastID } = await exec.run(
                'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
                [enrollmentId, amount, status]);
            return lastID;
        },
    };
}

module.exports = { createPaymentModel };

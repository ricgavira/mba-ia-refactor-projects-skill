function createEnrollmentModel(db) {
    return {
        async create({ userId, courseId }, exec = db) {
            const { lastID } = await exec.run(
                'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
            return lastID;
        },
    };
}

module.exports = { createEnrollmentModel };

function createCourseModel(db) {
    return {
        findActiveById: (courseId) =>
            db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [courseId]),
    };
}

module.exports = { createCourseModel };

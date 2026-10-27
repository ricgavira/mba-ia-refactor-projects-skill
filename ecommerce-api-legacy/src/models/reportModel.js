const { PAYMENT_STATUS, UNKNOWN_STUDENT } = require('../config/constants');

// Uma única query traz cursos, matrículas, alunos e pagamentos (sem N+1).
const FINANCIAL_ROWS_SQL = `
    SELECT c.id AS course_id, c.title, e.id AS enrollment_id,
           u.name AS student, p.amount, p.status
    FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.id
    LEFT JOIN users u ON u.id = e.user_id
    LEFT JOIN payments p ON p.enrollment_id = e.id
    ORDER BY c.id, e.id`;

function createReportModel(db) {
    return {
        async financialReport() {
            const rows = await db.all(FINANCIAL_ROWS_SQL);
            const byCourse = new Map();

            for (const row of rows) {
                if (!byCourse.has(row.course_id)) {
                    byCourse.set(row.course_id, { course: row.title, revenue: 0, students: [] });
                }
                if (row.enrollment_id === null) continue; // curso sem matrículas

                const entry = byCourse.get(row.course_id);
                if (row.status === PAYMENT_STATUS.PAID) entry.revenue += row.amount;
                entry.students.push({
                    student: row.student || UNKNOWN_STUDENT,
                    paid: row.amount ?? 0,
                });
            }
            return [...byCourse.values()];
        },
    };
}

module.exports = { createReportModel };

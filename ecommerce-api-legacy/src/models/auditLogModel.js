function createAuditLogModel(db) {
    return {
        async record(action, exec = db) {
            await exec.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
        },
    };
}

module.exports = { createAuditLogModel };

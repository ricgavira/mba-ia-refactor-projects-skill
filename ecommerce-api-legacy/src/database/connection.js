const sqlite3 = require('sqlite3');

/**
 * Wrapper Promise sobre o sqlite3 com uma única conexão.
 * transaction() serializa as transações: enquanto uma está aberta, as demais
 * chamadas esperam, evitando que BEGIN/COMMIT de requests concorrentes se misturem.
 */
class Database {
    constructor(path) {
        this.raw = new sqlite3.Database(path);
        this.active = null; // Promise da transação em andamento
    }

    async gate() {
        while (this.active) await this.active;
    }

    rawRun(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.raw.run(sql, params, function (err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    rawGet(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });
    }

    rawAll(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        });
    }

    async run(sql, params) { await this.gate(); return this.rawRun(sql, params); }
    async get(sql, params) { await this.gate(); return this.rawGet(sql, params); }
    async all(sql, params) { await this.gate(); return this.rawAll(sql, params); }

    /** Executa `fn(tx)` em uma transação atômica; `tx` tem run/get/all. */
    async transaction(fn) {
        while (this.active) await this.active;
        let release;
        this.active = new Promise((resolve) => { release = resolve; });
        const tx = {
            run: (sql, params) => this.rawRun(sql, params),
            get: (sql, params) => this.rawGet(sql, params),
            all: (sql, params) => this.rawAll(sql, params),
        };
        try {
            await this.rawRun('BEGIN');
            const result = await fn(tx);
            await this.rawRun('COMMIT');
            return result;
        } catch (err) {
            await this.rawRun('ROLLBACK').catch(() => {});
            throw err;
        } finally {
            this.active = null;
            release();
        }
    }

    close() {
        return new Promise((resolve, reject) => this.raw.close((err) => (err ? reject(err) : resolve())));
    }
}

module.exports = { Database };

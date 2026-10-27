const format = (level, args) => [`[${level}]`, ...args];

module.exports = {
    info: (...args) => console.log(...format('INFO', args)),
    warn: (...args) => console.warn(...format('WARN', args)),
    error: (...args) => console.error(...format('ERROR', args)),
};

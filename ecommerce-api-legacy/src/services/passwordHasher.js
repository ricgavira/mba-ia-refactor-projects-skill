const crypto = require('crypto');

const KEY_LENGTH = 64;

/** Hash com scrypt + sal aleatório por senha. Formato armazenado: "<salt>:<hash>" (hex). */
function hash(password) {
    return new Promise((resolve, reject) => {
        const salt = crypto.randomBytes(16).toString('hex');
        crypto.scrypt(password, salt, KEY_LENGTH, (err, key) =>
            (err ? reject(err) : resolve(`${salt}:${key.toString('hex')}`)));
    });
}

function verify(password, stored) {
    return new Promise((resolve, reject) => {
        const [salt, expected] = stored.split(':');
        crypto.scrypt(password, salt, KEY_LENGTH, (err, key) => {
            if (err) return reject(err);
            resolve(crypto.timingSafeEqual(Buffer.from(expected, 'hex'), key));
        });
    });
}

module.exports = { hash, verify };

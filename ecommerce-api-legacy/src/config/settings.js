// Toda configuração vem do ambiente; nenhum segredo mora no código.
module.exports = {
    port: Number(process.env.PORT) || 3000,
    dbPath: process.env.DB_PATH || ':memory:',
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    // Se definido, rotas administrativas exigem o header X-Admin-Token.
    adminToken: process.env.ADMIN_TOKEN || '',
    // Senha do usuário criado no seed de desenvolvimento.
    seedUserPassword: process.env.SEED_USER_PASSWORD || '123',
};

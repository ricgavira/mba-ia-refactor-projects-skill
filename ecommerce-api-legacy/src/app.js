const express = require('express');

const settings = require('./config/settings');
const logger = require('./utils/logger');
const { Database } = require('./database/connection');
const { initDb } = require('./database/schema');
const passwordHasher = require('./services/passwordHasher');
const { createPaymentGateway } = require('./services/paymentGateway');
const { createCheckoutService } = require('./services/checkoutService');
const { createUserModel } = require('./models/userModel');
const { createCourseModel } = require('./models/courseModel');
const { createEnrollmentModel } = require('./models/enrollmentModel');
const { createPaymentModel } = require('./models/paymentModel');
const { createAuditLogModel } = require('./models/auditLogModel');
const { createReportModel } = require('./models/reportModel');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createReportController } = require('./controllers/reportController');
const { createUserController } = require('./controllers/userController');
const { createAdminAuth } = require('./middlewares/adminAuth');
const { errorHandler, notFoundHandler } = require('./middlewares/errorHandler');
const { buildRoutes } = require('./views/routes');

/** Composition root: instancia as dependências e injeta cada camada na seguinte. */
async function createApp(config = settings) {
    const db = new Database(config.dbPath);
    await initDb(db, { seedPasswordHash: await passwordHasher.hash(config.seedUserPassword) });

    const userModel = createUserModel(db);
    const courseModel = createCourseModel(db);
    const enrollmentModel = createEnrollmentModel(db);
    const paymentModel = createPaymentModel(db);
    const auditLogModel = createAuditLogModel(db);
    const reportModel = createReportModel(db);

    const paymentGateway = createPaymentGateway({ apiKey: config.paymentGatewayKey, logger });
    const checkoutService = createCheckoutService({
        db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel,
        paymentGateway, passwordHasher, logger,
    });

    if (!config.adminToken) {
        logger.warn('ADMIN_TOKEN não configurado: rotas administrativas estão desabilitadas.');
    }

    const app = express();
    app.use(express.json());
    app.use(buildRoutes({
        checkoutController: createCheckoutController({ checkoutService }),
        reportController: createReportController({ reportModel }),
        userController: createUserController({ userModel }),
        requireAdminToken: createAdminAuth({ adminToken: config.adminToken }),
    }));
    app.use(notFoundHandler);
    app.use(errorHandler);
    return app;
}

if (require.main === module) {
    createApp()
        .then((app) => app.listen(settings.port, () => {
            logger.info(`LMS API rodando na porta ${settings.port}...`);
        }))
        .catch((err) => {
            logger.error('Falha ao iniciar a aplicação', err);
            process.exit(1);
        });
}

module.exports = { createApp };

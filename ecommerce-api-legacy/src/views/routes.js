// Mapeamento URL → controller. Nenhuma lógica aqui.
const { Router } = require('express');
const asyncHandler = require('../middlewares/asyncHandler');

function buildRoutes({ checkoutController, reportController, userController, requireAdminToken }) {
    const router = Router();

    router.post('/api/checkout', asyncHandler(checkoutController.checkout));
    router.get('/api/admin/financial-report', requireAdminToken, asyncHandler(reportController.financialReport));
    router.delete('/api/users/:id', requireAdminToken, asyncHandler(userController.remove));

    return router;
}

module.exports = { buildRoutes };

function createReportController({ reportModel }) {
    return {
        async financialReport(req, res) {
            res.json(await reportModel.financialReport());
        },
    };
}

module.exports = { createReportController };

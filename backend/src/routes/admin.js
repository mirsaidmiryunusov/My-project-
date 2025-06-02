const express = require('express');
const adminController = require('../controllers/adminController');
const router = express.Router();

// Статистика системы
router.get('/stats', adminController.getSystemStats);

// Управление номерами компании
router.get('/numbers', adminController.getCompanyNumbers);
router.post('/numbers/assign-api-key', adminController.assignGeminiApiKey);

// Управление модемами
router.get('/modems', adminController.getModemConfigs);
router.post('/modems', adminController.updateModemConfig);

// Управление пользователями
router.get('/users', adminController.getUsers);
router.get('/users/:userId', adminController.getUserDetails);

// Анализы
router.get('/analyses', adminController.getAnalyses);

// Статистика экономии
router.get('/savings', adminController.getSavingsStats);

// Экспорт данных
router.get('/export', adminController.exportData);

module.exports = router;
const express = require('express');
const callController = require('../controllers/callController');
const router = express.Router();

// Начать звонок
router.post('/start', callController.startCall);

// Отправить сообщение в звонке
router.post('/message', callController.sendMessage);

// Завершить звонок
router.post('/end', callController.endCall);

// Получить активные звонки
router.get('/active', callController.getActiveCalls);

// Получить историю звонков пользователя
router.get('/history/:userId', callController.getUserCallHistory);

// Получить детали звонка
router.get('/details/:callSessionId', callController.getCallDetails);

// Получить статистику звонков
router.get('/stats', callController.getCallStats);

// Симуляция звонка для тестирования
router.post('/simulate', callController.simulateCall);

module.exports = router;
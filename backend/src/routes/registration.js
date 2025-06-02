const express = require('express');
const registrationController = require('../controllers/registrationController');
const router = express.Router();

// Регистрация нового пользователя
router.post('/register', registrationController.register);

// Подтверждение email
router.post('/verify-email', registrationController.verifyEmail);

// Обновление номера телефона
router.post('/update-phone', registrationController.updatePhone);

// Получение статуса регистрации
router.get('/status/:userId', registrationController.getRegistrationStatus);

// Повторная отправка email верификации
router.post('/resend-verification', registrationController.resendVerificationEmail);

// Логин для клиентов
router.post('/login', registrationController.clientLogin);

module.exports = router;
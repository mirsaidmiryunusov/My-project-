const { PrismaClient } = require('@prisma/client');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const emailService = require('../services/emailService');
const companyNumberService = require('../services/companyNumberService');
const prisma = new PrismaClient();

class RegistrationController {
  // Регистрация нового пользователя
  async register(req, res) {
    try {
      const { email, password, name, phone } = req.body;

      // Валидация
      if (!email || !password || !name) {
        return res.status(400).json({
          success: false,
          message: 'Email, пароль и имя обязательны'
        });
      }

      // Проверяем, существует ли пользователь
      const existingUser = await prisma.user.findUnique({
        where: { email }
      });

      if (existingUser) {
        return res.status(400).json({
          success: false,
          message: 'Пользователь с таким email уже существует'
        });
      }

      // Хешируем пароль
      const hashedPassword = await bcrypt.hash(password, 12);

      // Генерируем токен верификации
      const verificationToken = emailService.generateVerificationToken();

      // Получаем дефолтный tenant (создаем если нет)
      let defaultTenant = await prisma.tenant.findFirst({
        where: { domain: 'default' }
      });

      if (!defaultTenant) {
        defaultTenant = await prisma.tenant.create({
          data: {
            name: 'Default Tenant',
            domain: 'default',
            isActive: true
          }
        });
      }

      // Создаем пользователя
      const user = await prisma.user.create({
        data: {
          email,
          password: hashedPassword,
          name,
          phone,
          role: 'CLIENT', // Новая роль для клиентов
          tenantId: defaultTenant.id,
          emailVerified: false,
          emailVerifyToken: verificationToken,
          registrationStep: 'email_verification'
        }
      });

      // Отправляем email верификации
      const emailSent = await emailService.sendVerificationEmail(email, verificationToken, name);

      if (!emailSent) {
        console.error('❌ Failed to send verification email');
      }

      res.status(201).json({
        success: true,
        message: 'Регистрация успешна! Проверьте ваш email для подтверждения.',
        data: {
          userId: user.id,
          email: user.email,
          name: user.name,
          registrationStep: user.registrationStep,
          emailSent
        }
      });

    } catch (error) {
      console.error('❌ Registration error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при регистрации'
      });
    }
  }

  // Подтверждение email
  async verifyEmail(req, res) {
    try {
      const { token } = req.body;

      if (!token) {
        return res.status(400).json({
          success: false,
          message: 'Токен верификации обязателен'
        });
      }

      // Находим пользователя по токену
      const user = await prisma.user.findFirst({
        where: { emailVerifyToken: token }
      });

      if (!user) {
        return res.status(400).json({
          success: false,
          message: 'Неверный или истекший токен верификации'
        });
      }

      // Обновляем пользователя
      const updatedUser = await prisma.user.update({
        where: { id: user.id },
        data: {
          emailVerified: true,
          emailVerifyToken: null,
          registrationStep: 'phone_verification'
        }
      });

      res.json({
        success: true,
        message: 'Email успешно подтвержден!',
        data: {
          userId: updatedUser.id,
          registrationStep: updatedUser.registrationStep
        }
      });

    } catch (error) {
      console.error('❌ Email verification error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при подтверждении email'
      });
    }
  }

  // Обновление номера телефона
  async updatePhone(req, res) {
    try {
      const { userId, phone } = req.body;

      if (!userId || !phone) {
        return res.status(400).json({
          success: false,
          message: 'ID пользователя и номер телефона обязательны'
        });
      }

      // Проверяем пользователя
      const user = await prisma.user.findUnique({
        where: { id: userId }
      });

      if (!user || !user.emailVerified) {
        return res.status(400).json({
          success: false,
          message: 'Пользователь не найден или email не подтвержден'
        });
      }

      // Назначаем номер компании
      const assignedNumber = await companyNumberService.assignNumberToUser(userId);

      // Обновляем пользователя
      const updatedUser = await prisma.user.update({
        where: { id: userId },
        data: {
          phone,
          registrationStep: 'call_scheduled'
        }
      });

      // Отправляем приветственный email с номером
      await emailService.sendWelcomeEmail(user.email, user.name, assignedNumber);

      res.json({
        success: true,
        message: 'Номер телефона обновлен! Вам назначен персональный номер компании.',
        data: {
          userId: updatedUser.id,
          phone: updatedUser.phone,
          assignedNumber,
          registrationStep: updatedUser.registrationStep
        }
      });

    } catch (error) {
      console.error('❌ Phone update error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при обновлении номера телефона'
      });
    }
  }

  // Получение статуса регистрации
  async getRegistrationStatus(req, res) {
    try {
      const { userId } = req.params;

      const user = await prisma.user.findUnique({
        where: { id: userId },
        select: {
          id: true,
          email: true,
          name: true,
          phone: true,
          emailVerified: true,
          assignedNumber: true,
          registrationStep: true,
          createdAt: true
        }
      });

      if (!user) {
        return res.status(404).json({
          success: false,
          message: 'Пользователь не найден'
        });
      }

      // Получаем дополнительную информацию в зависимости от шага
      let additionalData = {};

      if (user.registrationStep === 'analysis_done') {
        // Получаем анализ и расчет экономии
        const analysis = await prisma.aIAnalysis.findFirst({
          where: { userId: user.id },
          orderBy: { createdAt: 'desc' }
        });

        const savings = await prisma.savingsCalculation.findUnique({
          where: { userId: user.id }
        });

        additionalData = { analysis, savings };
      }

      res.json({
        success: true,
        data: {
          user,
          ...additionalData
        }
      });

    } catch (error) {
      console.error('❌ Get registration status error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при получении статуса регистрации'
      });
    }
  }

  // Повторная отправка email верификации
  async resendVerificationEmail(req, res) {
    try {
      const { email } = req.body;

      if (!email) {
        return res.status(400).json({
          success: false,
          message: 'Email обязателен'
        });
      }

      const user = await prisma.user.findUnique({
        where: { email }
      });

      if (!user) {
        return res.status(404).json({
          success: false,
          message: 'Пользователь не найден'
        });
      }

      if (user.emailVerified) {
        return res.status(400).json({
          success: false,
          message: 'Email уже подтвержден'
        });
      }

      // Генерируем новый токен
      const newToken = emailService.generateVerificationToken();

      await prisma.user.update({
        where: { id: user.id },
        data: { emailVerifyToken: newToken }
      });

      // Отправляем email
      const emailSent = await emailService.sendVerificationEmail(email, newToken, user.name);

      res.json({
        success: true,
        message: 'Email верификации отправлен повторно',
        emailSent
      });

    } catch (error) {
      console.error('❌ Resend verification email error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при повторной отправке email'
      });
    }
  }

  // Логин для клиентов
  async clientLogin(req, res) {
    try {
      const { email, password } = req.body;

      if (!email || !password) {
        return res.status(400).json({
          success: false,
          message: 'Email и пароль обязательны'
        });
      }

      // Находим пользователя
      const user = await prisma.user.findUnique({
        where: { email }
      });

      if (!user) {
        return res.status(401).json({
          success: false,
          message: 'Неверный email или пароль'
        });
      }

      // Проверяем пароль
      const isPasswordValid = await bcrypt.compare(password, user.password);

      if (!isPasswordValid) {
        return res.status(401).json({
          success: false,
          message: 'Неверный email или пароль'
        });
      }

      // Проверяем подтверждение email
      if (!user.emailVerified) {
        return res.status(401).json({
          success: false,
          message: 'Подтвердите ваш email перед входом',
          requiresEmailVerification: true
        });
      }

      // Генерируем JWT токен
      const token = jwt.sign(
        { userId: user.id, email: user.email, role: user.role },
        process.env.JWT_SECRET || 'your-secret-key',
        { expiresIn: '7d' }
      );

      // Обновляем последний вход
      await prisma.user.update({
        where: { id: user.id },
        data: { lastLogin: new Date() }
      });

      res.json({
        success: true,
        message: 'Вход выполнен успешно',
        data: {
          token,
          user: {
            id: user.id,
            email: user.email,
            name: user.name,
            phone: user.phone,
            role: user.role,
            registrationStep: user.registrationStep,
            assignedNumber: user.assignedNumber
          }
        }
      });

    } catch (error) {
      console.error('❌ Client login error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при входе'
      });
    }
  }
}

module.exports = new RegistrationController();
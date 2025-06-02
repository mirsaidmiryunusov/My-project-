const aiCallService = require('../services/aiCallService');
const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

class CallController {
  // Начать звонок
  async startCall(req, res) {
    try {
      const { companyNumber, clientPhone } = req.body;

      if (!companyNumber || !clientPhone) {
        return res.status(400).json({
          success: false,
          message: 'Номер компании и номер клиента обязательны'
        });
      }

      const result = await aiCallService.startCall(companyNumber, clientPhone);

      if (!result.success) {
        return res.status(400).json(result);
      }

      res.json({
        success: true,
        message: 'Звонок начат успешно',
        data: {
          callSessionId: result.callSessionId,
          greeting: result.greeting,
          user: {
            id: result.user.id,
            name: result.user.name,
            email: result.user.email
          }
        }
      });

    } catch (error) {
      console.error('❌ Start call error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при начале звонка'
      });
    }
  }

  // Отправить сообщение в звонке
  async sendMessage(req, res) {
    try {
      const { callSessionId, message } = req.body;

      if (!callSessionId || !message) {
        return res.status(400).json({
          success: false,
          message: 'ID сессии и сообщение обязательны'
        });
      }

      const result = await aiCallService.processClientMessage(callSessionId, message);

      if (result.error) {
        return res.status(400).json({
          success: false,
          message: result.error
        });
      }

      res.json({
        success: true,
        data: {
          response: result.response,
          timeRemaining: result.timeRemaining
        }
      });

    } catch (error) {
      console.error('❌ Send message error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при отправке сообщения'
      });
    }
  }

  // Завершить звонок
  async endCall(req, res) {
    try {
      const { callSessionId } = req.body;

      if (!callSessionId) {
        return res.status(400).json({
          success: false,
          message: 'ID сессии обязателен'
        });
      }

      const result = await aiCallService.endCall(callSessionId, 'manual');

      if (result.error) {
        return res.status(400).json({
          success: false,
          message: result.error
        });
      }

      res.json({
        success: true,
        message: 'Звонок завершен',
        data: {
          finalMessage: result.finalMessage,
          duration: result.duration
        }
      });

    } catch (error) {
      console.error('❌ End call error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при завершении звонка'
      });
    }
  }

  // Получить активные звонки (для админ панели)
  async getActiveCalls(req, res) {
    try {
      const activeCalls = aiCallService.getActiveCalls();

      res.json({
        success: true,
        data: {
          activeCalls,
          count: activeCalls.length
        }
      });

    } catch (error) {
      console.error('❌ Get active calls error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при получении активных звонков'
      });
    }
  }

  // Получить историю звонков пользователя
  async getUserCallHistory(req, res) {
    try {
      const { userId } = req.params;
      const { page = 1, limit = 10 } = req.query;

      const skip = (parseInt(page) - 1) * parseInt(limit);

      const calls = await prisma.callSession.findMany({
        where: { userId },
        skip,
        take: parseInt(limit),
        orderBy: { createdAt: 'desc' },
        include: {
          user: {
            select: {
              name: true,
              email: true,
              phone: true
            }
          }
        }
      });

      const total = await prisma.callSession.count({
        where: { userId }
      });

      res.json({
        success: true,
        data: {
          calls,
          pagination: {
            page: parseInt(page),
            limit: parseInt(limit),
            total,
            pages: Math.ceil(total / parseInt(limit))
          }
        }
      });

    } catch (error) {
      console.error('❌ Get user call history error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при получении истории звонков'
      });
    }
  }

  // Получить детали звонка
  async getCallDetails(req, res) {
    try {
      const { callSessionId } = req.params;

      const call = await prisma.callSession.findUnique({
        where: { id: callSessionId },
        include: {
          user: {
            select: {
              id: true,
              name: true,
              email: true,
              phone: true
            }
          }
        }
      });

      if (!call) {
        return res.status(404).json({
          success: false,
          message: 'Звонок не найден'
        });
      }

      // Парсим транскрипт если есть
      let transcript = [];
      if (call.transcript) {
        try {
          transcript = JSON.parse(call.transcript);
        } catch (e) {
          console.error('Error parsing transcript:', e);
        }
      }

      res.json({
        success: true,
        data: {
          ...call,
          transcript
        }
      });

    } catch (error) {
      console.error('❌ Get call details error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при получении деталей звонка'
      });
    }
  }

  // Получить статистику звонков
  async getCallStats(req, res) {
    try {
      const { period = '7d' } = req.query;
      
      let dateFilter = new Date();
      switch (period) {
        case '24h':
          dateFilter.setHours(dateFilter.getHours() - 24);
          break;
        case '7d':
          dateFilter.setDate(dateFilter.getDate() - 7);
          break;
        case '30d':
          dateFilter.setDate(dateFilter.getDate() - 30);
          break;
        default:
          dateFilter.setDate(dateFilter.getDate() - 7);
      }

      const totalCalls = await prisma.callSession.count({
        where: {
          createdAt: { gte: dateFilter }
        }
      });

      const completedCalls = await prisma.callSession.count({
        where: {
          status: 'completed',
          createdAt: { gte: dateFilter }
        }
      });

      const avgDuration = await prisma.callSession.aggregate({
        where: {
          status: 'completed',
          createdAt: { gte: dateFilter }
        },
        _avg: {
          duration: true
        }
      });

      const activeCalls = aiCallService.getActiveCalls().length;

      res.json({
        success: true,
        data: {
          totalCalls,
          completedCalls,
          activeCalls,
          avgDuration: Math.round(avgDuration._avg.duration || 0),
          completionRate: totalCalls > 0 ? Math.round((completedCalls / totalCalls) * 100) : 0,
          period
        }
      });

    } catch (error) {
      console.error('❌ Get call stats error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при получении статистики звонков'
      });
    }
  }

  // Симуляция звонка для тестирования
  async simulateCall(req, res) {
    try {
      const { userId, message } = req.body;

      if (!userId) {
        return res.status(400).json({
          success: false,
          message: 'ID пользователя обязателен'
        });
      }

      // Получаем пользователя
      const user = await prisma.user.findUnique({
        where: { id: userId }
      });

      if (!user || !user.assignedNumber) {
        return res.status(404).json({
          success: false,
          message: 'Пользователь не найден или номер не назначен'
        });
      }

      // Начинаем симуляцию звонка
      const startResult = await aiCallService.startCall(user.assignedNumber, user.phone);

      if (!startResult.success) {
        return res.status(400).json(startResult);
      }

      let response = startResult.greeting;

      // Если есть сообщение, обрабатываем его
      if (message) {
        const messageResult = await aiCallService.processClientMessage(
          startResult.callSessionId, 
          message
        );
        
        if (!messageResult.error) {
          response = messageResult.response;
        }
      }

      res.json({
        success: true,
        message: 'Симуляция звонка запущена',
        data: {
          callSessionId: startResult.callSessionId,
          response,
          user: {
            id: user.id,
            name: user.name,
            assignedNumber: user.assignedNumber
          }
        }
      });

    } catch (error) {
      console.error('❌ Simulate call error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при симуляции звонка'
      });
    }
  }
}

module.exports = new CallController();
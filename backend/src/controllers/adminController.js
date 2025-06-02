const { PrismaClient } = require('@prisma/client');
const companyNumberService = require('../services/companyNumberService');
const aiCallService = require('../services/aiCallService');
const prisma = new PrismaClient();

class AdminController {
  // Получить статистику системы
  async getSystemStats(req, res) {
    try {
      // Статистика пользователей
      const totalUsers = await prisma.user.count();
      const verifiedUsers = await prisma.user.count({
        where: { emailVerified: true }
      });
      const activeUsers = await prisma.user.count({
        where: { 
          lastLogin: {
            gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) // последние 30 дней
          }
        }
      });

      // Статистика по шагам регистрации
      const registrationSteps = await prisma.user.groupBy({
        by: ['registrationStep'],
        _count: true
      });

      // Статистика номеров
      const numbersStats = await companyNumberService.getNumbersStats();

      // Статистика звонков
      const totalCalls = await prisma.callSession.count();
      const completedCalls = await prisma.callSession.count({
        where: { status: 'completed' }
      });
      const activeCalls = aiCallService.getActiveCalls().length;

      // Статистика анализов
      const totalAnalyses = await prisma.aIAnalysis.count();
      const recentAnalyses = await prisma.aIAnalysis.count({
        where: {
          createdAt: {
            gte: new Date(Date.now() - 24 * 60 * 60 * 1000) // последние 24 часа
          }
        }
      });

      // Статистика подписок
      const subscriptions = await prisma.subscription.groupBy({
        by: ['status'],
        _count: true
      });

      res.json({
        success: true,
        data: {
          users: {
            total: totalUsers,
            verified: verifiedUsers,
            active: activeUsers,
            verificationRate: totalUsers > 0 ? Math.round((verifiedUsers / totalUsers) * 100) : 0
          },
          registrationSteps: registrationSteps.reduce((acc, step) => {
            acc[step.registrationStep] = step._count;
            return acc;
          }, {}),
          numbers: numbersStats,
          calls: {
            total: totalCalls,
            completed: completedCalls,
            active: activeCalls,
            completionRate: totalCalls > 0 ? Math.round((completedCalls / totalCalls) * 100) : 0
          },
          analyses: {
            total: totalAnalyses,
            recent: recentAnalyses
          },
          subscriptions: subscriptions.reduce((acc, sub) => {
            acc[sub.status] = sub._count;
            return acc;
          }, {})
        }
      });

    } catch (error) {
      console.error('❌ Get system stats error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при получении статистики системы'
      });
    }
  }

  // Управление номерами компании
  async getCompanyNumbers(req, res) {
    try {
      const { page = 1, limit = 50, filter } = req.query;

      const result = await companyNumberService.getAllNumbers(
        parseInt(page), 
        parseInt(limit)
      );

      res.json({
        success: true,
        data: result
      });

    } catch (error) {
      console.error('❌ Get company numbers error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при получении номеров компании'
      });
    }
  }

  // Назначить API ключ Gemini для номера
  async assignGeminiApiKey(req, res) {
    try {
      const { numberId, apiKey, modemId } = req.body;

      if (!numberId || !apiKey) {
        return res.status(400).json({
          success: false,
          message: 'ID номера и API ключ обязательны'
        });
      }

      await companyNumberService.assignGeminiApiKey(numberId, apiKey, modemId);

      res.json({
        success: true,
        message: 'API ключ Gemini назначен успешно'
      });

    } catch (error) {
      console.error('❌ Assign Gemini API key error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при назначении API ключа'
      });
    }
  }

  // Управление конфигурацией модемов
  async getModemConfigs(req, res) {
    try {
      const modems = await prisma.modemConfig.findMany({
        orderBy: { modemId: 'asc' }
      });

      res.json({
        success: true,
        data: { modems }
      });

    } catch (error) {
      console.error('❌ Get modem configs error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при получении конфигурации модемов'
      });
    }
  }

  // Создать/обновить конфигурацию модема
  async updateModemConfig(req, res) {
    try {
      const { modemId, geminiApiKey, isActive, assignedNumber, maxConcurrentCalls } = req.body;

      if (!modemId) {
        return res.status(400).json({
          success: false,
          message: 'ID модема обязателен'
        });
      }

      const modem = await prisma.modemConfig.upsert({
        where: { modemId },
        update: {
          geminiApiKey,
          isActive: isActive !== undefined ? isActive : true,
          assignedNumber,
          maxConcurrentCalls: maxConcurrentCalls || 1
        },
        create: {
          modemId,
          geminiApiKey,
          isActive: isActive !== undefined ? isActive : true,
          assignedNumber,
          maxConcurrentCalls: maxConcurrentCalls || 1
        }
      });

      res.json({
        success: true,
        message: 'Конфигурация модема обновлена',
        data: { modem }
      });

    } catch (error) {
      console.error('❌ Update modem config error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при обновлении конфигурации модема'
      });
    }
  }

  // Получить всех пользователей
  async getUsers(req, res) {
    try {
      const { page = 1, limit = 50, filter, registrationStep } = req.query;
      const skip = (parseInt(page) - 1) * parseInt(limit);

      let whereClause = {};
      
      if (filter) {
        whereClause.OR = [
          { name: { contains: filter, mode: 'insensitive' } },
          { email: { contains: filter, mode: 'insensitive' } },
          { phone: { contains: filter, mode: 'insensitive' } }
        ];
      }

      if (registrationStep) {
        whereClause.registrationStep = registrationStep;
      }

      const users = await prisma.user.findMany({
        where: whereClause,
        skip,
        take: parseInt(limit),
        orderBy: { createdAt: 'desc' },
        include: {
          callSessions: {
            select: {
              id: true,
              status: true,
              duration: true,
              createdAt: true
            },
            orderBy: { createdAt: 'desc' },
            take: 1
          },
          aiAnalysis: {
            select: {
              id: true,
              clientNeeds: true,
              createdAt: true
            },
            orderBy: { createdAt: 'desc' },
            take: 1
          },
          savingsCalculation: {
            select: {
              estimatedTimeSavings: true,
              estimatedMoneySavings: true,
              automationLevel: true
            }
          },
          subscriptions: {
            select: {
              plan: true,
              status: true,
              price: true
            },
            orderBy: { createdAt: 'desc' },
            take: 1
          }
        }
      });

      const total = await prisma.user.count({ where: whereClause });

      res.json({
        success: true,
        data: {
          users,
          pagination: {
            page: parseInt(page),
            limit: parseInt(limit),
            total,
            pages: Math.ceil(total / parseInt(limit))
          }
        }
      });

    } catch (error) {
      console.error('❌ Get users error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при получении пользователей'
      });
    }
  }

  // Получить детали пользователя
  async getUserDetails(req, res) {
    try {
      const { userId } = req.params;

      const user = await prisma.user.findUnique({
        where: { id: userId },
        include: {
          callSessions: {
            orderBy: { createdAt: 'desc' }
          },
          aiAnalysis: {
            orderBy: { createdAt: 'desc' }
          },
          savingsCalculation: true,
          subscriptions: {
            orderBy: { createdAt: 'desc' }
          },
          companyNumber: true
        }
      });

      if (!user) {
        return res.status(404).json({
          success: false,
          message: 'Пользователь не найден'
        });
      }

      res.json({
        success: true,
        data: { user }
      });

    } catch (error) {
      console.error('❌ Get user details error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при получении деталей пользователя'
      });
    }
  }

  // Получить все анализы
  async getAnalyses(req, res) {
    try {
      const { page = 1, limit = 20 } = req.query;
      const skip = (parseInt(page) - 1) * parseInt(limit);

      const analyses = await prisma.aIAnalysis.findMany({
        skip,
        take: parseInt(limit),
        orderBy: { createdAt: 'desc' },
        include: {
          user: {
            select: {
              id: true,
              name: true,
              email: true,
              phone: true,
              registrationStep: true
            }
          }
        }
      });

      const total = await prisma.aIAnalysis.count();

      res.json({
        success: true,
        data: {
          analyses,
          pagination: {
            page: parseInt(page),
            limit: parseInt(limit),
            total,
            pages: Math.ceil(total / parseInt(limit))
          }
        }
      });

    } catch (error) {
      console.error('❌ Get analyses error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при получении анализов'
      });
    }
  }

  // Получить статистику экономии
  async getSavingsStats(req, res) {
    try {
      const savings = await prisma.savingsCalculation.findMany({
        include: {
          user: {
            select: {
              name: true,
              email: true,
              registrationStep: true
            }
          }
        }
      });

      const totalTimeSavings = savings.reduce((sum, s) => sum + (s.estimatedTimeSavings || 0), 0);
      const totalMoneySavings = savings.reduce((sum, s) => sum + (s.estimatedMoneySavings || 0), 0);
      const avgTimeSavings = savings.length > 0 ? Math.round(totalTimeSavings / savings.length) : 0;
      const avgMoneySavings = savings.length > 0 ? Math.round(totalMoneySavings / savings.length) : 0;

      const automationLevels = savings.reduce((acc, s) => {
        const level = s.automationLevel || 'medium';
        acc[level] = (acc[level] || 0) + 1;
        return acc;
      }, {});

      res.json({
        success: true,
        data: {
          totalCalculations: savings.length,
          totalTimeSavings,
          totalMoneySavings,
          avgTimeSavings,
          avgMoneySavings,
          automationLevels,
          savings: savings.slice(0, 10) // Последние 10 для превью
        }
      });

    } catch (error) {
      console.error('❌ Get savings stats error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при получении статистики экономии'
      });
    }
  }

  // Экспорт данных
  async exportData(req, res) {
    try {
      const { type = 'users', format = 'json' } = req.query;

      let data;
      let filename;

      switch (type) {
        case 'users':
          data = await prisma.user.findMany({
            select: {
              id: true,
              email: true,
              name: true,
              phone: true,
              registrationStep: true,
              emailVerified: true,
              assignedNumber: true,
              createdAt: true,
              lastLogin: true
            }
          });
          filename = 'users_export';
          break;

        case 'calls':
          data = await prisma.callSession.findMany({
            include: {
              user: {
                select: {
                  name: true,
                  email: true
                }
              }
            }
          });
          filename = 'calls_export';
          break;

        case 'analyses':
          data = await prisma.aIAnalysis.findMany({
            include: {
              user: {
                select: {
                  name: true,
                  email: true
                }
              }
            }
          });
          filename = 'analyses_export';
          break;

        default:
          return res.status(400).json({
            success: false,
            message: 'Неподдерживаемый тип экспорта'
          });
      }

      if (format === 'csv') {
        // Простая CSV конвертация
        const csv = this.convertToCSV(data);
        res.setHeader('Content-Type', 'text/csv');
        res.setHeader('Content-Disposition', `attachment; filename="${filename}.csv"`);
        res.send(csv);
      } else {
        res.setHeader('Content-Type', 'application/json');
        res.setHeader('Content-Disposition', `attachment; filename="${filename}.json"`);
        res.json({
          success: true,
          exportDate: new Date().toISOString(),
          type,
          count: data.length,
          data
        });
      }

    } catch (error) {
      console.error('❌ Export data error:', error);
      res.status(500).json({
        success: false,
        message: 'Ошибка при экспорте данных'
      });
    }
  }

  // Вспомогательная функция для конвертации в CSV
  convertToCSV(data) {
    if (!data.length) return '';

    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(','),
      ...data.map(row => 
        headers.map(header => {
          const value = row[header];
          if (typeof value === 'object' && value !== null) {
            return `"${JSON.stringify(value).replace(/"/g, '""')}"`;
          }
          return `"${String(value || '').replace(/"/g, '""')}"`;
        }).join(',')
      )
    ].join('\n');

    return csvContent;
  }
}

module.exports = new AdminController();
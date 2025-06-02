const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();

class CompanyNumberService {
  constructor() {
    this.initializeNumbers();
  }

  // Инициализация пула номеров компании
  async initializeNumbers() {
    try {
      const existingNumbers = await prisma.companyNumber.count();
      
      if (existingNumbers === 0) {
        console.log('🔢 Initializing company numbers pool...');
        
        // Создаем пул номеров (например, +7-800-XXX-XXXX)
        const numbers = [];
        for (let i = 1000; i <= 1100; i++) {
          numbers.push({
            number: `+7-800-555-${i}`,
            isAvailable: true
          });
        }
        
        await prisma.companyNumber.createMany({
          data: numbers
        });
        
        console.log(`✅ Created ${numbers.length} company numbers`);
      }
    } catch (error) {
      console.error('❌ Error initializing company numbers:', error);
    }
  }

  // Получить свободный номер для клиента
  async assignNumberToUser(userId) {
    try {
      // Проверяем, есть ли уже назначенный номер
      const existingAssignment = await prisma.companyNumber.findFirst({
        where: { assignedTo: userId }
      });

      if (existingAssignment) {
        return existingAssignment.number;
      }

      // Находим первый свободный номер
      const availableNumber = await prisma.companyNumber.findFirst({
        where: { isAvailable: true }
      });

      if (!availableNumber) {
        throw new Error('No available company numbers');
      }

      // Назначаем номер пользователю
      await prisma.companyNumber.update({
        where: { id: availableNumber.id },
        data: {
          isAvailable: false,
          assignedTo: userId
        }
      });

      // Обновляем пользователя
      await prisma.user.update({
        where: { id: userId },
        data: { assignedNumber: availableNumber.number }
      });

      console.log(`📞 Assigned number ${availableNumber.number} to user ${userId}`);
      return availableNumber.number;

    } catch (error) {
      console.error('❌ Error assigning number to user:', error);
      throw error;
    }
  }

  // Освободить номер
  async releaseNumber(userId) {
    try {
      const assignment = await prisma.companyNumber.findFirst({
        where: { assignedTo: userId }
      });

      if (assignment) {
        await prisma.companyNumber.update({
          where: { id: assignment.id },
          data: {
            isAvailable: true,
            assignedTo: null
          }
        });

        await prisma.user.update({
          where: { id: userId },
          data: { assignedNumber: null }
        });

        console.log(`📞 Released number ${assignment.number} from user ${userId}`);
      }
    } catch (error) {
      console.error('❌ Error releasing number:', error);
      throw error;
    }
  }

  // Получить статистику номеров
  async getNumbersStats() {
    try {
      const total = await prisma.companyNumber.count();
      const available = await prisma.companyNumber.count({
        where: { isAvailable: true }
      });
      const assigned = total - available;

      return {
        total,
        available,
        assigned,
        utilization: total > 0 ? Math.round((assigned / total) * 100) : 0
      };
    } catch (error) {
      console.error('❌ Error getting numbers stats:', error);
      return { total: 0, available: 0, assigned: 0, utilization: 0 };
    }
  }

  // Получить все номера для админ панели
  async getAllNumbers(page = 1, limit = 50) {
    try {
      const skip = (page - 1) * limit;
      
      const numbers = await prisma.companyNumber.findMany({
        skip,
        take: limit,
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
        },
        orderBy: { number: 'asc' }
      });

      const total = await prisma.companyNumber.count();

      return {
        numbers,
        pagination: {
          page,
          limit,
          total,
          pages: Math.ceil(total / limit)
        }
      };
    } catch (error) {
      console.error('❌ Error getting all numbers:', error);
      throw error;
    }
  }

  // Назначить API ключ Gemini для номера
  async assignGeminiApiKey(numberId, apiKey, modemId) {
    try {
      await prisma.companyNumber.update({
        where: { id: numberId },
        data: {
          geminiApiKey: apiKey,
          modemId: modemId
        }
      });

      console.log(`🔑 Assigned Gemini API key to number ${numberId}`);
      return true;
    } catch (error) {
      console.error('❌ Error assigning Gemini API key:', error);
      throw error;
    }
  }

  // Получить API ключ для номера
  async getGeminiApiKey(companyNumber) {
    try {
      const numberRecord = await prisma.companyNumber.findUnique({
        where: { number: companyNumber }
      });

      return numberRecord?.geminiApiKey || process.env.GEMINI_API_KEY;
    } catch (error) {
      console.error('❌ Error getting Gemini API key:', error);
      return process.env.GEMINI_API_KEY;
    }
  }

  // Проверить, принадлежит ли номер пользователю
  async verifyNumberOwnership(companyNumber, userPhone) {
    try {
      const numberRecord = await prisma.companyNumber.findUnique({
        where: { number: companyNumber },
        include: {
          user: true
        }
      });

      if (!numberRecord || !numberRecord.user) {
        return { valid: false, reason: 'Number not assigned' };
      }

      // Проверяем номер телефона (убираем все символы кроме цифр для сравнения)
      const cleanUserPhone = userPhone.replace(/\D/g, '');
      const cleanRegisteredPhone = numberRecord.user.phone?.replace(/\D/g, '') || '';

      if (cleanUserPhone !== cleanRegisteredPhone) {
        return { 
          valid: false, 
          reason: 'Phone number mismatch',
          expectedPhone: numberRecord.user.phone
        };
      }

      return {
        valid: true,
        user: numberRecord.user,
        companyNumber: numberRecord
      };
    } catch (error) {
      console.error('❌ Error verifying number ownership:', error);
      return { valid: false, reason: 'Verification error' };
    }
  }
}

module.exports = new CompanyNumberService();
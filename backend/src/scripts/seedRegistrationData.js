const { PrismaClient } = require('@prisma/client');
const bcrypt = require('bcryptjs');
const prisma = new PrismaClient();

async function seedRegistrationData() {
  try {
    console.log('🌱 Seeding registration system data...');

    // Создаем тестовые номера компании
    const companyNumbers = [
      '+1-800-GEMINI-1',
      '+1-800-GEMINI-2', 
      '+1-800-GEMINI-3',
      '+1-800-GEMINI-4',
      '+1-800-GEMINI-5'
    ];

    for (const number of companyNumbers) {
      await prisma.companyNumber.upsert({
        where: { number },
        update: {},
        create: {
          number,
          isActive: true,
          geminiApiKey: 'demo-api-key-' + Math.random().toString(36).substr(2, 9),
          modemId: 'modem-' + Math.random().toString(36).substr(2, 5)
        }
      });
    }

    console.log('✅ Registration system data seeded successfully!');
    console.log('📊 Created company numbers and test configurations');

  } catch (error) {
    console.error('❌ Error seeding registration data:', error);
  } finally {
    await prisma.$disconnect();
  }
}

// Запускаем если файл вызван напрямую
if (require.main === module) {
  seedRegistrationData();
}

module.exports = { seedRegistrationData };
const { PrismaClient } = require('@prisma/client');
const { GoogleGenerativeAI } = require('@google/generative-ai');
const companyNumberService = require('./companyNumberService');
const emailService = require('./emailService');
const prisma = new PrismaClient();

class AICallService {
  constructor() {
    this.activeCalls = new Map(); // Хранение активных звонков
    this.callTimeouts = new Map(); // Таймауты для звонков
  }

  // Начать звонок
  async startCall(companyNumber, clientPhone) {
    try {
      console.log(`📞 Starting call from ${clientPhone} to ${companyNumber}`);

      // Проверяем принадлежность номера
      const verification = await companyNumberService.verifyNumberOwnership(companyNumber, clientPhone);
      
      if (!verification.valid) {
        console.log(`❌ Call rejected: ${verification.reason}`);
        return {
          success: false,
          reason: verification.reason,
          message: this.getRejectMessage(verification.reason)
        };
      }

      // Создаем сессию звонка
      const callSession = await prisma.callSession.create({
        data: {
          userId: verification.user.id,
          companyNumber,
          clientPhone,
          status: 'in_progress',
          startTime: new Date()
        }
      });

      // Сохраняем активный звонок
      this.activeCalls.set(callSession.id, {
        session: callSession,
        user: verification.user,
        startTime: Date.now(),
        transcript: [],
        currentStep: 'greeting'
      });

      // Устанавливаем таймаут на 30 минут
      const timeout = setTimeout(() => {
        this.endCall(callSession.id, 'timeout');
      }, 30 * 60 * 1000); // 30 минут

      this.callTimeouts.set(callSession.id, timeout);

      // Обновляем статус пользователя
      await prisma.user.update({
        where: { id: verification.user.id },
        data: { registrationStep: 'call_completed' }
      });

      console.log(`✅ Call started successfully for user ${verification.user.name}`);

      return {
        success: true,
        callSessionId: callSession.id,
        greeting: await this.generateGreeting(verification.user),
        user: verification.user
      };

    } catch (error) {
      console.error('❌ Error starting call:', error);
      return {
        success: false,
        reason: 'system_error',
        message: 'Извините, произошла техническая ошибка. Попробуйте позвонить позже.'
      };
    }
  }

  // Генерация приветствия
  async generateGreeting(user) {
    const greeting = `
      Здравствуйте, ${user.name}! Добро пожаловать в GeminiVoice AI Call Center!
      
      Меня зовут Алиса, я ваш персональный AI-консультант. Я помогу вам понять, 
      как наша платформа может автоматизировать ваши бизнес-процессы и сэкономить 
      ваше время и деньги.
      
      У нас есть 30 минут для детальной консультации. За это время я:
      
      1. Узнаю о ваших текущих задачах и процессах
      2. Проанализирую возможности для автоматизации
      3. Предложу конкретные решения
      4. Рассчитаю потенциальную экономию
      5. Подготовлю персональные рекомендации
      
      Расскажите, пожалуйста, чем занимается ваш бизнес и какие задачи 
      вы хотели бы автоматизировать?
    `;

    return greeting.trim();
  }

  // Обработка сообщения от клиента
  async processClientMessage(callSessionId, message) {
    try {
      const callData = this.activeCalls.get(callSessionId);
      if (!callData) {
        return { error: 'Call session not found' };
      }

      // Добавляем сообщение в транскрипт
      callData.transcript.push({
        timestamp: new Date(),
        speaker: 'client',
        message: message
      });

      // Получаем API ключ для этого номера
      const apiKey = await companyNumberService.getGeminiApiKey(callData.session.companyNumber);
      const genAI = new GoogleGenerativeAI(apiKey);
      const model = genAI.getGenerativeModel({ model: "gemini-pro" });

      // Генерируем ответ на основе контекста
      const response = await this.generateAIResponse(callData, message, model);

      // Добавляем ответ в транскрипт
      callData.transcript.push({
        timestamp: new Date(),
        speaker: 'ai',
        message: response
      });

      // Обновляем данные звонка
      this.activeCalls.set(callSessionId, callData);

      return {
        success: true,
        response: response,
        timeRemaining: this.getTimeRemaining(callData.startTime)
      };

    } catch (error) {
      console.error('❌ Error processing client message:', error);
      return {
        error: 'Failed to process message',
        response: 'Извините, произошла ошибка. Можете повторить ваш вопрос?'
      };
    }
  }

  // Генерация AI ответа
  async generateAIResponse(callData, clientMessage, model) {
    const context = this.buildConversationContext(callData);
    
    const prompt = `
      Ты - Алиса, персональный AI-консультант GeminiVoice AI Call Center.
      
      КОНТЕКСТ КОМПАНИИ:
      GeminiVoice AI - это платформа для автоматизации бизнес-процессов через AI.
      
      НАШИ ВОЗМОЖНОСТИ:
      - Автоматизация телефонных звонков
      - AI-чат боты для Telegram, WhatsApp, сайтов
      - Автоматизация email рассылок
      - Обработка документов и данных
      - Интеграция с CRM системами
      - Голосовые помощники
      - Автоматизация социальных сетей
      - Анализ данных и отчетность
      
      ТВОЯ ЗАДАЧА:
      1. Выяснить потребности клиента
      2. Предложить конкретные решения
      3. Рассчитать экономию времени/денег
      4. Подготовить рекомендации
      
      ИСТОРИЯ РАЗГОВОРА:
      ${context}
      
      ПОСЛЕДНЕЕ СООБЩЕНИЕ КЛИЕНТА:
      ${clientMessage}
      
      ИНСТРУКЦИИ:
      - Отвечай дружелюбно и профессионально
      - Задавай уточняющие вопросы
      - Предлагай конкретные решения
      - Приводи примеры экономии
      - Говори на русском языке
      - Ответ должен быть 2-4 предложения
      
      ОТВЕТ:
    `;

    try {
      const result = await model.generateContent(prompt);
      const response = result.response;
      return response.text();
    } catch (error) {
      console.error('❌ Error generating AI response:', error);
      return 'Понял вас. Расскажите подробнее о ваших задачах, чтобы я мог предложить лучшие решения.';
    }
  }

  // Построение контекста разговора
  buildConversationContext(callData) {
    return callData.transcript
      .slice(-10) // Последние 10 сообщений
      .map(entry => `${entry.speaker === 'client' ? 'Клиент' : 'AI'}: ${entry.message}`)
      .join('\n');
  }

  // Завершение звонка
  async endCall(callSessionId, reason = 'completed') {
    try {
      const callData = this.activeCalls.get(callSessionId);
      if (!callData) {
        return { error: 'Call session not found' };
      }

      const endTime = new Date();
      const duration = Math.floor((endTime - callData.session.startTime) / 1000);

      // Очищаем таймаут
      const timeout = this.callTimeouts.get(callSessionId);
      if (timeout) {
        clearTimeout(timeout);
        this.callTimeouts.delete(callSessionId);
      }

      // Обновляем сессию в базе
      const transcript = JSON.stringify(callData.transcript);
      await prisma.callSession.update({
        where: { id: callSessionId },
        data: {
          status: 'completed',
          endTime,
          duration,
          transcript
        }
      });

      // Генерируем финальное сообщение
      const finalMessage = reason === 'timeout' 
        ? this.generateTimeoutMessage()
        : this.generateCompletionMessage();

      // Запускаем анализ звонка
      this.analyzeCallWithGemini(callSessionId, callData);

      // Удаляем из активных звонков
      this.activeCalls.delete(callSessionId);

      console.log(`✅ Call ${callSessionId} ended: ${reason}, duration: ${duration}s`);

      return {
        success: true,
        finalMessage,
        duration,
        reason
      };

    } catch (error) {
      console.error('❌ Error ending call:', error);
      return { error: 'Failed to end call' };
    }
  }

  // Генерация сообщения о завершении времени
  generateTimeoutMessage() {
    return `
      Наше время подошло к концу! Спасибо за интересную беседу.
      
      Я проанализирую наш разговор и подготовлю для вас:
      - Персональные рекомендации по автоматизации
      - Расчет экономии времени и денег
      - Готовые промпты и инструменты
      - Варианты подписки со скидками
      
      Все материалы будут отправлены на ваш email в течение 10 минут.
      Также вы сможете найти их в личном кабинете на нашем сайте.
      
      До свидания! Жду вас в нашей платформе! 🚀
    `;
  }

  // Генерация сообщения о завершении
  generateCompletionMessage() {
    return `
      Отлично! Я получил всю необходимую информацию.
      
      Сейчас я проанализирую наш разговор и подготовлю персональные 
      рекомендации специально для ваших задач.
      
      В течение 10 минут вы получите на email:
      - Детальный анализ ваших потребностей
      - Конкретные решения для автоматизации
      - Расчет экономии времени и денег
      - Готовые промпты для внедрения
      
      Спасибо за время! Увидимся в личном кабинете! 🎯
    `;
  }

  // Анализ звонка с помощью Gemini
  async analyzeCallWithGemini(callSessionId, callData) {
    try {
      console.log(`🤖 Starting AI analysis for call ${callSessionId}`);

      const apiKey = await companyNumberService.getGeminiApiKey(callData.session.companyNumber);
      const genAI = new GoogleGenerativeAI(apiKey);
      const model = genAI.getGenerativeModel({ model: "gemini-pro" });

      const transcript = callData.transcript
        .map(entry => `${entry.speaker === 'client' ? 'Клиент' : 'AI'}: ${entry.message}`)
        .join('\n');

      const analysisPrompt = `
        Проанализируй этот разговор с клиентом и подготовь детальные рекомендации.
        
        ТРАНСКРИПТ РАЗГОВОРА:
        ${transcript}
        
        ЗАДАЧА:
        Создай JSON с анализом и рекомендациями в следующем формате:
        
        {
          "clientNeeds": "Краткое описание потребностей клиента",
          "businessType": "Тип бизнеса клиента",
          "currentChallenges": ["список текущих проблем"],
          "recommendedFeatures": [
            {
              "feature": "название функции",
              "description": "описание",
              "benefit": "польза для клиента",
              "implementation": "как внедрить"
            }
          ],
          "generatedPrompts": [
            {
              "type": "telegram_bot",
              "prompt": "готовый промпт для телеграм бота",
              "useCase": "для чего использовать"
            },
            {
              "type": "voice_assistant",
              "prompt": "промпт для голосового помощника",
              "useCase": "применение"
            }
          ],
          "automationSuggestions": [
            {
              "process": "процесс для автоматизации",
              "solution": "решение",
              "timeSavings": "экономия времени в часах/месяц",
              "moneySavings": "экономия денег в долларах/месяц"
            }
          ],
          "estimatedSavings": {
            "timePerMonth": "часов в месяц",
            "moneyPerMonth": "долларов в месяц",
            "currentCosts": "текущие расходы",
            "automationLevel": "low/medium/high"
          }
        }
        
        ВАЖНО: Отвечай только JSON, без дополнительного текста.
      `;

      const result = await model.generateContent(analysisPrompt);
      const analysisText = result.response.text();
      
      // Парсим JSON ответ
      let analysisData;
      try {
        // Убираем markdown форматирование если есть
        const cleanJson = analysisText.replace(/```json\n?|\n?```/g, '').trim();
        analysisData = JSON.parse(cleanJson);
      } catch (parseError) {
        console.error('❌ Error parsing analysis JSON:', parseError);
        analysisData = {
          clientNeeds: "Анализ в процессе обработки",
          recommendedFeatures: [],
          generatedPrompts: [],
          automationSuggestions: [],
          estimatedSavings: { timePerMonth: 0, moneyPerMonth: 0 }
        };
      }

      // Сохраняем анализ в базу
      await prisma.aIAnalysis.create({
        data: {
          userId: callData.user.id,
          callSessionId: callSessionId,
          clientNeeds: analysisData.clientNeeds,
          recommendedFeatures: JSON.stringify(analysisData.recommendedFeatures),
          generatedPrompts: JSON.stringify(analysisData.generatedPrompts),
          automationSuggestions: JSON.stringify(analysisData.automationSuggestions),
          geminiResponse: analysisText
        }
      });

      // Сохраняем расчет экономии
      if (analysisData.estimatedSavings) {
        await prisma.savingsCalculation.upsert({
          where: { userId: callData.user.id },
          update: {
            estimatedTimeSavings: parseInt(analysisData.estimatedSavings.timePerMonth) || 0,
            estimatedMoneySavings: parseFloat(analysisData.estimatedSavings.moneyPerMonth) || 0,
            currentCosts: parseFloat(analysisData.estimatedSavings.currentCosts) || 0,
            automationLevel: analysisData.estimatedSavings.automationLevel || 'medium',
            calculationData: JSON.stringify(analysisData)
          },
          create: {
            userId: callData.user.id,
            estimatedTimeSavings: parseInt(analysisData.estimatedSavings.timePerMonth) || 0,
            estimatedMoneySavings: parseFloat(analysisData.estimatedSavings.moneyPerMonth) || 0,
            currentCosts: parseFloat(analysisData.estimatedSavings.currentCosts) || 0,
            automationLevel: analysisData.estimatedSavings.automationLevel || 'medium',
            calculationData: JSON.stringify(analysisData)
          }
        });
      }

      // Обновляем статус пользователя
      await prisma.user.update({
        where: { id: callData.user.id },
        data: { registrationStep: 'analysis_done' }
      });

      // Отправляем email с результатами
      await emailService.sendAnalysisResultEmail(
        callData.user.email,
        callData.user.name,
        analysisData
      );

      console.log(`✅ AI analysis completed for user ${callData.user.name}`);

    } catch (error) {
      console.error('❌ Error analyzing call with Gemini:', error);
    }
  }

  // Получение сообщения отклонения
  getRejectMessage(reason) {
    const messages = {
      'Number not assigned': 'Извините, этот номер не назначен ни одному клиенту.',
      'Phone number mismatch': 'Извините, номер телефона не совпадает с зарегистрированным.',
      'Verification error': 'Произошла ошибка проверки. Попробуйте позже.'
    };

    return messages[reason] || 'Звонок не может быть принят.';
  }

  // Получение оставшегося времени
  getTimeRemaining(startTime) {
    const elapsed = Date.now() - startTime;
    const remaining = Math.max(0, (30 * 60 * 1000) - elapsed); // 30 минут
    return Math.floor(remaining / 1000); // в секундах
  }

  // Получение активных звонков
  getActiveCalls() {
    const calls = [];
    for (const [sessionId, callData] of this.activeCalls) {
      calls.push({
        sessionId,
        user: callData.user.name,
        phone: callData.session.clientPhone,
        duration: Math.floor((Date.now() - callData.startTime) / 1000),
        timeRemaining: this.getTimeRemaining(callData.startTime)
      });
    }
    return calls;
  }
}

module.exports = new AICallService();
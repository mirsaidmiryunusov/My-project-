const nodemailer = require('nodemailer');
const crypto = require('crypto');

class EmailService {
  constructor() {
    this.transporter = nodemailer.createTransporter({
      host: process.env.SMTP_HOST || 'smtp.gmail.com',
      port: process.env.SMTP_PORT || 587,
      secure: false,
      auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS
      }
    });
  }

  generateVerificationToken() {
    return crypto.randomBytes(32).toString('hex');
  }

  async sendVerificationEmail(email, token, name) {
    const verificationUrl = `${process.env.FRONTEND_URL}/verify-email?token=${token}`;
    
    const mailOptions = {
      from: `"GeminiVoice AI" <${process.env.SMTP_USER}>`,
      to: email,
      subject: '🎯 Подтвердите ваш email - GeminiVoice AI Call Center',
      html: `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
            .button { display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
            .features { background: white; padding: 20px; border-radius: 5px; margin: 20px 0; }
            .feature { margin: 10px 0; padding: 10px; border-left: 4px solid #667eea; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>🎯 Добро пожаловать в GeminiVoice AI!</h1>
              <p>Революционная платформа автоматизации звонков</p>
            </div>
            <div class="content">
              <h2>Привет, ${name}! 👋</h2>
              
              <p>Спасибо за регистрацию в GeminiVoice AI Call Center! Вы сделали первый шаг к автоматизации ваших бизнес-процессов.</p>
              
              <div style="text-align: center;">
                <a href="${verificationUrl}" class="button">✅ Подтвердить Email</a>
              </div>
              
              <div class="features">
                <h3>🚀 Что вас ждет после подтверждения:</h3>
                <div class="feature">📞 <strong>Персональный номер компании</strong> - получите свой уникальный номер для тестирования</div>
                <div class="feature">🤖 <strong>AI-консультация</strong> - 30-минутный разговор с ИИ для анализа ваших потребностей</div>
                <div class="feature">💡 <strong>Персональные рекомендации</strong> - получите готовые решения для автоматизации</div>
                <div class="feature">💰 <strong>Расчет экономии</strong> - узнайте, сколько времени и денег сэкономите</div>
                <div class="feature">🎯 <strong>Готовые промпты</strong> - получите настроенные промпты для ваших задач</div>
              </div>
              
              <p><strong>Следующие шаги:</strong></p>
              <ol>
                <li>Подтвердите email по ссылке выше</li>
                <li>Укажите ваш номер телефона</li>
                <li>Получите персональный номер компании</li>
                <li>Пройдите AI-консультацию</li>
                <li>Получите персональные рекомендации</li>
              </ol>
              
              <p style="color: #666; font-size: 14px;">
                Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо.
                <br>Ссылка действительна в течение 24 часов.
              </p>
            </div>
          </div>
        </body>
        </html>
      `
    };

    try {
      await this.transporter.sendMail(mailOptions);
      console.log(`✅ Verification email sent to ${email}`);
      return true;
    } catch (error) {
      console.error('❌ Error sending verification email:', error);
      return false;
    }
  }

  async sendWelcomeEmail(email, name, assignedNumber) {
    const mailOptions = {
      from: `"GeminiVoice AI" <${process.env.SMTP_USER}>`,
      to: email,
      subject: '🎉 Ваш персональный номер готов! - GeminiVoice AI',
      html: `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
            .number-box { background: white; border: 2px solid #667eea; padding: 20px; text-align: center; border-radius: 10px; margin: 20px 0; }
            .number { font-size: 24px; font-weight: bold; color: #667eea; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>🎉 Поздравляем, ${name}!</h1>
              <p>Ваш персональный номер готов к использованию</p>
            </div>
            <div class="content">
              <div class="number-box">
                <h3>📞 Ваш персональный номер компании:</h3>
                <div class="number">${assignedNumber}</div>
                <p style="color: #666;">Позвоните на этот номер для AI-консультации</p>
              </div>
              
              <h3>🤖 Что произойдет при звонке:</h3>
              <ol>
                <li><strong>Проверка номера</strong> - система проверит, что звоните именно вы</li>
                <li><strong>Приветствие</strong> - ИИ поприветствует вас и расскажет о возможностях</li>
                <li><strong>Анализ потребностей</strong> - 30-минутная консультация о ваших задачах</li>
                <li><strong>Рекомендации</strong> - получите персональные решения для автоматизации</li>
              </ol>
              
              <p><strong>💡 Подготовьтесь к звонку:</strong></p>
              <ul>
                <li>Подумайте о задачах, которые хотите автоматизировать</li>
                <li>Приготовьте информацию о вашем бизнесе</li>
                <li>Выделите 30 минут свободного времени</li>
              </ul>
              
              <p style="text-align: center; margin-top: 30px;">
                <strong>Готовы начать? Позвоните на ваш номер прямо сейчас! 📞</strong>
              </p>
            </div>
          </div>
        </body>
        </html>
      `
    };

    try {
      await this.transporter.sendMail(mailOptions);
      console.log(`✅ Welcome email sent to ${email}`);
      return true;
    } catch (error) {
      console.error('❌ Error sending welcome email:', error);
      return false;
    }
  }

  async sendAnalysisResultEmail(email, name, analysis) {
    const mailOptions = {
      from: `"GeminiVoice AI" <${process.env.SMTP_USER}>`,
      to: email,
      subject: '🎯 Ваши персональные рекомендации готовы! - GeminiVoice AI',
      html: `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
            .analysis-box { background: white; padding: 20px; border-radius: 10px; margin: 20px 0; border-left: 4px solid #667eea; }
            .button { display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>🎯 Анализ завершен, ${name}!</h1>
              <p>Ваши персональные рекомендации готовы</p>
            </div>
            <div class="content">
              <div class="analysis-box">
                <h3>🤖 Анализ ваших потребностей:</h3>
                <p>${analysis.clientNeeds || 'Анализ в процессе обработки...'}</p>
              </div>
              
              <div class="analysis-box">
                <h3>💡 Рекомендуемые функции:</h3>
                <p>${analysis.recommendedFeatures || 'Рекомендации формируются...'}</p>
              </div>
              
              <div class="analysis-box">
                <h3>🎯 Готовые промпты:</h3>
                <p>${analysis.generatedPrompts || 'Промпты генерируются...'}</p>
              </div>
              
              <div style="text-align: center;">
                <a href="${process.env.FRONTEND_URL}/dashboard" class="button">🚀 Перейти в личный кабинет</a>
              </div>
              
              <p>В личном кабинете вы найдете:</p>
              <ul>
                <li>📊 Детальный расчет экономии времени и денег</li>
                <li>🛠️ Готовые инструменты для автоматизации</li>
                <li>📋 Пошаговый план внедрения</li>
                <li>💳 Варианты подписки с персональными скидками</li>
              </ul>
            </div>
          </div>
        </body>
        </html>
      `
    };

    try {
      await this.transporter.sendMail(mailOptions);
      console.log(`✅ Analysis result email sent to ${email}`);
      return true;
    } catch (error) {
      console.error('❌ Error sending analysis result email:', error);
      return false;
    }
  }
}

module.exports = new EmailService();
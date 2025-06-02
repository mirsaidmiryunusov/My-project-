"""
Telegram Sales Bot - AI инструмент для продаж через Telegram
Интегрируется с системой звонков для автоматической обработки лидов
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import aiohttp
import structlog
from sqlmodel import Session, select
from database import get_db_manager
from models import User, ConversationContext, Modem

logger = structlog.get_logger(__name__)


@dataclass
class TelegramMessage:
    """Структура сообщения Telegram"""
    chat_id: str
    message_id: int
    text: str
    from_user: Dict[str, Any]
    timestamp: datetime


@dataclass
class SalesLead:
    """Структура лида для продаж"""
    phone_number: str
    client_name: Optional[str]
    call_summary: str
    interests: List[str]
    budget_range: Optional[str]
    urgency: str  # high, medium, low
    next_action: str
    telegram_chat_id: Optional[str] = None


class TelegramSalesBot:
    """
    AI Telegram бот для продаж с интеграцией звонков
    """
    
    def __init__(self, bot_token: str, sales_chat_id: str):
        self.bot_token = bot_token
        self.sales_chat_id = sales_chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.db_manager = get_db_manager()
        self.engine = self.db_manager.engine
        
        # Промпты для AI анализа
        self.sales_prompts = {
            "lead_analysis": """
Проанализируй звонок клиента и создай профиль лида для продаж:

Информация о звонке:
- Номер телефона: {phone_number}
- Время звонка: {call_time}
- Продолжительность: {duration}
- Краткое содержание: {summary}

Определи:
1. Потенциальные интересы клиента
2. Примерный бюджет (если упоминался)
3. Уровень срочности (высокий/средний/низкий)
4. Рекомендуемые следующие действия
5. Подходящие продукты/услуги

Ответь в формате JSON:
{{
    "interests": ["интерес1", "интерес2"],
    "budget_range": "примерный бюджет или null",
    "urgency": "high/medium/low",
    "next_action": "рекомендуемое действие",
    "recommended_products": ["продукт1", "продукт2"],
    "sales_notes": "заметки для менеджера"
}}
""",
            
            "follow_up_message": """
Создай персонализированное сообщение для отправки клиенту в Telegram:

Профиль клиента:
- Интересы: {interests}
- Обсуждалось в звонке: {call_summary}
- Уровень срочности: {urgency}

Создай дружелюбное сообщение, которое:
1. Благодарит за звонок
2. Кратко резюмирует обсуждение
3. Предлагает конкретные решения
4. Содержит призыв к действию
5. Не превышает 200 слов

Тон: профессиональный, но дружелюбный
""",
            
            "sales_report": """
Создай краткий отчет о лиде для команды продаж:

Данные лида:
- Телефон: {phone_number}
- Интересы: {interests}
- Бюджет: {budget_range}
- Срочность: {urgency}
- Заметки: {sales_notes}

Создай структурированный отчет для менеджера продаж с рекомендациями по работе с этим лидом.
"""
        }
    
    async def process_call_for_sales(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка звонка для создания лида продаж
        """
        try:
            phone_number = call_data.get("phone_number")
            call_summary = call_data.get("summary", "")
            call_duration = call_data.get("duration", 0)
            call_time = call_data.get("timestamp", datetime.now())
            
            logger.info("Processing call for sales", phone_number=phone_number)
            
            # 1. Анализ звонка с помощью AI
            lead_analysis = await self._analyze_call_with_ai(
                phone_number, call_summary, call_duration, call_time
            )
            
            if not lead_analysis:
                return {"success": False, "error": "Failed to analyze call"}
            
            # 2. Создание лида
            sales_lead = SalesLead(
                phone_number=phone_number,
                client_name=call_data.get("client_name"),
                call_summary=call_summary,
                interests=lead_analysis.get("interests", []),
                budget_range=lead_analysis.get("budget_range"),
                urgency=lead_analysis.get("urgency", "medium"),
                next_action=lead_analysis.get("next_action", "")
            )
            
            # 3. Сохранение в базу данных
            await self._save_sales_lead(sales_lead)
            
            # 4. Отправка уведомления команде продаж
            await self._notify_sales_team(sales_lead, lead_analysis)
            
            # 5. Отправка follow-up сообщения клиенту (если есть Telegram)
            client_telegram = await self._find_client_telegram(phone_number)
            if client_telegram:
                await self._send_follow_up_message(client_telegram, sales_lead)
            
            return {
                "success": True,
                "lead_id": f"lead_{phone_number}_{int(call_time.timestamp())}",
                "analysis": lead_analysis,
                "actions_taken": [
                    "Lead created",
                    "Sales team notified",
                    "Follow-up scheduled" if client_telegram else "No Telegram contact"
                ]
            }
            
        except Exception as e:
            logger.error("Failed to process call for sales", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _analyze_call_with_ai(self, phone_number: str, summary: str, 
                                   duration: int, call_time: datetime) -> Optional[Dict[str, Any]]:
        """
        Анализ звонка с помощью AI для создания профиля лида
        """
        try:
            # Здесь интеграция с Gemini API для анализа
            prompt = self.sales_prompts["lead_analysis"].format(
                phone_number=phone_number,
                call_time=call_time.strftime("%Y-%m-%d %H:%M"),
                duration=f"{duration} секунд",
                summary=summary
            )
            
            # Симуляция AI анализа (в реальности здесь будет вызов Gemini API)
            analysis = await self._simulate_ai_analysis(summary)
            
            logger.info("Call analysis completed", phone_number=phone_number)
            return analysis
            
        except Exception as e:
            logger.error("AI analysis failed", error=str(e))
            return None
    
    async def _simulate_ai_analysis(self, summary: str) -> Dict[str, Any]:
        """
        Симуляция AI анализа (заменить на реальный вызов Gemini API)
        """
        # Простой анализ на основе ключевых слов
        interests = []
        urgency = "medium"
        budget_range = None
        
        summary_lower = summary.lower()
        
        # Определение интересов
        if any(word in summary_lower for word in ["автоматизация", "crm", "система"]):
            interests.append("CRM и автоматизация")
        if any(word in summary_lower for word in ["звонки", "колл-центр", "телефония"]):
            interests.append("Телефония и колл-центр")
        if any(word in summary_lower for word in ["ai", "ии", "искусственный интеллект"]):
            interests.append("AI решения")
        
        # Определение срочности
        if any(word in summary_lower for word in ["срочно", "быстро", "сегодня"]):
            urgency = "high"
        elif any(word in summary_lower for word in ["подумать", "позже", "не спешим"]):
            urgency = "low"
        
        # Определение бюджета
        if any(word in summary_lower for word in ["бюджет", "стоимость", "цена"]):
            if any(word in summary_lower for word in ["дорого", "дешево"]):
                budget_range = "Обсуждался бюджет"
        
        return {
            "interests": interests if interests else ["Общий интерес к услугам"],
            "budget_range": budget_range,
            "urgency": urgency,
            "next_action": "Связаться в течение 24 часов",
            "recommended_products": ["AI Call Center", "CRM Integration"],
            "sales_notes": f"Клиент проявил интерес. Краткое содержание: {summary[:100]}..."
        }
    
    async def _save_sales_lead(self, lead: SalesLead) -> None:
        """
        Сохранение лида в базу данных
        """
        try:
            with Session(self.engine) as session:
                # Создаем запись в контексте разговора
                context = ConversationContext(
                    phone_number=lead.phone_number,
                    context_data={
                        "type": "sales_lead",
                        "interests": lead.interests,
                        "budget_range": lead.budget_range,
                        "urgency": lead.urgency,
                        "next_action": lead.next_action,
                        "call_summary": lead.call_summary,
                        "created_at": datetime.now().isoformat()
                    },
                    created_at=datetime.now()
                )
                session.add(context)
                session.commit()
                
                logger.info("Sales lead saved", phone_number=lead.phone_number)
                
        except Exception as e:
            logger.error("Failed to save sales lead", error=str(e))
    
    async def _notify_sales_team(self, lead: SalesLead, analysis: Dict[str, Any]) -> None:
        """
        Уведомление команды продаж о новом лиде
        """
        try:
            # Создание отчета для команды
            report = f"""
🔥 **НОВЫЙ ЛИД**

📞 **Телефон:** `{lead.phone_number}`
⏰ **Время звонка:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

💡 **Интересы:**
{chr(10).join([f"• {interest}" for interest in lead.interests])}

💰 **Бюджет:** {lead.budget_range or 'Не обсуждался'}
🚨 **Срочность:** {self._get_urgency_emoji(lead.urgency)} {lead.urgency.upper()}

📋 **Краткое содержание:**
{lead.call_summary[:200]}...

🎯 **Рекомендуемые действия:**
{lead.next_action}

📦 **Подходящие продукты:**
{chr(10).join([f"• {product}" for product in analysis.get('recommended_products', [])])}

📝 **Заметки:**
{analysis.get('sales_notes', 'Нет дополнительных заметок')}
"""
            
            await self._send_telegram_message(self.sales_chat_id, report)
            logger.info("Sales team notified", phone_number=lead.phone_number)
            
        except Exception as e:
            logger.error("Failed to notify sales team", error=str(e))
    
    def _get_urgency_emoji(self, urgency: str) -> str:
        """Получение эмодзи для уровня срочности"""
        return {
            "high": "🔴",
            "medium": "🟡", 
            "low": "🟢"
        }.get(urgency, "🟡")
    
    async def _find_client_telegram(self, phone_number: str) -> Optional[str]:
        """
        Поиск Telegram чата клиента по номеру телефона
        """
        try:
            with Session(self.engine) as session:
                # Поиск пользователя по номеру телефона
                user = session.exec(
                    select(User).where(User.phone_number == phone_number)
                ).first()
                
                if user and hasattr(user, 'telegram_chat_id'):
                    return user.telegram_chat_id
                
                return None
                
        except Exception as e:
            logger.error("Failed to find client telegram", error=str(e))
            return None
    
    async def _send_follow_up_message(self, chat_id: str, lead: SalesLead) -> None:
        """
        Отправка follow-up сообщения клиенту
        """
        try:
            # Создание персонализированного сообщения
            message = f"""
Здравствуйте! 👋

Спасибо за звонок сегодня. Было приятно с вами пообщаться!

📋 **Краткое резюме нашего разговора:**
{lead.call_summary[:150]}...

💡 **Что мы можем предложить:**
{chr(10).join([f"• {interest}" for interest in lead.interests[:3]])}

🎯 **Следующие шаги:**
{lead.next_action}

Если у вас есть дополнительные вопросы, не стесняйтесь писать! Мы готовы помочь вам найти идеальное решение.

С уважением,
Команда AI Call Center 🤖
"""
            
            await self._send_telegram_message(chat_id, message)
            logger.info("Follow-up message sent", phone_number=lead.phone_number)
            
        except Exception as e:
            logger.error("Failed to send follow-up message", error=str(e))
    
    async def _send_telegram_message(self, chat_id: str, text: str) -> bool:
        """
        Отправка сообщения в Telegram
        """
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        logger.info("Telegram message sent", chat_id=chat_id)
                        return True
                    else:
                        logger.error("Failed to send telegram message", 
                                   status=response.status, chat_id=chat_id)
                        return False
                        
        except Exception as e:
            logger.error("Telegram API error", error=str(e))
            return False
    
    async def handle_incoming_message(self, message: TelegramMessage) -> None:
        """
        Обработка входящих сообщений от клиентов
        """
        try:
            # Проверка, является ли отправитель существующим лидом
            lead_info = await self._get_lead_by_chat_id(message.chat_id)
            
            if lead_info:
                # Обновление информации о лиде
                await self._update_lead_interaction(message, lead_info)
                
                # Уведомление команды продаж о новом сообщении
                await self._notify_new_client_message(message, lead_info)
            else:
                # Новый потенциальный клиент
                await self._handle_new_potential_client(message)
                
        except Exception as e:
            logger.error("Failed to handle incoming message", error=str(e))
    
    async def _get_lead_by_chat_id(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение информации о лиде по chat_id
        """
        try:
            with Session(self.engine) as session:
                context = session.exec(
                    select(ConversationContext).where(
                        ConversationContext.context_data.contains(f'"telegram_chat_id": "{chat_id}"')
                    )
                ).first()
                
                if context:
                    return context.context_data
                return None
                
        except Exception as e:
            logger.error("Failed to get lead by chat_id", error=str(e))
            return None
    
    async def _update_lead_interaction(self, message: TelegramMessage, lead_info: Dict[str, Any]) -> None:
        """
        Обновление взаимодействия с лидом
        """
        try:
            # Добавление нового сообщения в историю
            if "messages" not in lead_info:
                lead_info["messages"] = []
            
            lead_info["messages"].append({
                "timestamp": message.timestamp.isoformat(),
                "text": message.text,
                "from": "client"
            })
            
            # Обновление в базе данных
            with Session(self.engine) as session:
                context = session.exec(
                    select(ConversationContext).where(
                        ConversationContext.context_data.contains(f'"telegram_chat_id": "{message.chat_id}"')
                    )
                ).first()
                
                if context:
                    context.context_data = lead_info
                    session.commit()
                    
        except Exception as e:
            logger.error("Failed to update lead interaction", error=str(e))
    
    async def _notify_new_client_message(self, message: TelegramMessage, lead_info: Dict[str, Any]) -> None:
        """
        Уведомление команды о новом сообщении от клиента
        """
        try:
            notification = f"""
💬 **НОВОЕ СООБЩЕНИЕ ОТ КЛИЕНТА**

📞 **Лид:** {lead_info.get('phone_number', 'Неизвестен')}
👤 **Telegram:** @{message.from_user.get('username', 'Нет username')}
⏰ **Время:** {message.timestamp.strftime('%d.%m.%Y %H:%M')}

💭 **Сообщение:**
{message.text}

🔗 **Ответить:** [Перейти в чат](tg://user?id={message.chat_id})
"""
            
            await self._send_telegram_message(self.sales_chat_id, notification)
            
        except Exception as e:
            logger.error("Failed to notify about new client message", error=str(e))
    
    async def _handle_new_potential_client(self, message: TelegramMessage) -> None:
        """
        Обработка нового потенциального клиента
        """
        try:
            # Автоматический ответ новому клиенту
            welcome_message = """
Здравствуйте! 👋

Спасибо за обращение к нам! Мы специализируемся на AI решениях для автоматизации бизнеса.

🤖 **Наши услуги:**
• AI Call Center с голосовыми ботами
• CRM интеграции и автоматизация
• Telegram боты для бизнеса
• Аналитика и отчетность

📞 **Хотите узнать больше?**
Позвоните нам или опишите вашу задачу здесь, и мы подберем оптимальное решение!

С уважением,
Команда AI Call Center
"""
            
            await self._send_telegram_message(message.chat_id, welcome_message)
            
            # Уведомление команды о новом потенциальном клиенте
            team_notification = f"""
🆕 **НОВЫЙ ПОТЕНЦИАЛЬНЫЙ КЛИЕНТ**

👤 **Telegram:** @{message.from_user.get('username', 'Нет username')}
🆔 **Chat ID:** {message.chat_id}
⏰ **Время:** {message.timestamp.strftime('%d.%m.%Y %H:%M')}

💭 **Первое сообщение:**
{message.text}

✅ **Отправлен приветственный ответ**
"""
            
            await self._send_telegram_message(self.sales_chat_id, team_notification)
            
        except Exception as e:
            logger.error("Failed to handle new potential client", error=str(e))
    
    async def get_sales_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики продаж
        """
        try:
            with Session(self.engine) as session:
                # Подсчет лидов за разные периоды
                today = datetime.now().date()
                week_ago = today - timedelta(days=7)
                month_ago = today - timedelta(days=30)
                
                # Общее количество лидов
                total_leads = session.exec(
                    select(ConversationContext).where(
                        ConversationContext.context_data.contains('"type": "sales_lead"')
                    )
                ).all()
                
                # Статистика по срочности
                urgency_stats = {"high": 0, "medium": 0, "low": 0}
                for lead in total_leads:
                    urgency = lead.context_data.get("urgency", "medium")
                    urgency_stats[urgency] += 1
                
                return {
                    "total_leads": len(total_leads),
                    "leads_today": len([l for l in total_leads if l.created_at.date() == today]),
                    "leads_this_week": len([l for l in total_leads if l.created_at.date() >= week_ago]),
                    "leads_this_month": len([l for l in total_leads if l.created_at.date() >= month_ago]),
                    "urgency_distribution": urgency_stats,
                    "last_updated": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error("Failed to get sales statistics", error=str(e))
            return {"error": str(e)}


# Функция для создания экземпляра бота
def create_sales_bot(bot_token: str, sales_chat_id: str) -> TelegramSalesBot:
    """
    Создание экземпляра Telegram Sales Bot
    """
    return TelegramSalesBot(bot_token, sales_chat_id)


# Пример использования
async def example_usage():
    """
    Пример использования Telegram Sales Bot
    """
    # Создание бота
    bot = create_sales_bot(
        bot_token="YOUR_BOT_TOKEN",
        sales_chat_id="YOUR_SALES_CHAT_ID"
    )
    
    # Обработка звонка
    call_data = {
        "phone_number": "+1234567890",
        "summary": "Клиент интересуется автоматизацией колл-центра с помощью AI",
        "duration": 180,
        "timestamp": datetime.now(),
        "client_name": "Иван Петров"
    }
    
    result = await bot.process_call_for_sales(call_data)
    print("Результат обработки звонка:", result)
    
    # Получение статистики
    stats = await bot.get_sales_statistics()
    print("Статистика продаж:", stats)


if __name__ == "__main__":
    asyncio.run(example_usage())
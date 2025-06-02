"""
Universal Telegram AI Bot - Универсальный AI инструмент для любых задач клиента
Выполняет задачи на основе промптов из звонков клиентов
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
class ClientRequest:
    """Структура запроса клиента"""
    phone_number: str
    client_name: Optional[str]
    call_summary: str
    client_needs: List[str]
    requested_actions: List[str]
    priority: str  # urgent, normal, low
    category: str  # support, automation, integration, custom
    telegram_chat_id: Optional[str] = None


@dataclass
class AITask:
    """Структура AI задачи"""
    task_id: str
    client_phone: str
    task_type: str
    description: str
    ai_prompt: str
    status: str  # pending, processing, completed, failed
    result: Optional[Dict[str, Any]] = None
    created_at: datetime = None


class TelegramUniversalBot:
    """
    Универсальный AI Telegram бот для выполнения любых задач клиента
    """
    
    def __init__(self, bot_token: str, notification_chat_id: str):
        self.bot_token = bot_token
        self.notification_chat_id = notification_chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.db_manager = get_db_manager()
        self.engine = self.db_manager.engine
        
        # Универсальные промпты для разных типов задач
        self.ai_prompts = {
            "task_analysis": """
Проанализируй звонок клиента и определи, что именно он хочет автоматизировать или какую помощь получить:

Информация о звонке:
- Номер телефона: {phone_number}
- Время звонка: {call_time}
- Продолжительность: {duration}
- Содержание разговора: {summary}

Определи:
1. Основные потребности клиента
2. Какие задачи он хочет автоматизировать
3. Какие инструменты/сервисы ему нужны
4. Приоритет задач (срочно/обычно/не спешит)
5. Категорию запроса (поддержка/автоматизация/интеграция/особое)
6. Конкретные действия, которые нужно выполнить

Ответь в формате JSON:
{{
    "client_needs": ["потребность1", "потребность2"],
    "requested_actions": ["действие1", "действие2"],
    "priority": "urgent/normal/low",
    "category": "support/automation/integration/custom",
    "recommended_tools": ["инструмент1", "инструмент2"],
    "next_steps": "что делать дальше",
    "ai_tasks": [
        {{
            "task_type": "тип задачи",
            "description": "описание задачи",
            "ai_prompt": "промпт для выполнения задачи"
        }}
    ]
}}
""",
            
            "client_response": """
Создай персонализированный ответ клиенту на основе его запроса:

Запрос клиента:
- Потребности: {client_needs}
- Запрошенные действия: {requested_actions}
- Категория: {category}
- Приоритет: {priority}

Создай дружелюбное сообщение, которое:
1. Подтверждает понимание запроса
2. Объясняет, что будет сделано
3. Указывает примерные сроки
4. Предлагает дополнительную помощь
5. Содержит контактную информацию

Тон: профессиональный, понимающий, готовый помочь
""",
            
            "task_execution": """
Выполни следующую задачу для клиента:

Тип задачи: {task_type}
Описание: {description}
Контекст клиента: {client_context}

Задача: {ai_prompt}

Выполни задачу и предоставь результат в структурированном виде.
""",
            
            "team_notification": """
Создай уведомление для команды о новом запросе клиента:

Данные клиента:
- Телефон: {phone_number}
- Потребности: {client_needs}
- Приоритет: {priority}
- Категория: {category}
- Запрошенные действия: {requested_actions}

Создай краткое, но информативное уведомление для команды.
"""
        }
        
        # Доступные AI инструменты для выполнения задач
        self.available_tools = {
            "email_automation": {
                "name": "Email автоматизация",
                "description": "Настройка автоматических email рассылок",
                "capabilities": ["send_emails", "create_templates", "schedule_campaigns"]
            },
            "calendar_management": {
                "name": "Управление календарем",
                "description": "Автоматическое планирование встреч и событий",
                "capabilities": ["schedule_meetings", "send_reminders", "sync_calendars"]
            },
            "crm_integration": {
                "name": "CRM интеграция",
                "description": "Подключение и настройка CRM систем",
                "capabilities": ["sync_contacts", "track_deals", "generate_reports"]
            },
            "social_media": {
                "name": "Социальные сети",
                "description": "Автоматизация постов и взаимодействий",
                "capabilities": ["schedule_posts", "respond_messages", "analyze_engagement"]
            },
            "document_processing": {
                "name": "Обработка документов",
                "description": "Автоматическая обработка и анализ документов",
                "capabilities": ["extract_data", "generate_reports", "convert_formats"]
            },
            "payment_processing": {
                "name": "Обработка платежей",
                "description": "Настройка автоматических платежей",
                "capabilities": ["process_payments", "send_invoices", "track_transactions"]
            },
            "customer_support": {
                "name": "Поддержка клиентов",
                "description": "Автоматизация службы поддержки",
                "capabilities": ["auto_responses", "ticket_routing", "knowledge_base"]
            },
            "data_analytics": {
                "name": "Аналитика данных",
                "description": "Анализ и визуализация данных",
                "capabilities": ["generate_insights", "create_dashboards", "predict_trends"]
            },
            "workflow_automation": {
                "name": "Автоматизация процессов",
                "description": "Создание автоматических рабочих процессов",
                "capabilities": ["create_workflows", "trigger_actions", "monitor_processes"]
            },
            "communication": {
                "name": "Коммуникации",
                "description": "Автоматизация общения с клиентами",
                "capabilities": ["send_notifications", "manage_chats", "schedule_calls"]
            }
        }
    
    async def process_client_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка звонка клиента для выполнения его запросов
        """
        try:
            phone_number = call_data.get("phone_number")
            call_summary = call_data.get("summary", "")
            call_duration = call_data.get("duration", 0)
            call_time = call_data.get("timestamp", datetime.now())
            
            logger.info("Processing client call", phone_number=phone_number)
            
            # 1. Анализ звонка с помощью AI
            analysis = await self._analyze_client_request(
                phone_number, call_summary, call_duration, call_time
            )
            
            if not analysis:
                return {"success": False, "error": "Failed to analyze call"}
            
            # 2. Создание запроса клиента
            client_request = ClientRequest(
                phone_number=phone_number,
                client_name=call_data.get("client_name"),
                call_summary=call_summary,
                client_needs=analysis.get("client_needs", []),
                requested_actions=analysis.get("requested_actions", []),
                priority=analysis.get("priority", "normal"),
                category=analysis.get("category", "custom")
            )
            
            # 3. Сохранение запроса
            await self._save_client_request(client_request)
            
            # 4. Создание AI задач
            ai_tasks = analysis.get("ai_tasks", [])
            created_tasks = []
            
            for task_data in ai_tasks:
                task = await self._create_ai_task(client_request, task_data)
                if task:
                    created_tasks.append(task)
            
            # 5. Уведомление команды
            await self._notify_team(client_request, analysis)
            
            # 6. Ответ клиенту
            client_telegram = await self._find_client_telegram(phone_number)
            if client_telegram:
                await self._send_client_response(client_telegram, client_request)
            
            # 7. Запуск выполнения задач
            for task in created_tasks:
                await self._execute_ai_task(task)
            
            return {
                "success": True,
                "request_id": f"req_{phone_number}_{int(call_time.timestamp())}",
                "analysis": analysis,
                "tasks_created": len(created_tasks),
                "actions_taken": [
                    "Request analyzed",
                    "Tasks created",
                    "Team notified",
                    "Client contacted" if client_telegram else "No Telegram contact",
                    "Tasks execution started"
                ]
            }
            
        except Exception as e:
            logger.error("Failed to process client call", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _analyze_client_request(self, phone_number: str, summary: str, 
                                    duration: int, call_time: datetime) -> Optional[Dict[str, Any]]:
        """
        Анализ запроса клиента с помощью AI
        """
        try:
            prompt = self.ai_prompts["task_analysis"].format(
                phone_number=phone_number,
                call_time=call_time.strftime("%Y-%m-%d %H:%M"),
                duration=f"{duration} секунд",
                summary=summary
            )
            
            # Симуляция AI анализа (в реальности здесь будет вызов Gemini API)
            analysis = await self._simulate_ai_analysis(summary)
            
            logger.info("Client request analysis completed", phone_number=phone_number)
            return analysis
            
        except Exception as e:
            logger.error("AI analysis failed", error=str(e))
            return None
    
    async def _simulate_ai_analysis(self, summary: str) -> Dict[str, Any]:
        """
        Симуляция AI анализа запроса клиента
        """
        summary_lower = summary.lower()
        
        # Определение потребностей клиента
        client_needs = []
        requested_actions = []
        category = "custom"
        priority = "normal"
        
        # Анализ ключевых слов для определения потребностей
        if any(word in summary_lower for word in ["автоматизация", "автоматический", "автомат"]):
            client_needs.append("Автоматизация процессов")
            category = "automation"
            
        if any(word in summary_lower for word in ["email", "почта", "письма", "рассылка"]):
            client_needs.append("Email маркетинг")
            requested_actions.append("Настроить email автоматизацию")
            
        if any(word in summary_lower for word in ["календарь", "встречи", "планирование"]):
            client_needs.append("Управление календарем")
            requested_actions.append("Автоматизировать планирование встреч")
            
        if any(word in summary_lower for word in ["crm", "клиенты", "контакты"]):
            client_needs.append("CRM система")
            requested_actions.append("Настроить CRM интеграцию")
            
        if any(word in summary_lower for word in ["соцсети", "instagram", "facebook", "вконтакте"]):
            client_needs.append("Социальные сети")
            requested_actions.append("Автоматизировать посты в соцсетях")
            
        if any(word in summary_lower for word in ["документы", "файлы", "обработка"]):
            client_needs.append("Обработка документов")
            requested_actions.append("Автоматизировать обработку документов")
            
        if any(word in summary_lower for word in ["платежи", "оплата", "счета"]):
            client_needs.append("Платежная система")
            requested_actions.append("Настроить автоматические платежи")
            
        if any(word in summary_lower for word in ["поддержка", "чат", "ответы"]):
            client_needs.append("Служба поддержки")
            requested_actions.append("Создать автоматические ответы")
            category = "support"
            
        if any(word in summary_lower for word in ["аналитика", "отчеты", "статистика"]):
            client_needs.append("Аналитика и отчеты")
            requested_actions.append("Настроить автоматические отчеты")
            
        if any(word in summary_lower for word in ["уведомления", "напоминания", "alerts"]):
            client_needs.append("Уведомления")
            requested_actions.append("Настроить автоматические уведомления")
        
        # Определение приоритета
        if any(word in summary_lower for word in ["срочно", "быстро", "сегодня", "немедленно"]):
            priority = "urgent"
        elif any(word in summary_lower for word in ["не спешим", "когда удобно", "не срочно"]):
            priority = "low"
        
        # Если ничего не определилось, добавляем общие потребности
        if not client_needs:
            client_needs = ["Консультация по автоматизации"]
            requested_actions = ["Провести анализ потребностей"]
        
        # Создание AI задач
        ai_tasks = []
        for action in requested_actions:
            ai_tasks.append({
                "task_type": "automation_setup",
                "description": action,
                "ai_prompt": f"Помоги клиенту с задачей: {action}. Контекст: {summary[:200]}..."
            })
        
        return {
            "client_needs": client_needs,
            "requested_actions": requested_actions,
            "priority": priority,
            "category": category,
            "recommended_tools": self._get_recommended_tools(client_needs),
            "next_steps": "Связаться с клиентом для уточнения деталей",
            "ai_tasks": ai_tasks
        }
    
    def _get_recommended_tools(self, client_needs: List[str]) -> List[str]:
        """
        Получение рекомендуемых инструментов на основе потребностей клиента
        """
        recommended = []
        
        for need in client_needs:
            need_lower = need.lower()
            
            if "email" in need_lower:
                recommended.append("email_automation")
            if "календар" in need_lower or "встреч" in need_lower:
                recommended.append("calendar_management")
            if "crm" in need_lower or "клиент" in need_lower:
                recommended.append("crm_integration")
            if "соц" in need_lower:
                recommended.append("social_media")
            if "документ" in need_lower:
                recommended.append("document_processing")
            if "платеж" in need_lower:
                recommended.append("payment_processing")
            if "поддержк" in need_lower:
                recommended.append("customer_support")
            if "аналитик" in need_lower:
                recommended.append("data_analytics")
            if "автоматизац" in need_lower:
                recommended.append("workflow_automation")
            if "уведомлен" in need_lower:
                recommended.append("communication")
        
        return list(set(recommended)) if recommended else ["workflow_automation"]
    
    async def _save_client_request(self, request: ClientRequest) -> None:
        """
        Сохранение запроса клиента в базу данных
        """
        try:
            with Session(self.engine) as session:
                context = ConversationContext(
                    phone_number=request.phone_number,
                    context_data={
                        "type": "client_request",
                        "client_name": request.client_name,
                        "client_needs": request.client_needs,
                        "requested_actions": request.requested_actions,
                        "priority": request.priority,
                        "category": request.category,
                        "call_summary": request.call_summary,
                        "created_at": datetime.now().isoformat()
                    },
                    created_at=datetime.now()
                )
                session.add(context)
                session.commit()
                
                logger.info("Client request saved", phone_number=request.phone_number)
                
        except Exception as e:
            logger.error("Failed to save client request", error=str(e))
    
    async def _create_ai_task(self, request: ClientRequest, task_data: Dict[str, Any]) -> Optional[AITask]:
        """
        Создание AI задачи
        """
        try:
            task = AITask(
                task_id=f"task_{request.phone_number}_{int(datetime.now().timestamp())}",
                client_phone=request.phone_number,
                task_type=task_data["task_type"],
                description=task_data["description"],
                ai_prompt=task_data["ai_prompt"],
                status="pending",
                created_at=datetime.now()
            )
            
            # Сохранение задачи в базу данных
            with Session(self.engine) as session:
                context = ConversationContext(
                    phone_number=request.phone_number,
                    context_data={
                        "type": "ai_task",
                        "task_id": task.task_id,
                        "task_type": task.task_type,
                        "description": task.description,
                        "ai_prompt": task.ai_prompt,
                        "status": task.status,
                        "created_at": task.created_at.isoformat()
                    },
                    created_at=datetime.now()
                )
                session.add(context)
                session.commit()
            
            logger.info("AI task created", task_id=task.task_id)
            return task
            
        except Exception as e:
            logger.error("Failed to create AI task", error=str(e))
            return None
    
    async def _execute_ai_task(self, task: AITask) -> None:
        """
        Выполнение AI задачи
        """
        try:
            logger.info("Executing AI task", task_id=task.task_id)
            
            # Обновление статуса
            await self._update_task_status(task.task_id, "processing")
            
            # Симуляция выполнения задачи
            result = await self._simulate_task_execution(task)
            
            # Сохранение результата
            await self._save_task_result(task.task_id, result)
            
            # Уведомление о завершении
            await self._notify_task_completion(task, result)
            
            logger.info("AI task completed", task_id=task.task_id)
            
        except Exception as e:
            logger.error("AI task execution failed", task_id=task.task_id, error=str(e))
            await self._update_task_status(task.task_id, "failed")
    
    async def _simulate_task_execution(self, task: AITask) -> Dict[str, Any]:
        """
        Симуляция выполнения AI задачи
        """
        # Имитация времени выполнения
        await asyncio.sleep(2)
        
        return {
            "status": "completed",
            "result": f"Задача '{task.description}' выполнена успешно",
            "details": {
                "task_type": task.task_type,
                "execution_time": "2 секунды",
                "recommendations": [
                    "Настройка завершена",
                    "Система готова к использованию",
                    "Рекомендуется тестирование"
                ]
            },
            "next_steps": "Протестировать настройки и при необходимости внести корректировки"
        }
    
    async def _update_task_status(self, task_id: str, status: str) -> None:
        """
        Обновление статуса задачи
        """
        try:
            with Session(self.engine) as session:
                # Поиск и обновление задачи
                contexts = session.exec(
                    select(ConversationContext).where(
                        ConversationContext.context_data.contains(f'"task_id": "{task_id}"')
                    )
                ).all()
                
                for context in contexts:
                    context.context_data["status"] = status
                    context.context_data["updated_at"] = datetime.now().isoformat()
                
                session.commit()
                
        except Exception as e:
            logger.error("Failed to update task status", error=str(e))
    
    async def _save_task_result(self, task_id: str, result: Dict[str, Any]) -> None:
        """
        Сохранение результата выполнения задачи
        """
        try:
            with Session(self.engine) as session:
                contexts = session.exec(
                    select(ConversationContext).where(
                        ConversationContext.context_data.contains(f'"task_id": "{task_id}"')
                    )
                ).all()
                
                for context in contexts:
                    context.context_data["status"] = "completed"
                    context.context_data["result"] = result
                    context.context_data["completed_at"] = datetime.now().isoformat()
                
                session.commit()
                
        except Exception as e:
            logger.error("Failed to save task result", error=str(e))
    
    async def _notify_team(self, request: ClientRequest, analysis: Dict[str, Any]) -> None:
        """
        Уведомление команды о новом запросе клиента
        """
        try:
            priority_emoji = {"urgent": "🔴", "normal": "🟡", "low": "🟢"}
            category_emoji = {
                "support": "🛠️",
                "automation": "⚙️", 
                "integration": "🔗",
                "custom": "🎯"
            }
            
            message = f"""
🆕 **НОВЫЙ ЗАПРОС КЛИЕНТА**

📞 **Телефон:** `{request.phone_number}`
👤 **Имя:** {request.client_name or 'Не указано'}
⏰ **Время:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

{priority_emoji.get(request.priority, '🟡')} **Приоритет:** {request.priority.upper()}
{category_emoji.get(request.category, '🎯')} **Категория:** {request.category}

💡 **Потребности клиента:**
{chr(10).join([f"• {need}" for need in request.client_needs])}

🎯 **Запрошенные действия:**
{chr(10).join([f"• {action}" for action in request.requested_actions])}

🔧 **Рекомендуемые инструменты:**
{chr(10).join([f"• {tool}" for tool in analysis.get('recommended_tools', [])])}

📋 **Краткое содержание звонка:**
{request.call_summary[:300]}...

📝 **Следующие шаги:**
{analysis.get('next_steps', 'Связаться с клиентом')}

🤖 **AI задачи созданы и выполняются автоматически**
"""
            
            await self._send_telegram_message(self.notification_chat_id, message)
            logger.info("Team notified", phone_number=request.phone_number)
            
        except Exception as e:
            logger.error("Failed to notify team", error=str(e))
    
    async def _send_client_response(self, chat_id: str, request: ClientRequest) -> None:
        """
        Отправка ответа клиенту
        """
        try:
            message = f"""
Здравствуйте! 👋

Спасибо за ваш звонок! Мы внимательно изучили ваш запрос и уже приступили к работе.

📋 **Ваши потребности:**
{chr(10).join([f"• {need}" for need in request.client_needs])}

🎯 **Что мы делаем для вас:**
{chr(10).join([f"• {action}" for action in request.requested_actions])}

⚡ **Приоритет:** {request.priority}
📂 **Категория:** {request.category}

🤖 **Наши AI системы уже работают над вашими задачами!**

⏰ **Ожидаемые сроки:**
• Срочные задачи: в течение 2-4 часов
• Обычные задачи: 1-2 рабочих дня
• Сложные интеграции: 3-5 рабочих дней

📞 **Остались вопросы?**
Пишите сюда или звоните - мы всегда готовы помочь!

С уважением,
Команда AI Call Center 🤖
"""
            
            await self._send_telegram_message(chat_id, message)
            logger.info("Client response sent", phone_number=request.phone_number)
            
        except Exception as e:
            logger.error("Failed to send client response", error=str(e))
    
    async def _notify_task_completion(self, task: AITask, result: Dict[str, Any]) -> None:
        """
        Уведомление о завершении задачи
        """
        try:
            message = f"""
✅ **ЗАДАЧА ВЫПОЛНЕНА**

📞 **Клиент:** {task.client_phone}
🆔 **Задача:** {task.task_id}
📝 **Описание:** {task.description}

✨ **Результат:**
{result.get('result', 'Задача выполнена успешно')}

📋 **Детали:**
{chr(10).join([f"• {detail}" for detail in result.get('details', {}).get('recommendations', [])])}

🎯 **Следующие шаги:**
{result.get('next_steps', 'Задача завершена')}

⏰ **Время выполнения:** {result.get('details', {}).get('execution_time', 'Неизвестно')}
"""
            
            await self._send_telegram_message(self.notification_chat_id, message)
            
            # Также отправляем клиенту, если есть его Telegram
            client_telegram = await self._find_client_telegram(task.client_phone)
            if client_telegram:
                client_message = f"""
✅ **Ваша задача выполнена!**

📝 **Задача:** {task.description}

✨ **Результат:**
{result.get('result', 'Задача выполнена успешно')}

🎯 **Что дальше:**
{result.get('next_steps', 'Можете начинать использовать настроенную систему')}

Если у вас есть вопросы или нужна дополнительная помощь - пишите!

С уважением,
Команда AI Call Center 🤖
"""
                await self._send_telegram_message(client_telegram, client_message)
            
        except Exception as e:
            logger.error("Failed to notify task completion", error=str(e))
    
    async def _find_client_telegram(self, phone_number: str) -> Optional[str]:
        """
        Поиск Telegram чата клиента по номеру телефона
        """
        try:
            with Session(self.engine) as session:
                user = session.exec(
                    select(User).where(User.phone_number == phone_number)
                ).first()
                
                if user and hasattr(user, 'telegram_chat_id'):
                    return user.telegram_chat_id
                
                return None
                
        except Exception as e:
            logger.error("Failed to find client telegram", error=str(e))
            return None
    
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
    
    async def get_client_requests_stats(self) -> Dict[str, Any]:
        """
        Получение статистики запросов клиентов
        """
        try:
            with Session(self.engine) as session:
                today = datetime.now().date()
                week_ago = today - timedelta(days=7)
                month_ago = today - timedelta(days=30)
                
                # Получение всех запросов
                all_requests = session.exec(
                    select(ConversationContext).where(
                        ConversationContext.context_data.contains('"type": "client_request"')
                    )
                ).all()
                
                # Статистика по категориям
                category_stats = {}
                priority_stats = {"urgent": 0, "normal": 0, "low": 0}
                
                for request in all_requests:
                    data = request.context_data
                    category = data.get("category", "custom")
                    priority = data.get("priority", "normal")
                    
                    category_stats[category] = category_stats.get(category, 0) + 1
                    priority_stats[priority] += 1
                
                # Получение задач
                all_tasks = session.exec(
                    select(ConversationContext).where(
                        ConversationContext.context_data.contains('"type": "ai_task"')
                    )
                ).all()
                
                task_stats = {"pending": 0, "processing": 0, "completed": 0, "failed": 0}
                for task in all_tasks:
                    status = task.context_data.get("status", "pending")
                    task_stats[status] += 1
                
                return {
                    "total_requests": len(all_requests),
                    "requests_today": len([r for r in all_requests if r.created_at.date() == today]),
                    "requests_this_week": len([r for r in all_requests if r.created_at.date() >= week_ago]),
                    "requests_this_month": len([r for r in all_requests if r.created_at.date() >= month_ago]),
                    "category_distribution": category_stats,
                    "priority_distribution": priority_stats,
                    "total_tasks": len(all_tasks),
                    "task_status_distribution": task_stats,
                    "available_tools": len(self.available_tools),
                    "last_updated": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error("Failed to get client requests stats", error=str(e))
            return {"error": str(e)}


# Функция для создания экземпляра бота
def create_universal_bot(bot_token: str, notification_chat_id: str) -> TelegramUniversalBot:
    """
    Создание экземпляра универсального Telegram бота
    """
    return TelegramUniversalBot(bot_token, notification_chat_id)


# Пример использования
async def example_usage():
    """
    Пример использования универсального Telegram бота
    """
    bot = create_universal_bot(
        bot_token="YOUR_BOT_TOKEN",
        notification_chat_id="YOUR_NOTIFICATION_CHAT_ID"
    )
    
    # Обработка звонка клиента
    call_data = {
        "phone_number": "+1234567890",
        "summary": "Клиент хочет автоматизировать email рассылки и настроить CRM систему для отслеживания клиентов",
        "duration": 240,
        "timestamp": datetime.now(),
        "client_name": "Анна Смирнова"
    }
    
    result = await bot.process_client_call(call_data)
    print("Результат обработки:", result)
    
    # Получение статистики
    stats = await bot.get_client_requests_stats()
    print("Статистика:", stats)


if __name__ == "__main__":
    asyncio.run(example_usage())
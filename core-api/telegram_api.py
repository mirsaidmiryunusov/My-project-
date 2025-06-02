"""
Telegram API для интеграции с Sales Bot
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog
from auth import get_current_user
from models import User
from telegram_universal_bot import TelegramUniversalBot, create_universal_bot, ClientRequest
from telegram_sales_bot import TelegramSalesBot, create_sales_bot, TelegramMessage

logger = structlog.get_logger(__name__)

telegram_router = APIRouter(prefix="/telegram", tags=["telegram"])

# Глобальные экземпляры ботов (будут инициализированы при настройке)
sales_bot: Optional[TelegramSalesBot] = None
universal_bot: Optional[TelegramUniversalBot] = None


class TelegramBotConfig(BaseModel):
    """Конфигурация Telegram бота"""
    bot_token: str
    notification_chat_id: str
    bot_type: str = "universal"  # "universal" или "sales"
    enabled: bool = True


class CallProcessRequest(BaseModel):
    """Запрос на обработку звонка для продаж"""
    phone_number: str
    summary: str
    duration: int
    client_name: Optional[str] = None
    modem_id: Optional[str] = None


class TelegramWebhookMessage(BaseModel):
    """Webhook сообщение от Telegram"""
    update_id: int
    message: Dict[str, Any]


class SalesStatsResponse(BaseModel):
    """Ответ со статистикой продаж"""
    success: bool
    stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@telegram_router.post("/configure-bot")
async def configure_telegram_bot(
    config: TelegramBotConfig,
    current_user: User = Depends(get_current_user)
):
    """
    Настройка Telegram бота (универсального или для продаж)
    Только для администраторов
    """
    try:
        # Проверка прав администратора
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        global sales_bot, universal_bot
        
        if config.enabled:
            if config.bot_type == "universal":
                # Создание универсального бота
                universal_bot = create_universal_bot(config.bot_token, config.notification_chat_id)
                
                # Тестирование подключения
                test_message = "🤖 Универсальный AI Telegram Bot активирован!\n\nТеперь я могу выполнять любые задачи клиентов на основе их звонков."
                success = await universal_bot._send_telegram_message(config.notification_chat_id, test_message)
                
                if not success:
                    raise HTTPException(status_code=400, detail="Failed to connect to Telegram")
                
                logger.info("Telegram universal bot configured", admin_id=current_user.id)
                
                return {
                    "success": True,
                    "message": "Универсальный Telegram Bot успешно настроен",
                    "bot_type": "universal",
                    "bot_active": True
                }
            else:
                # Создание бота для продаж
                sales_bot = create_sales_bot(config.bot_token, config.notification_chat_id)
                
                # Тестирование подключения
                test_message = "🤖 Telegram Sales Bot активирован!"
                success = await sales_bot._send_telegram_message(config.notification_chat_id, test_message)
                
                if not success:
                    raise HTTPException(status_code=400, detail="Failed to connect to Telegram")
                
                logger.info("Telegram sales bot configured", admin_id=current_user.id)
                
                return {
                    "success": True,
                    "message": "Telegram Sales Bot успешно настроен",
                    "bot_type": "sales",
                    "bot_active": True
                }
        else:
            # Отключение ботов
            if config.bot_type == "universal":
                universal_bot = None
                message = "Универсальный Telegram Bot отключен"
            else:
                sales_bot = None
                message = "Telegram Sales Bot отключен"
            
            return {
                "success": True,
                "message": message,
                "bot_active": False
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to configure telegram bot", error=str(e))
        raise HTTPException(status_code=500, detail="Configuration failed")


@telegram_router.post("/process-call")
async def process_call_with_ai(
    request: CallProcessRequest,
    background_tasks: BackgroundTasks,
    bot_type: str = "universal",
    current_user: User = Depends(get_current_user)
):
    """
    Обработка звонка с помощью AI бота (универсального или для продаж)
    """
    try:
        # Подготовка данных звонка
        call_data = {
            "phone_number": request.phone_number,
            "summary": request.summary,
            "duration": request.duration,
            "timestamp": datetime.now(),
            "client_name": request.client_name,
            "modem_id": request.modem_id
        }
        
        if bot_type == "universal":
            if not universal_bot:
                raise HTTPException(status_code=400, detail="Universal Telegram Bot not configured")
            
            # Обработка универсальным ботом
            background_tasks.add_task(
                universal_bot.process_client_call,
                call_data
            )
            
            message = "Звонок отправлен на обработку универсальным AI ботом"
        else:
            if not sales_bot:
                raise HTTPException(status_code=400, detail="Sales Telegram Bot not configured")
            
            # Обработка ботом для продаж
            background_tasks.add_task(
                sales_bot.process_call_for_sales,
                call_data
            )
            
            message = "Звонок отправлен на обработку ботом для продаж"
        
        logger.info("Call processing started", 
                   phone_number=request.phone_number, 
                   bot_type=bot_type)
        
        return {
            "success": True,
            "message": message,
            "phone_number": request.phone_number,
            "bot_type": bot_type,
            "processing": "background"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to process call", error=str(e))
        raise HTTPException(status_code=500, detail="Call processing failed")


@telegram_router.post("/webhook")
async def telegram_webhook(webhook_data: TelegramWebhookMessage):
    """
    Webhook для получения сообщений от Telegram
    """
    try:
        if not sales_bot:
            return {"ok": True, "message": "Bot not configured"}
        
        message_data = webhook_data.message
        
        # Создание объекта сообщения
        telegram_message = TelegramMessage(
            chat_id=str(message_data["chat"]["id"]),
            message_id=message_data["message_id"],
            text=message_data.get("text", ""),
            from_user=message_data["from"],
            timestamp=datetime.fromtimestamp(message_data["date"])
        )
        
        # Обработка сообщения
        await sales_bot.handle_incoming_message(telegram_message)
        
        return {"ok": True}
        
    except Exception as e:
        logger.error("Webhook processing failed", error=str(e))
        return {"ok": False, "error": str(e)}


@telegram_router.get("/stats", response_model=SalesStatsResponse)
async def get_bot_statistics(
    bot_type: str = "universal",
    current_user: User = Depends(get_current_user)
):
    """
    Получение статистики бота (универсального или для продаж)
    """
    try:
        if bot_type == "universal":
            if not universal_bot:
                return SalesStatsResponse(
                    success=False,
                    error="Universal Telegram Bot not configured"
                )
            
            stats = await universal_bot.get_client_requests_stats()
        else:
            if not sales_bot:
                return SalesStatsResponse(
                    success=False,
                    error="Sales Telegram Bot not configured"
                )
            
            stats = await sales_bot.get_sales_statistics()
        
        return SalesStatsResponse(
            success=True,
            stats=stats
        )
        
    except Exception as e:
        logger.error("Failed to get bot statistics", error=str(e))
        return SalesStatsResponse(
            success=False,
            error="Failed to get statistics"
        )


@telegram_router.get("/bot-status")
async def get_bot_status(current_user: User = Depends(get_current_user)):
    """
    Получение статуса Telegram ботов
    """
    try:
        return {
            "universal_bot": {
                "configured": universal_bot is not None,
                "active": universal_bot is not None,
                "type": "universal"
            },
            "sales_bot": {
                "configured": sales_bot is not None,
                "active": sales_bot is not None,
                "type": "sales"
            },
            "last_check": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get bot status", error=str(e))
        raise HTTPException(status_code=500, detail="Status check failed")


@telegram_router.post("/send-message")
async def send_telegram_message(
    chat_id: str,
    message: str,
    bot_type: str = "universal",
    current_user: User = Depends(get_current_user)
):
    """
    Отправка сообщения через Telegram бота
    Только для администраторов
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        if bot_type == "universal":
            if not universal_bot:
                raise HTTPException(status_code=400, detail="Universal Telegram Bot not configured")
            success = await universal_bot._send_telegram_message(chat_id, message)
        else:
            if not sales_bot:
                raise HTTPException(status_code=400, detail="Sales Telegram Bot not configured")
            success = await sales_bot._send_telegram_message(chat_id, message)
        
        if success:
            return {
                "success": True,
                "message": "Сообщение отправлено",
                "chat_id": chat_id,
                "bot_type": bot_type
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to send message")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to send telegram message", error=str(e))
        raise HTTPException(status_code=500, detail="Message sending failed")


class LeadUpdateRequest(BaseModel):
    """Запрос на обновление лида"""
    phone_number: str
    status: str  # contacted, qualified, proposal, closed_won, closed_lost
    notes: Optional[str] = None


@telegram_router.post("/update-lead")
async def update_lead_status(
    request: LeadUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Обновление статуса лида
    """
    try:
        # Здесь можно добавить логику обновления статуса лида в CRM
        logger.info("Lead status updated", 
                   phone_number=request.phone_number, 
                   status=request.status,
                   user_id=current_user.id)
        
        return {
            "success": True,
            "message": "Статус лида обновлен",
            "phone_number": request.phone_number,
            "new_status": request.status
        }
        
    except Exception as e:
        logger.error("Failed to update lead status", error=str(e))
        raise HTTPException(status_code=500, detail="Lead update failed")


@telegram_router.get("/leads")
async def get_leads(
    limit: int = 50,
    offset: int = 0,
    urgency: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Получение списка лидов
    """
    try:
        # Здесь можно добавить логику получения лидов из базы данных
        # с фильтрацией по срочности и пагинацией
        
        return {
            "success": True,
            "leads": [],  # Заглушка - здесь будут реальные лиды
            "total": 0,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error("Failed to get leads", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get leads")


# Функция для интеграции с основным приложением
def get_telegram_router():
    """Получение роутера для интеграции с main.py"""
    return telegram_router
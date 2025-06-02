"""
Agentic Function Manager
Универсальный менеджер для управления всеми агентскими функциями
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum

import structlog
from sqlmodel import Session, select, Field, SQLModel, create_engine
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import httpx

from config import CoreAPIConfig
from database import get_db_manager
from agentic_function_service import AgenticFunction, FunctionResult
from universal_agentic_functions import UniversalAgenticFunctionService
from advanced_agentic_functions import *
from specialized_agentic_functions import *

logger = structlog.get_logger(__name__)


class FunctionStatus(str, Enum):
    """Статус функции."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    RUNNING = "running"


class ConnectionType(str, Enum):
    """Тип подключения функций."""
    SEQUENTIAL = "sequential"  # Последовательное выполнение
    PARALLEL = "parallel"     # Параллельное выполнение
    CONDITIONAL = "conditional"  # Условное выполнение
    TRIGGER = "trigger"       # Триггерное выполнение


@dataclass
class FunctionConnection:
    """Связь между функциями."""
    id: str
    source_function: str
    target_function: str
    connection_type: ConnectionType
    conditions: Dict[str, Any]
    mapping: Dict[str, str]  # Маппинг параметров между функциями
    enabled: bool = True
    created_at: datetime = None


@dataclass
class ClientConnection:
    """Подключение к клиентскому телефону."""
    id: str
    phone_number: str
    client_name: str
    connected_functions: List[str]
    gemini_integration: bool
    auto_trigger: bool
    trigger_keywords: List[str]
    status: FunctionStatus
    created_at: datetime = None


class AgenticFunctionManager:
    """
    Менеджер агентских функций
    Управляет всеми функциями, их связями и подключениями к клиентам
    """
    
    def __init__(self, config: CoreAPIConfig):
        self.config = config
        self.db_manager = get_db_manager()
        self.logger = structlog.get_logger(__name__)
        
        # Инициализация всех сервисов функций
        self.universal_service = UniversalAgenticFunctionService(config)
        self.advanced_functions = self._init_advanced_functions()
        self.specialized_functions = self._init_specialized_functions()
        
        # Все доступные функции
        self.all_functions = {}
        self._register_all_functions()
        
        # Активные подключения и связи
        self.function_connections: Dict[str, FunctionConnection] = {}
        self.client_connections: Dict[str, ClientConnection] = {}
        self.active_workflows: Dict[str, Dict] = {}
        
        # Статистика выполнения
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'avg_execution_time': 0.0
        }
    
    def _init_advanced_functions(self) -> Dict[str, AgenticFunction]:
        """Инициализация продвинутых функций."""
        functions = {}
        
        # Финансовые функции
        functions['cryptocurrency_tracker'] = CryptocurrencyTrackerFunction(self.config)
        functions['stock_market_analyzer'] = StockMarketAnalyzerFunction(self.config)
        functions['forex_tracker'] = ForexTrackerFunction(self.config)
        
        # Путешествия
        functions['flight_booking'] = FlightBookingFunction(self.config)
        functions['hotel_booking'] = HotelBookingFunction(self.config)
        functions['ride_booking'] = RideBookingFunction(self.config)
        
        # Здоровье и фитнес
        functions['fitness_tracker'] = FitnessTrackerFunction(self.config)
        functions['nutrition_tracker'] = NutritionTrackerFunction(self.config)
        
        # Образование
        functions['language_learning'] = LanguageLearningFunction(self.config)
        functions['skill_assessment'] = SkillAssessmentFunction(self.config)
        
        return functions
    
    def _init_specialized_functions(self) -> Dict[str, AgenticFunction]:
        """Инициализация специализированных функций."""
        functions = {}
        
        # Недвижимость
        functions['property_search'] = PropertySearchFunction(self.config)
        functions['property_valuation'] = PropertyValuationFunction(self.config)
        
        # Юридические
        functions['contract_analyzer'] = ContractAnalyzerFunction(self.config)
        functions['compliance_checker'] = ComplianceCheckerFunction(self.config)
        
        # Развлечения
        functions['game_recommendation'] = GameRecommendationFunction(self.config)
        functions['movie_recommendation'] = MovieRecommendationFunction(self.config)
        
        # Безопасность
        functions['security_scanner'] = SecurityScannerFunction(self.config)
        functions['password_generator'] = PasswordGeneratorFunction(self.config)
        
        return functions
    
    def _register_all_functions(self):
        """Регистрация всех доступных функций."""
        # Универсальные функции
        self.all_functions.update(self.universal_service.functions)
        
        # Продвинутые функции
        self.all_functions.update(self.advanced_functions)
        
        # Специализированные функции
        self.all_functions.update(self.specialized_functions)
        
        self.logger.info("All functions registered", total_count=len(self.all_functions))
    
    async def execute_function(self, function_name: str, context: Dict[str, Any], 
                             session: Session, client_phone: str = None) -> FunctionResult:
        """Выполнение функции с возможностью подключения к клиенту."""
        
        start_time = datetime.utcnow()
        
        try:
            if function_name not in self.all_functions:
                return FunctionResult(
                    success=False,
                    error=f"Function '{function_name}' not found"
                )
            
            function = self.all_functions[function_name]
            
            # Добавляем информацию о клиенте в контекст
            if client_phone:
                context['client_phone'] = client_phone
                context['client_connection'] = self.client_connections.get(client_phone)
            
            # Выполняем функцию
            result = await function.execute(context, session)
            
            # Обновляем статистику
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_execution_stats(result.success, execution_time)
            
            # Если функция выполнена успешно и есть связанные функции
            if result.success and function_name in self._get_source_functions():
                await self._trigger_connected_functions(function_name, result, context, session)
            
            # Отправляем результат клиенту через Gemini если подключен
            if client_phone and client_phone in self.client_connections:
                await self._send_result_to_client(client_phone, function_name, result)
            
            return result
            
        except Exception as e:
            self.logger.error("Function execution failed", 
                            function_name=function_name, 
                            error=str(e))
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_execution_stats(False, execution_time)
            
            return FunctionResult(
                success=False,
                error=f"Execution failed: {str(e)}"
            )
    
    async def create_function_connection(self, source_function: str, target_function: str,
                                       connection_type: ConnectionType, 
                                       conditions: Dict[str, Any] = None,
                                       mapping: Dict[str, str] = None) -> str:
        """Создание связи между функциями."""
        
        if source_function not in self.all_functions:
            raise ValueError(f"Source function '{source_function}' not found")
        
        if target_function not in self.all_functions:
            raise ValueError(f"Target function '{target_function}' not found")
        
        connection_id = f"conn_{uuid.uuid4().hex[:8]}"
        
        connection = FunctionConnection(
            id=connection_id,
            source_function=source_function,
            target_function=target_function,
            connection_type=connection_type,
            conditions=conditions or {},
            mapping=mapping or {},
            created_at=datetime.utcnow()
        )
        
        self.function_connections[connection_id] = connection
        
        self.logger.info("Function connection created",
                        connection_id=connection_id,
                        source=source_function,
                        target=target_function,
                        type=connection_type)
        
        return connection_id
    
    async def connect_client_phone(self, phone_number: str, client_name: str,
                                 functions: List[str], enable_gemini: bool = True,
                                 auto_trigger: bool = True,
                                 trigger_keywords: List[str] = None) -> str:
        """Подключение клиентского телефона к функциям."""
        
        # Проверяем существование функций
        for func_name in functions:
            if func_name not in self.all_functions:
                raise ValueError(f"Function '{func_name}' not found")
        
        connection_id = f"client_{uuid.uuid4().hex[:8]}"
        
        client_connection = ClientConnection(
            id=connection_id,
            phone_number=phone_number,
            client_name=client_name,
            connected_functions=functions,
            gemini_integration=enable_gemini,
            auto_trigger=auto_trigger,
            trigger_keywords=trigger_keywords or [],
            status=FunctionStatus.ACTIVE,
            created_at=datetime.utcnow()
        )
        
        self.client_connections[phone_number] = client_connection
        
        # Если включена интеграция с Gemini, настраиваем webhook
        if enable_gemini:
            await self._setup_gemini_webhook(phone_number, functions)
        
        self.logger.info("Client phone connected",
                        phone=phone_number,
                        client=client_name,
                        functions=functions,
                        gemini_enabled=enable_gemini)
        
        return connection_id
    
    async def process_client_call(self, phone_number: str, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обработка звонка от клиента."""
        
        if phone_number not in self.client_connections:
            return {
                'success': False,
                'error': 'Client phone not connected'
            }
        
        client_connection = self.client_connections[phone_number]
        
        if client_connection.status != FunctionStatus.ACTIVE:
            return {
                'success': False,
                'error': 'Client connection is not active'
            }
        
        # Анализируем содержание звонка для определения нужных функций
        call_summary = call_data.get('summary', '')
        triggered_functions = await self._analyze_call_for_functions(
            call_summary, 
            client_connection.connected_functions,
            client_connection.trigger_keywords
        )
        
        results = []
        
        # Выполняем триггерные функции
        with Session(self.db_manager.engine) as session:
            for func_name in triggered_functions:
                context = {
                    'call_data': call_data,
                    'client_phone': phone_number,
                    'client_name': client_connection.client_name,
                    'auto_triggered': True
                }
                
                result = await self.execute_function(func_name, context, session, phone_number)
                results.append({
                    'function': func_name,
                    'result': result.to_dict()
                })
        
        # Отправляем сводку клиенту через Gemini
        if client_connection.gemini_integration:
            await self._send_call_summary_to_client(phone_number, call_data, results)
        
        return {
            'success': True,
            'triggered_functions': triggered_functions,
            'results': results,
            'client_notified': client_connection.gemini_integration
        }
    
    async def _trigger_connected_functions(self, source_function: str, source_result: FunctionResult,
                                         context: Dict[str, Any], session: Session):
        """Запуск связанных функций."""
        
        connections = [
            conn for conn in self.function_connections.values()
            if conn.source_function == source_function and conn.enabled
        ]
        
        for connection in connections:
            try:
                # Проверяем условия выполнения
                if not self._check_connection_conditions(connection, source_result):
                    continue
                
                # Подготавливаем контекст для целевой функции
                target_context = self._map_function_parameters(
                    connection, source_result.data, context
                )
                
                if connection.connection_type == ConnectionType.SEQUENTIAL:
                    # Последовательное выполнение
                    await self.execute_function(
                        connection.target_function, 
                        target_context, 
                        session,
                        context.get('client_phone')
                    )
                
                elif connection.connection_type == ConnectionType.PARALLEL:
                    # Параллельное выполнение
                    asyncio.create_task(
                        self.execute_function(
                            connection.target_function, 
                            target_context, 
                            session,
                            context.get('client_phone')
                        )
                    )
                
                elif connection.connection_type == ConnectionType.TRIGGER:
                    # Триггерное выполнение с задержкой
                    await asyncio.sleep(1)  # Небольшая задержка
                    await self.execute_function(
                        connection.target_function, 
                        target_context, 
                        session,
                        context.get('client_phone')
                    )
                
            except Exception as e:
                self.logger.error("Connected function execution failed",
                                connection_id=connection.id,
                                target_function=connection.target_function,
                                error=str(e))
    
    async def _analyze_call_for_functions(self, call_summary: str, available_functions: List[str],
                                        trigger_keywords: List[str]) -> List[str]:
        """Анализ звонка для определения нужных функций."""
        
        triggered_functions = []
        call_lower = call_summary.lower()
        
        # Проверяем ключевые слова
        for keyword in trigger_keywords:
            if keyword.lower() in call_lower:
                # Находим подходящие функции для этого ключевого слова
                matching_functions = self._get_functions_for_keyword(keyword, available_functions)
                triggered_functions.extend(matching_functions)
        
        # Автоматический анализ содержания
        function_keywords = {
            'email_sender': ['email', 'письмо', 'отправить', 'рассылка'],
            'sms_bulk_sender': ['sms', 'смс', 'сообщение', 'уведомление'],
            'social_media_poster': ['соцсети', 'facebook', 'instagram', 'пост'],
            'cryptocurrency_tracker': ['криптовалюта', 'биткоин', 'ethereum', 'курс'],
            'flight_booking': ['билет', 'самолет', 'перелет', 'авиа'],
            'hotel_booking': ['отель', 'гостиница', 'бронирование', 'номер'],
            'property_search': ['недвижимость', 'квартира', 'дом', 'купить'],
            'fitness_tracker': ['фитнес', 'тренировка', 'спорт', 'здоровье'],
            'language_learning': ['язык', 'изучение', 'перевод', 'английский'],
            'security_scanner': ['безопасность', 'сканирование', 'уязвимость'],
            'data_analyzer': ['данные', 'анализ', 'статистика', 'отчет'],
            'web_scraper': ['парсинг', 'сайт', 'данные', 'извлечение'],
            'content_generator': ['контент', 'статья', 'текст', 'генерация'],
            'payment_processor': ['платеж', 'оплата', 'деньги', 'транзакция']
        }
        
        for func_name, keywords in function_keywords.items():
            if func_name in available_functions:
                if any(keyword in call_lower for keyword in keywords):
                    if func_name not in triggered_functions:
                        triggered_functions.append(func_name)
        
        return triggered_functions
    
    def _get_functions_for_keyword(self, keyword: str, available_functions: List[str]) -> List[str]:
        """Получение функций для ключевого слова."""
        
        keyword_mapping = {
            'автоматизация': ['email_sender', 'sms_bulk_sender', 'social_media_poster'],
            'финансы': ['cryptocurrency_tracker', 'stock_market_analyzer', 'payment_processor'],
            'путешествия': ['flight_booking', 'hotel_booking', 'ride_booking'],
            'здоровье': ['fitness_tracker', 'nutrition_tracker'],
            'безопасность': ['security_scanner', 'password_generator'],
            'недвижимость': ['property_search', 'property_valuation'],
            'образование': ['language_learning', 'skill_assessment'],
            'развлечения': ['game_recommendation', 'movie_recommendation']
        }
        
        functions = keyword_mapping.get(keyword.lower(), [])
        return [f for f in functions if f in available_functions]
    
    async def _setup_gemini_webhook(self, phone_number: str, functions: List[str]):
        """Настройка webhook для Gemini интеграции."""
        
        try:
            async with httpx.AsyncClient() as client:
                webhook_data = {
                    'phone_number': phone_number,
                    'connected_functions': functions,
                    'webhook_url': f"{self.config.core_api_url}/webhook/gemini/{phone_number}",
                    'enabled': True
                }
                
                # Отправляем настройки в Gemini сервис
                response = await client.post(
                    f"{self.config.voice_bridge_url}/setup_client_webhook",
                    json=webhook_data
                )
                
                if response.status_code == 200:
                    self.logger.info("Gemini webhook setup successful", phone=phone_number)
                else:
                    self.logger.error("Gemini webhook setup failed", 
                                    phone=phone_number, 
                                    status=response.status_code)
                    
        except Exception as e:
            self.logger.error("Gemini webhook setup error", phone=phone_number, error=str(e))
    
    async def _send_result_to_client(self, phone_number: str, function_name: str, result: FunctionResult):
        """Отправка результата клиенту через Gemini."""
        
        try:
            client_connection = self.client_connections[phone_number]
            
            if not client_connection.gemini_integration:
                return
            
            # Формируем сообщение для клиента
            if result.success:
                message = f"✅ Функция '{function_name}' выполнена успешно!\n\n"
                
                # Добавляем краткое описание результата
                if result.data:
                    if function_name == 'email_sender':
                        message += f"📧 Email отправлен: {result.data.get('recipients', [])}"
                    elif function_name == 'cryptocurrency_tracker':
                        prices = result.data.get('prices', [])
                        if prices:
                            message += "💰 Курсы криптовалют:\n"
                            for price in prices[:3]:
                                message += f"{price['symbol']}: ${price['price']}\n"
                    elif function_name == 'flight_booking':
                        flights = result.data.get('flights', [])
                        if flights:
                            message += f"✈️ Найдено рейсов: {len(flights)}\n"
                            message += f"Лучший вариант: {flights[0]['price']}"
                    else:
                        message += f"Результат: {str(result.data)[:200]}..."
            else:
                message = f"❌ Ошибка выполнения функции '{function_name}':\n{result.error}"
            
            # Отправляем через Gemini
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config.voice_bridge_url}/send_client_message",
                    json={
                        'phone_number': phone_number,
                        'message': message,
                        'function_result': result.to_dict()
                    }
                )
                
                if response.status_code == 200:
                    self.logger.info("Result sent to client", 
                                   phone=phone_number, 
                                   function=function_name)
                    
        except Exception as e:
            self.logger.error("Failed to send result to client", 
                            phone=phone_number, 
                            function=function_name, 
                            error=str(e))
    
    async def _send_call_summary_to_client(self, phone_number: str, call_data: Dict[str, Any], 
                                         results: List[Dict]):
        """Отправка сводки по звонку клиенту."""
        
        try:
            summary = f"📞 Обработка вашего звонка завершена!\n\n"
            summary += f"🕐 Время: {datetime.utcnow().strftime('%H:%M %d.%m.%Y')}\n"
            summary += f"⚡ Выполнено функций: {len(results)}\n\n"
            
            for result in results:
                func_name = result['function']
                success = result['result']['success']
                status = "✅" if success else "❌"
                summary += f"{status} {func_name}\n"
            
            summary += f"\n📱 Все результаты сохранены в вашем личном кабинете."
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.config.voice_bridge_url}/send_client_message",
                    json={
                        'phone_number': phone_number,
                        'message': summary,
                        'call_summary': call_data,
                        'function_results': results
                    }
                )
                
        except Exception as e:
            self.logger.error("Failed to send call summary", 
                            phone=phone_number, 
                            error=str(e))
    
    def _check_connection_conditions(self, connection: FunctionConnection, 
                                   source_result: FunctionResult) -> bool:
        """Проверка условий для выполнения связанной функции."""
        
        if not connection.conditions:
            return True
        
        # Проверяем условие успешности
        if 'require_success' in connection.conditions:
            if connection.conditions['require_success'] and not source_result.success:
                return False
        
        # Проверяем условия по данным
        if 'data_conditions' in connection.conditions:
            data_conditions = connection.conditions['data_conditions']
            
            for key, expected_value in data_conditions.items():
                if key not in source_result.data:
                    return False
                
                actual_value = source_result.data[key]
                
                if isinstance(expected_value, dict):
                    # Сложные условия (больше, меньше, содержит)
                    if 'gt' in expected_value and actual_value <= expected_value['gt']:
                        return False
                    if 'lt' in expected_value and actual_value >= expected_value['lt']:
                        return False
                    if 'contains' in expected_value and expected_value['contains'] not in str(actual_value):
                        return False
                else:
                    # Простое сравнение
                    if actual_value != expected_value:
                        return False
        
        return True
    
    def _map_function_parameters(self, connection: FunctionConnection, 
                               source_data: Dict[str, Any], 
                               original_context: Dict[str, Any]) -> Dict[str, Any]:
        """Маппинг параметров между функциями."""
        
        target_context = original_context.copy()
        
        # Применяем маппинг параметров
        for source_param, target_param in connection.mapping.items():
            if source_param in source_data:
                target_context[target_param] = source_data[source_param]
        
        # Добавляем все данные источника с префиксом
        target_context['source_function_data'] = source_data
        target_context['source_function_name'] = connection.source_function
        
        return target_context
    
    def _get_source_functions(self) -> Set[str]:
        """Получение списка функций, которые являются источниками в связях."""
        return {conn.source_function for conn in self.function_connections.values()}
    
    def _update_execution_stats(self, success: bool, execution_time: float):
        """Обновление статистики выполнения."""
        self.execution_stats['total_executions'] += 1
        
        if success:
            self.execution_stats['successful_executions'] += 1
        else:
            self.execution_stats['failed_executions'] += 1
        
        # Обновляем среднее время выполнения
        total = self.execution_stats['total_executions']
        current_avg = self.execution_stats['avg_execution_time']
        self.execution_stats['avg_execution_time'] = (
            (current_avg * (total - 1) + execution_time) / total
        )
    
    def get_all_functions_info(self) -> Dict[str, Any]:
        """Получение информации о всех доступных функциях."""
        
        functions_info = {}
        
        for name, function in self.all_functions.items():
            functions_info[name] = {
                'name': function.name,
                'description': function.description,
                'category': self._get_function_category(name),
                'status': 'active',
                'connections': {
                    'as_source': len([c for c in self.function_connections.values() 
                                    if c.source_function == name]),
                    'as_target': len([c for c in self.function_connections.values() 
                                    if c.target_function == name])
                }
            }
        
        return functions_info
    
    def _get_function_category(self, function_name: str) -> str:
        """Определение категории функции."""
        
        categories = {
            'communication': ['email_sender', 'sms_bulk_sender', 'telegram_bot_sender', 'whatsapp_sender', 'social_media_poster'],
            'finance': ['cryptocurrency_tracker', 'stock_market_analyzer', 'forex_tracker', 'payment_processor'],
            'travel': ['flight_booking', 'hotel_booking', 'ride_booking'],
            'health': ['fitness_tracker', 'nutrition_tracker'],
            'education': ['language_learning', 'skill_assessment'],
            'real_estate': ['property_search', 'property_valuation'],
            'legal': ['contract_analyzer', 'compliance_checker'],
            'entertainment': ['game_recommendation', 'movie_recommendation'],
            'security': ['security_scanner', 'password_generator'],
            'data': ['data_analyzer', 'web_scraper'],
            'content': ['content_generator', 'image_generator'],
            'automation': ['file_organizer', 'task_scheduler']
        }
        
        for category, functions in categories.items():
            if function_name in functions:
                return category
        
        return 'other'
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Получение данных для дашборда."""
        
        return {
            'total_functions': len(self.all_functions),
            'active_connections': len([c for c in self.function_connections.values() if c.enabled]),
            'connected_clients': len(self.client_connections),
            'execution_stats': self.execution_stats,
            'recent_executions': [],  # Можно добавить историю
            'function_categories': self._get_category_stats(),
            'top_used_functions': self._get_top_used_functions()
        }
    
    def _get_category_stats(self) -> Dict[str, int]:
        """Статистика по категориям функций."""
        
        category_counts = {}
        
        for function_name in self.all_functions.keys():
            category = self._get_function_category(function_name)
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return category_counts
    
    def _get_top_used_functions(self) -> List[Dict[str, Any]]:
        """Топ используемых функций."""
        
        # Здесь можно добавить реальную статистику использования
        # Пока возвращаем примерные данные
        return [
            {'name': 'email_sender', 'usage_count': 150},
            {'name': 'cryptocurrency_tracker', 'usage_count': 120},
            {'name': 'social_media_poster', 'usage_count': 95},
            {'name': 'data_analyzer', 'usage_count': 80},
            {'name': 'content_generator', 'usage_count': 75}
        ]
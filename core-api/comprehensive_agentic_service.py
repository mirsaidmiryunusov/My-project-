"""
Comprehensive Agentic Service Manager
Integrates all universal, advanced, and specialized agentic functions
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

import structlog
from sqlmodel import Session

from config import CoreAPIConfig
from agentic_function_service import AgenticFunctionService, FunctionResult
from universal_agentic_functions import (
    EmailSenderFunction, SMSBulkSenderFunction, TelegramBotSenderFunction,
    WhatsAppSenderFunction, SocialMediaPosterFunction, DataAnalyzerFunction,
    WebScraperFunction, FileOrganizerFunction
)
from advanced_agentic_functions import (
    CryptocurrencyTrackerFunction, StockMarketAnalyzerFunction, ForexTrackerFunction,
    FlightBookingFunction, HotelBookingFunction, RideBookingFunction,
    FitnessTrackerFunction, NutritionTrackerFunction, LanguageLearningFunction,
    SkillAssessmentFunction
)
from specialized_agentic_functions import (
    PropertySearchFunction, PropertyValuationFunction, ContractAnalyzerFunction,
    ComplianceCheckerFunction, GameRecommendationFunction, MovieRecommendationFunction,
    SecurityScannerFunction, PasswordGeneratorFunction
)

logger = structlog.get_logger(__name__)


class ComprehensiveAgenticService:
    """
    Comprehensive Agentic Service Manager
    
    Provides access to all available agentic functions organized by category
    with intelligent routing, execution monitoring, and result aggregation.
    """
    
    def __init__(self, config: CoreAPIConfig):
        self.config = config
        self.logger = structlog.get_logger(__name__)
        
        # Initialize function categories
        self.communication_functions = {}
        self.data_functions = {}
        self.file_functions = {}
        self.finance_functions = {}
        self.travel_functions = {}
        self.health_functions = {}
        self.education_functions = {}
        self.real_estate_functions = {}
        self.legal_functions = {}
        self.entertainment_functions = {}
        self.security_functions = {}
        
        # Execution tracking
        self.execution_history = []
        self.function_stats = {}
        
        # Initialize all functions
        self._initialize_all_functions()
    
    def _initialize_all_functions(self):
        """Initialize all agentic functions by category."""
        
        # Communication Functions
        self.communication_functions = {
            'email_sender': EmailSenderFunction(self.config),
            'sms_bulk_sender': SMSBulkSenderFunction(self.config),
            'telegram_bot_sender': TelegramBotSenderFunction(self.config),
            'whatsapp_sender': WhatsAppSenderFunction(self.config),
            'social_media_poster': SocialMediaPosterFunction(self.config)
        }
        
        # Data Processing Functions
        self.data_functions = {
            'data_analyzer': DataAnalyzerFunction(self.config),
            'web_scraper': WebScraperFunction(self.config)
        }
        
        # File Management Functions
        self.file_functions = {
            'file_organizer': FileOrganizerFunction(self.config)
        }
        
        # Finance Functions
        self.finance_functions = {
            'cryptocurrency_tracker': CryptocurrencyTrackerFunction(self.config),
            'stock_market_analyzer': StockMarketAnalyzerFunction(self.config),
            'forex_tracker': ForexTrackerFunction(self.config)
        }
        
        # Travel Functions
        self.travel_functions = {
            'flight_booking': FlightBookingFunction(self.config),
            'hotel_booking': HotelBookingFunction(self.config),
            'ride_booking': RideBookingFunction(self.config)
        }
        
        # Health & Fitness Functions
        self.health_functions = {
            'fitness_tracker': FitnessTrackerFunction(self.config),
            'nutrition_tracker': NutritionTrackerFunction(self.config)
        }
        
        # Education Functions
        self.education_functions = {
            'language_learning': LanguageLearningFunction(self.config),
            'skill_assessment': SkillAssessmentFunction(self.config)
        }
        
        # Real Estate Functions
        self.real_estate_functions = {
            'property_search': PropertySearchFunction(self.config),
            'property_valuation': PropertyValuationFunction(self.config)
        }
        
        # Legal Functions
        self.legal_functions = {
            'contract_analyzer': ContractAnalyzerFunction(self.config),
            'compliance_checker': ComplianceCheckerFunction(self.config)
        }
        
        # Entertainment Functions
        self.entertainment_functions = {
            'game_recommendation': GameRecommendationFunction(self.config),
            'movie_recommendation': MovieRecommendationFunction(self.config)
        }
        
        # Security Functions
        self.security_functions = {
            'security_scanner': SecurityScannerFunction(self.config),
            'password_generator': PasswordGeneratorFunction(self.config)
        }
        
        self.logger.info("Comprehensive agentic service initialized",
                        total_categories=11,
                        total_functions=self.get_total_function_count())
    
    def get_total_function_count(self) -> int:
        """Get total number of available functions."""
        return sum([
            len(self.communication_functions),
            len(self.data_functions),
            len(self.file_functions),
            len(self.finance_functions),
            len(self.travel_functions),
            len(self.health_functions),
            len(self.education_functions),
            len(self.real_estate_functions),
            len(self.legal_functions),
            len(self.entertainment_functions),
            len(self.security_functions)
        ])
    
    async def execute_function(self, function_name: str, context: Dict[str, Any], 
                             session: Session) -> FunctionResult:
        """Execute any agentic function by name."""
        
        # Find function in all categories
        function = self._find_function(function_name)
        
        if not function:
            return FunctionResult(
                success=False,
                error=f"Function '{function_name}' not found"
            )
        
        try:
            # Execute function
            start_time = datetime.utcnow()
            result = await function.execute(context, session)
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Track execution
            self._track_execution(function_name, context, result, execution_time)
            
            self.logger.info("Function executed",
                           function_name=function_name,
                           success=result.success,
                           execution_time=execution_time)
            
            return result
            
        except Exception as e:
            self.logger.error("Function execution failed",
                            function_name=function_name,
                            error=str(e))
            
            return FunctionResult(
                success=False,
                error=f"Execution failed: {str(e)}"
            )
    
    def _find_function(self, function_name: str):
        """Find function in all categories."""
        all_functions = {
            **self.communication_functions,
            **self.data_functions,
            **self.file_functions,
            **self.finance_functions,
            **self.travel_functions,
            **self.health_functions,
            **self.education_functions,
            **self.real_estate_functions,
            **self.legal_functions,
            **self.entertainment_functions,
            **self.security_functions
        }
        
        return all_functions.get(function_name)
    
    def _track_execution(self, function_name: str, context: Dict[str, Any], 
                        result: FunctionResult, execution_time: float):
        """Track function execution for analytics."""
        
        execution_record = {
            'function_name': function_name,
            'context': context,
            'result': result.to_dict(),
            'execution_time': execution_time,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.execution_history.append(execution_record)
        
        # Update function statistics
        if function_name not in self.function_stats:
            self.function_stats[function_name] = {
                'total_executions': 0,
                'successful_executions': 0,
                'total_execution_time': 0,
                'avg_execution_time': 0,
                'last_executed': None
            }
        
        stats = self.function_stats[function_name]
        stats['total_executions'] += 1
        stats['total_execution_time'] += execution_time
        stats['avg_execution_time'] = stats['total_execution_time'] / stats['total_executions']
        stats['last_executed'] = datetime.utcnow().isoformat()
        
        if result.success:
            stats['successful_executions'] += 1
    
    async def execute_workflow(self, workflow: List[Dict[str, Any]], 
                             session: Session) -> Dict[str, Any]:
        """Execute a workflow of multiple functions."""
        
        workflow_id = f"workflow_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        workflow_results = []
        workflow_context = {}
        
        self.logger.info("Starting workflow execution",
                        workflow_id=workflow_id,
                        steps=len(workflow))
        
        for step_index, step in enumerate(workflow):
            function_name = step.get('function')
            step_context = step.get('context', {})
            
            # Merge workflow context with step context
            merged_context = {**workflow_context, **step_context}
            
            # Execute function
            result = await self.execute_function(function_name, merged_context, session)
            
            step_result = {
                'step': step_index + 1,
                'function': function_name,
                'success': result.success,
                'result': result.to_dict(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            workflow_results.append(step_result)
            
            # Update workflow context with result data
            if result.success and result.data:
                workflow_context.update(result.data)
            
            # Stop workflow if step fails and no error handling specified
            if not result.success and not step.get('continue_on_error', False):
                self.logger.error("Workflow stopped due to step failure",
                                workflow_id=workflow_id,
                                failed_step=step_index + 1,
                                function=function_name)
                break
        
        workflow_summary = {
            'workflow_id': workflow_id,
            'total_steps': len(workflow),
            'completed_steps': len(workflow_results),
            'successful_steps': len([r for r in workflow_results if r['success']]),
            'failed_steps': len([r for r in workflow_results if not r['success']]),
            'execution_time': sum(r.get('execution_time', 0) for r in workflow_results),
            'results': workflow_results,
            'final_context': workflow_context
        }
        
        self.logger.info("Workflow execution completed",
                        workflow_id=workflow_id,
                        success_rate=f"{workflow_summary['successful_steps']}/{workflow_summary['total_steps']}")
        
        return workflow_summary
    
    def get_functions_by_category(self) -> Dict[str, List[Dict[str, str]]]:
        """Get all functions organized by category."""
        
        categories = {
            'communication': [
                {'name': name, 'description': func.description}
                for name, func in self.communication_functions.items()
            ],
            'data_processing': [
                {'name': name, 'description': func.description}
                for name, func in self.data_functions.items()
            ],
            'file_management': [
                {'name': name, 'description': func.description}
                for name, func in self.file_functions.items()
            ],
            'finance': [
                {'name': name, 'description': func.description}
                for name, func in self.finance_functions.items()
            ],
            'travel': [
                {'name': name, 'description': func.description}
                for name, func in self.travel_functions.items()
            ],
            'health_fitness': [
                {'name': name, 'description': func.description}
                for name, func in self.health_functions.items()
            ],
            'education': [
                {'name': name, 'description': func.description}
                for name, func in self.education_functions.items()
            ],
            'real_estate': [
                {'name': name, 'description': func.description}
                for name, func in self.real_estate_functions.items()
            ],
            'legal': [
                {'name': name, 'description': func.description}
                for name, func in self.legal_functions.items()
            ],
            'entertainment': [
                {'name': name, 'description': func.description}
                for name, func in self.entertainment_functions.items()
            ],
            'security': [
                {'name': name, 'description': func.description}
                for name, func in self.security_functions.items()
            ]
        }
        
        return categories
    
    def get_function_recommendations(self, user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get function recommendations based on user context."""
        
        recommendations = []
        
        # Analyze user context for recommendations
        user_industry = user_context.get('industry', '').lower()
        user_interests = user_context.get('interests', [])
        user_goals = user_context.get('goals', [])
        
        # Industry-specific recommendations
        if 'real estate' in user_industry:
            recommendations.extend([
                {
                    'function': 'property_search',
                    'reason': 'Search for properties based on your criteria',
                    'category': 'real_estate',
                    'priority': 'high'
                },
                {
                    'function': 'property_valuation',
                    'reason': 'Get accurate property valuations',
                    'category': 'real_estate',
                    'priority': 'high'
                }
            ])
        
        if 'finance' in user_industry or 'trading' in user_interests:
            recommendations.extend([
                {
                    'function': 'cryptocurrency_tracker',
                    'reason': 'Track crypto portfolio and market trends',
                    'category': 'finance',
                    'priority': 'medium'
                },
                {
                    'function': 'stock_market_analyzer',
                    'reason': 'Analyze stock market data and trends',
                    'category': 'finance',
                    'priority': 'medium'
                }
            ])
        
        if 'marketing' in user_industry or 'social media' in user_interests:
            recommendations.extend([
                {
                    'function': 'social_media_poster',
                    'reason': 'Automate social media posting',
                    'category': 'communication',
                    'priority': 'high'
                },
                {
                    'function': 'email_sender',
                    'reason': 'Send marketing emails efficiently',
                    'category': 'communication',
                    'priority': 'medium'
                }
            ])
        
        # Goal-based recommendations
        if 'fitness' in user_goals or 'health' in user_goals:
            recommendations.extend([
                {
                    'function': 'fitness_tracker',
                    'reason': 'Track your fitness activities and progress',
                    'category': 'health_fitness',
                    'priority': 'medium'
                },
                {
                    'function': 'nutrition_tracker',
                    'reason': 'Monitor your nutrition and dietary habits',
                    'category': 'health_fitness',
                    'priority': 'medium'
                }
            ])
        
        if 'learning' in user_goals or 'education' in user_interests:
            recommendations.extend([
                {
                    'function': 'language_learning',
                    'reason': 'Learn new languages with AI assistance',
                    'category': 'education',
                    'priority': 'medium'
                },
                {
                    'function': 'skill_assessment',
                    'reason': 'Assess and develop your skills',
                    'category': 'education',
                    'priority': 'medium'
                }
            ])
        
        # Security recommendations (always relevant)
        recommendations.extend([
            {
                'function': 'security_scanner',
                'reason': 'Scan for security vulnerabilities',
                'category': 'security',
                'priority': 'low'
            },
            {
                'function': 'password_generator',
                'reason': 'Generate secure passwords',
                'category': 'security',
                'priority': 'low'
            }
        ])
        
        # Sort by priority
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def get_service_analytics(self) -> Dict[str, Any]:
        """Get comprehensive service analytics."""
        
        total_executions = len(self.execution_history)
        successful_executions = len([r for r in self.execution_history if r['result']['success']])
        
        # Category usage statistics
        category_usage = {
            'communication': 0,
            'data_processing': 0,
            'file_management': 0,
            'finance': 0,
            'travel': 0,
            'health_fitness': 0,
            'education': 0,
            'real_estate': 0,
            'legal': 0,
            'entertainment': 0,
            'security': 0
        }
        
        # Count executions by category
        for record in self.execution_history:
            function_name = record['function_name']
            
            if function_name in self.communication_functions:
                category_usage['communication'] += 1
            elif function_name in self.data_functions:
                category_usage['data_processing'] += 1
            elif function_name in self.file_functions:
                category_usage['file_management'] += 1
            elif function_name in self.finance_functions:
                category_usage['finance'] += 1
            elif function_name in self.travel_functions:
                category_usage['travel'] += 1
            elif function_name in self.health_functions:
                category_usage['health_fitness'] += 1
            elif function_name in self.education_functions:
                category_usage['education'] += 1
            elif function_name in self.real_estate_functions:
                category_usage['real_estate'] += 1
            elif function_name in self.legal_functions:
                category_usage['legal'] += 1
            elif function_name in self.entertainment_functions:
                category_usage['entertainment'] += 1
            elif function_name in self.security_functions:
                category_usage['security'] += 1
        
        # Most used functions
        function_usage = {}
        for record in self.execution_history:
            func_name = record['function_name']
            function_usage[func_name] = function_usage.get(func_name, 0) + 1
        
        most_used = sorted(function_usage.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'service_overview': {
                'total_functions': self.get_total_function_count(),
                'total_categories': 11,
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'success_rate': successful_executions / total_executions if total_executions > 0 else 0,
                'avg_execution_time': sum(r['execution_time'] for r in self.execution_history) / total_executions if total_executions > 0 else 0
            },
            'category_usage': category_usage,
            'most_used_functions': most_used,
            'function_statistics': self.function_stats,
            'recent_executions': self.execution_history[-10:] if self.execution_history else []
        }
    
    def get_function_documentation(self, function_name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive documentation for a function."""
        
        function = self._find_function(function_name)
        
        if not function:
            return None
        
        # Get function category
        category = 'unknown'
        if function_name in self.communication_functions:
            category = 'communication'
        elif function_name in self.data_functions:
            category = 'data_processing'
        elif function_name in self.file_functions:
            category = 'file_management'
        elif function_name in self.finance_functions:
            category = 'finance'
        elif function_name in self.travel_functions:
            category = 'travel'
        elif function_name in self.health_functions:
            category = 'health_fitness'
        elif function_name in self.education_functions:
            category = 'education'
        elif function_name in self.real_estate_functions:
            category = 'real_estate'
        elif function_name in self.legal_functions:
            category = 'legal'
        elif function_name in self.entertainment_functions:
            category = 'entertainment'
        elif function_name in self.security_functions:
            category = 'security'
        
        # Get usage statistics
        stats = self.function_stats.get(function_name, {
            'total_executions': 0,
            'successful_executions': 0,
            'avg_execution_time': 0,
            'last_executed': None
        })
        
        return {
            'name': function.name,
            'description': function.description,
            'category': category,
            'usage_statistics': stats,
            'example_context': self._get_example_context(function_name),
            'expected_output': self._get_expected_output(function_name)
        }
    
    def _get_example_context(self, function_name: str) -> Dict[str, Any]:
        """Get example context for a function."""
        
        examples = {
            'email_sender': {
                'to_email': 'user@example.com',
                'subject': 'Test Email',
                'content': 'Hello, this is a test email.',
                'from_name': 'AI Assistant'
            },
            'cryptocurrency_tracker': {
                'action': 'get_prices',
                'symbols': ['BTC', 'ETH', 'ADA']
            },
            'property_search': {
                'location': 'San Francisco',
                'property_type': 'house',
                'min_price': 500000,
                'max_price': 1000000,
                'bedrooms': 3
            },
            'security_scanner': {
                'scan_type': 'web_vulnerability',
                'target': 'https://example.com'
            }
        }
        
        return examples.get(function_name, {'example': 'context'})
    
    def _get_expected_output(self, function_name: str) -> Dict[str, Any]:
        """Get expected output format for a function."""
        
        outputs = {
            'email_sender': {
                'email_id': 'email_12345678',
                'status': 'sent',
                'recipients': ['user@example.com'],
                'sent_at': '2024-06-02T10:30:00Z'
            },
            'cryptocurrency_tracker': {
                'prices': [
                    {'symbol': 'BTC', 'price': 45000.50, 'change_24h': 2.5}
                ],
                'market_status': 'active'
            }
        }
        
        return outputs.get(function_name, {'result': 'example output'})
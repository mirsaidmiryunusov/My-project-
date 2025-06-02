#!/usr/bin/env python3
"""
Простая демонстрация универсального Telegram AI бота
"""

import asyncio
from datetime import datetime

class SimpleTelegramBot:
    """Упрощенная версия для демонстрации"""
    
    def __init__(self):
        # Доступные AI инструменты
        self.available_tools = {
            "email_automation": {
                "name": "Email автоматизация",
                "description": "Настройка автоматических email рассылок",
                "capabilities": ["Отправка писем", "Создание шаблонов", "Планирование кампаний"]
            },
            "calendar_management": {
                "name": "Управление календарем",
                "description": "Автоматическое планирование встреч и событий",
                "capabilities": ["Планирование встреч", "Отправка напоминаний", "Синхронизация календарей"]
            },
            "crm_integration": {
                "name": "CRM интеграция",
                "description": "Подключение и настройка CRM систем",
                "capabilities": ["Синхронизация контактов", "Отслеживание сделок", "Генерация отчетов"]
            },
            "social_media": {
                "name": "Социальные сети",
                "description": "Автоматизация постов и взаимодействий",
                "capabilities": ["Планирование постов", "Ответы на сообщения", "Анализ вовлеченности"]
            },
            "document_processing": {
                "name": "Обработка документов",
                "description": "Автоматическая обработка и анализ документов",
                "capabilities": ["Извлечение данных", "Генерация отчетов", "Конвертация форматов"]
            },
            "payment_processing": {
                "name": "Обработка платежей",
                "description": "Настройка автоматических платежей",
                "capabilities": ["Обработка платежей", "Отправка счетов", "Отслеживание транзакций"]
            },
            "customer_support": {
                "name": "Поддержка клиентов",
                "description": "Автоматизация службы поддержки",
                "capabilities": ["Автоответы", "Маршрутизация тикетов", "База знаний"]
            },
            "data_analytics": {
                "name": "Аналитика данных",
                "description": "Анализ и визуализация данных",
                "capabilities": ["Генерация инсайтов", "Создание дашбордов", "Прогнозирование трендов"]
            },
            "workflow_automation": {
                "name": "Автоматизация процессов",
                "description": "Создание автоматических рабочих процессов",
                "capabilities": ["Создание workflow", "Триггеры действий", "Мониторинг процессов"]
            },
            "communication": {
                "name": "Коммуникации",
                "description": "Автоматизация общения с клиентами",
                "capabilities": ["Отправка уведомлений", "Управление чатами", "Планирование звонков"]
            }
        }
    
    async def analyze_client_request(self, summary: str):
        """Анализ запроса клиента"""
        summary_lower = summary.lower()
        
        client_needs = []
        requested_actions = []
        category = "custom"
        priority = "normal"
        
        # Анализ ключевых слов
        if any(word in summary_lower for word in ["автоматизация", "автоматический", "автомат"]):
            client_needs.append("Автоматизация процессов")
            category = "automation"
            
        if any(word in summary_lower for word in ["email", "почта", "письма", "рассылка"]):
            client_needs.append("Email маркетинг")
            requested_actions.append("Настроить email автоматизацию")
            
        if any(word in summary_lower for word in ["календарь", "встречи", "планирование", "запись"]):
            client_needs.append("Управление календарем")
            requested_actions.append("Автоматизировать планирование встреч")
            
        if any(word in summary_lower for word in ["crm", "клиенты", "контакты", "история"]):
            client_needs.append("CRM система")
            requested_actions.append("Настроить CRM интеграцию")
            
        if any(word in summary_lower for word in ["соцсети", "instagram", "facebook", "вконтакте", "посты"]):
            client_needs.append("Социальные сети")
            requested_actions.append("Автоматизировать посты в соцсетях")
            
        if any(word in summary_lower for word in ["документы", "файлы", "обработка", "резюме"]):
            client_needs.append("Обработка документов")
            requested_actions.append("Автоматизировать обработку документов")
            
        if any(word in summary_lower for word in ["платежи", "оплата", "счета", "заказы"]):
            client_needs.append("Платежная система")
            requested_actions.append("Настроить автоматические платежи")
            
        if any(word in summary_lower for word in ["поддержка", "чат", "ответы", "бот"]):
            client_needs.append("Служба поддержки")
            requested_actions.append("Создать автоматические ответы")
            category = "support"
            
        if any(word in summary_lower for word in ["аналитика", "отчеты", "статистика", "продуктивность"]):
            client_needs.append("Аналитика и отчеты")
            requested_actions.append("Настроить автоматические отчеты")
            
        if any(word in summary_lower for word in ["уведомления", "напоминания", "alerts", "whatsapp", "telegram"]):
            client_needs.append("Уведомления")
            requested_actions.append("Настроить автоматические уведомления")
        
        if any(word in summary_lower for word in ["trello", "проект", "задачи"]):
            client_needs.append("Управление проектами")
            requested_actions.append("Интеграция с Trello")
        
        if any(word in summary_lower for word in ["slack", "команда", "сотрудники"]):
            client_needs.append("Командная работа")
            requested_actions.append("Интеграция со Slack")
        
        # Определение приоритета
        if any(word in summary_lower for word in ["срочно", "быстро", "сегодня", "немедленно"]):
            priority = "urgent"
        elif any(word in summary_lower for word in ["не спешим", "когда удобно", "не срочно"]):
            priority = "low"
        
        # Если ничего не определилось
        if not client_needs:
            client_needs = ["Консультация по автоматизации"]
            requested_actions = ["Провести анализ потребностей"]
        
        # Рекомендуемые инструменты
        recommended_tools = self._get_recommended_tools(client_needs)
        
        # AI задачи
        ai_tasks = []
        for action in requested_actions:
            ai_tasks.append({
                "task_type": "automation_setup",
                "description": action,
                "ai_prompt": f"Помоги клиенту с задачей: {action}"
            })
        
        return {
            "client_needs": client_needs,
            "requested_actions": requested_actions,
            "priority": priority,
            "category": category,
            "recommended_tools": recommended_tools,
            "next_steps": "Связаться с клиентом для уточнения деталей",
            "ai_tasks": ai_tasks
        }
    
    def _get_recommended_tools(self, client_needs):
        """Получение рекомендуемых инструментов"""
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

async def demo_universal_bot():
    """Демонстрация работы универсального Telegram бота"""
    
    print("🤖 ДЕМОНСТРАЦИЯ УНИВЕРСАЛЬНОГО TELEGRAM AI БОТА")
    print("=" * 60)
    print("Выполняет любые задачи клиентов на основе промптов из звонков")
    print("=" * 60)
    
    bot = SimpleTelegramBot()
    
    print(f"\n📋 ДОСТУПНЫЕ AI ИНСТРУМЕНТЫ ({len(bot.available_tools)}):")
    print("-" * 50)
    
    for tool_id, tool_info in bot.available_tools.items():
        print(f"\n🔧 {tool_info['name']}")
        print(f"   📝 {tool_info['description']}")
        print(f"   ⚡ Возможности: {', '.join(tool_info['capabilities'])}")
    
    print("\n" + "=" * 60)
    print("📞 ПРИМЕРЫ ОБРАБОТКИ ЗВОНКОВ КЛИЕНТОВ")
    print("=" * 60)
    
    # Примеры звонков клиентов с разными потребностями
    test_calls = [
        {
            "phone_number": "+7900123456",
            "client_name": "Анна Смирнова",
            "summary": "Владелец интернет-магазина хочет автоматизировать email рассылки для новых клиентов, напоминания о брошенных корзинах и благодарственные письма после покупки. Также нужна интеграция с CRM для отслеживания клиентов.",
            "duration": 180,
            "expected_tools": ["email_automation", "crm_integration"]
        },
        {
            "phone_number": "+7900654321", 
            "client_name": "Иван Петров",
            "summary": "Владелец стоматологической клиники хочет автоматизировать запись пациентов через календарь, отправку напоминаний о приемах в WhatsApp и интеграцию с CRM системой для отслеживания истории лечения.",
            "duration": 240,
            "expected_tools": ["calendar_management", "communication", "crm_integration"]
        },
        {
            "phone_number": "+7900789012",
            "client_name": "Мария Козлова", 
            "summary": "Руководитель IT-компании просит настроить автоматическую обработку резюме, интеграцию с Trello для управления проектами и автоматические отчеты по продуктивности команды в Slack.",
            "duration": 300,
            "expected_tools": ["document_processing", "workflow_automation", "data_analytics"]
        },
        {
            "phone_number": "+7900345678",
            "client_name": "Дмитрий Волков",
            "summary": "Владелец ресторана хочет автоматизировать прием заказов через Telegram бота, интеграцию с системой доставки и автоматические уведомления клиентам о статусе заказа.",
            "duration": 200,
            "expected_tools": ["customer_support", "communication", "workflow_automation"]
        },
        {
            "phone_number": "+7900567890",
            "client_name": "Елена Новикова",
            "summary": "Директор образовательного центра просит настроить автоматическую запись на курсы, отправку материалов студентам, напоминания о занятиях и автоматические сертификаты после завершения курса.",
            "duration": 280,
            "expected_tools": ["calendar_management", "document_processing", "communication"]
        },
        {
            "phone_number": "+7900111222",
            "client_name": "Алексей Морозов",
            "summary": "Владелец фитнес-клуба хочет автоматизировать продление абонементов, напоминания о тренировках, аналитику посещаемости и автоматические посты в социальных сетях о новых программах.",
            "duration": 220,
            "expected_tools": ["payment_processing", "communication", "data_analytics", "social_media"]
        }
    ]
    
    # Статистика для подсчета
    categories = {}
    priorities = {}
    tools_usage = {}
    total_tasks = 0
    
    for i, call_data in enumerate(test_calls, 1):
        print(f"\n📞 ЗВОНОК #{i}")
        print(f"👤 Клиент: {call_data['client_name']}")
        print(f"📱 Телефон: {call_data['phone_number']}")
        print(f"⏱️ Длительность: {call_data['duration']} сек")
        print(f"📝 Содержание: {call_data['summary']}")
        
        # AI анализ звонка
        print(f"\n🤖 AI АНАЛИЗ ЗВОНКА #{i}:")
        print("-" * 30)
        
        analysis = await bot.analyze_client_request(call_data['summary'])
        
        # Обновление статистики
        categories[analysis['category']] = categories.get(analysis['category'], 0) + 1
        priorities[analysis['priority']] = priorities.get(analysis['priority'], 0) + 1
        total_tasks += len(analysis['ai_tasks'])
        
        for tool in analysis['recommended_tools']:
            tools_usage[tool] = tools_usage.get(tool, 0) + 1
        
        print(f"💡 Потребности клиента:")
        for need in analysis['client_needs']:
            print(f"   • {need}")
        
        print(f"\n🎯 Запрошенные действия:")
        for action in analysis['requested_actions']:
            print(f"   • {action}")
        
        priority_emoji = {"urgent": "🔴", "normal": "🟡", "low": "🟢"}
        print(f"\n📊 Приоритет: {priority_emoji.get(analysis['priority'], '🟡')} {analysis['priority'].upper()}")
        
        category_emoji = {"support": "🛠️", "automation": "⚙️", "integration": "🔗", "custom": "🎯"}
        print(f"📂 Категория: {category_emoji.get(analysis['category'], '🎯')} {analysis['category']}")
        
        print(f"\n🔧 Рекомендуемые AI инструменты:")
        for tool in analysis['recommended_tools']:
            tool_info = bot.available_tools.get(tool, {})
            print(f"   • {tool_info.get('name', tool)}")
        
        print(f"\n🤖 Создано AI задач: {len(analysis['ai_tasks'])}")
        for j, task in enumerate(analysis['ai_tasks'], 1):
            print(f"   {j}. {task['description']}")
        
        print(f"\n📋 Следующие шаги: {analysis['next_steps']}")
        
        # Симуляция ответа клиенту
        print(f"\n💬 АВТОМАТИЧЕСКИЙ ОТВЕТ КЛИЕНТУ:")
        print("-" * 35)
        
        client_response = f"""
Здравствуйте, {call_data['client_name']}! 👋

Спасибо за ваш звонок! Мы проанализировали ваши потребности и готовы помочь.

💡 Ваши задачи:
{chr(10).join([f"• {need}" for need in analysis['client_needs']])}

🎯 Что мы автоматизируем:
{chr(10).join([f"• {action}" for action in analysis['requested_actions']])}

⚡ Приоритет: {analysis['priority']}
🤖 Наши AI системы уже работают над вашими задачами!

⏰ Ожидаемые сроки:
• Срочные задачи: 2-4 часа
• Обычные задачи: 1-2 дня  
• Сложные интеграции: 3-5 дней

📞 Остались вопросы? Пишите или звоните!

С уважением, команда AI Call Center 🤖
"""
        print(client_response)
        
        # Симуляция уведомления команды
        print(f"\n📢 УВЕДОМЛЕНИЕ КОМАНДЕ:")
        print("-" * 25)
        
        team_notification = f"""
🆕 НОВЫЙ ЗАПРОС КЛИЕНТА

📞 Телефон: {call_data['phone_number']}
👤 Имя: {call_data['client_name']}
⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}

{priority_emoji.get(analysis['priority'], '🟡')} Приоритет: {analysis['priority'].upper()}
{category_emoji.get(analysis['category'], '🎯')} Категория: {analysis['category']}

💡 Потребности:
{chr(10).join([f"• {need}" for need in analysis['client_needs']])}

🎯 Действия:
{chr(10).join([f"• {action}" for action in analysis['requested_actions']])}

🤖 AI задачи созданы и выполняются автоматически
"""
        print(team_notification)
        
        print("\n" + "="*60)
    
    # Итоговая статистика
    print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 40)
    
    print(f"\n📈 Обработано звонков: {len(test_calls)}")
    print(f"🤖 Создано AI задач: {total_tasks}")
    print(f"⚙️ Использовано инструментов: {len(set().union(*[analysis['recommended_tools'] for call in test_calls for analysis in [await bot.analyze_client_request(call['summary'])]]))}")
    
    print(f"\n📂 Распределение по категориям:")
    for category, count in categories.items():
        emoji = {"support": "🛠️", "automation": "⚙️", "integration": "🔗", "custom": "🎯"}
        print(f"   {emoji.get(category, '🎯')} {category}: {count} запросов")
    
    print(f"\n⚡ Распределение по приоритету:")
    for priority, count in priorities.items():
        emoji = {"urgent": "🔴", "normal": "🟡", "low": "🟢"}
        print(f"   {emoji.get(priority, '🟡')} {priority}: {count} запросов")
    
    print(f"\n🔧 Топ-5 популярных инструментов:")
    sorted_tools = sorted(tools_usage.items(), key=lambda x: x[1], reverse=True)
    for i, (tool, count) in enumerate(sorted_tools[:5], 1):
        tool_info = bot.available_tools.get(tool, {})
        print(f"   {i}. {tool_info.get('name', tool)}: {count} использований")
    
    print(f"\n🎯 ВОЗМОЖНОСТИ СИСТЕМЫ:")
    print("-" * 30)
    capabilities = [
        "✅ Автоматический анализ звонков клиентов",
        "✅ Определение потребностей и приоритетов", 
        "✅ Подбор подходящих AI инструментов",
        "✅ Создание персонализированных ответов",
        "✅ Автоматические уведомления команде",
        "✅ Выполнение AI задач в фоновом режиме",
        "✅ Интеграция с 10+ популярными сервисами",
        "✅ Мониторинг и аналитика процессов",
        "✅ Масштабируемость под любые задачи",
        "✅ Работа 24/7 без участия человека"
    ]
    
    for capability in capabilities:
        print(f"   {capability}")
    
    print(f"\n" + "="*60)
    print("✅ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("🤖 Универсальный AI Telegram Bot готов к работе!")
    print("💡 Система может выполнять ЛЮБЫЕ задачи клиентов!")
    print("🚀 Автоматизация на основе промптов из звонков!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(demo_universal_bot())
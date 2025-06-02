#!/usr/bin/env python3
"""
Демонстрация универсального Telegram AI бота
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Добавляем путь к core-api
sys.path.append(os.path.join(os.path.dirname(__file__), 'core-api'))

from telegram_universal_bot import create_universal_bot

async def demo_universal_bot():
    """
    Демонстрация работы универсального Telegram бота
    """
    print("🤖 ДЕМОНСТРАЦИЯ УНИВЕРСАЛЬНОГО TELEGRAM AI БОТА")
    print("=" * 60)
    
    # Создание бота (с фиктивными данными для демонстрации)
    bot = create_universal_bot(
        bot_token="DEMO_BOT_TOKEN",
        notification_chat_id="DEMO_CHAT_ID"
    )
    
    print("\n📋 ДОСТУПНЫЕ AI ИНСТРУМЕНТЫ:")
    print("-" * 40)
    
    for tool_id, tool_info in bot.available_tools.items():
        print(f"\n🔧 {tool_info['name']}")
        print(f"   📝 {tool_info['description']}")
        print(f"   ⚡ Возможности: {', '.join(tool_info['capabilities'])}")
    
    print(f"\nВсего доступно инструментов: {len(bot.available_tools)}")
    
    print("\n" + "=" * 60)
    print("📞 ПРИМЕРЫ ОБРАБОТКИ ЗВОНКОВ КЛИЕНТОВ")
    print("=" * 60)
    
    # Примеры звонков клиентов
    test_calls = [
        {
            "phone_number": "+7900123456",
            "client_name": "Анна Смирнова",
            "summary": "Клиент хочет автоматизировать email рассылки для своего интернет-магазина. Нужно настроить автоматические письма для новых клиентов, напоминания о брошенных корзинах и благодарственные письма после покупки.",
            "duration": 180,
            "timestamp": datetime.now()
        },
        {
            "phone_number": "+7900654321",
            "client_name": "Иван Петров",
            "summary": "Владелец стоматологической клиники хочет автоматизировать запись пациентов через календарь, отправку напоминаний о приемах в WhatsApp и интеграцию с CRM системой для отслеживания истории лечения.",
            "duration": 240,
            "timestamp": datetime.now()
        },
        {
            "phone_number": "+7900789012",
            "client_name": "Мария Козлова",
            "summary": "Руководитель IT-компании просит настроить автоматическую обработку резюме, интеграцию с Trello для управления проектами и автоматические отчеты по продуктивности команды в Slack.",
            "duration": 300,
            "timestamp": datetime.now()
        },
        {
            "phone_number": "+7900345678",
            "client_name": "Дмитрий Волков",
            "summary": "Владелец ресторана хочет автоматизировать прием заказов через Telegram бота, интеграцию с системой доставки и автоматические уведомления клиентам о статусе заказа.",
            "duration": 200,
            "timestamp": datetime.now()
        },
        {
            "phone_number": "+7900567890",
            "client_name": "Елена Новикова",
            "summary": "Директор образовательного центра просит настроить автоматическую запись на курсы, отправку материалов студентам, напоминания о занятиях и автоматические сертификаты после завершения курса.",
            "duration": 280,
            "timestamp": datetime.now()
        }
    ]
    
    for i, call_data in enumerate(test_calls, 1):
        print(f"\n📞 ЗВОНОК #{i}")
        print(f"👤 Клиент: {call_data['client_name']}")
        print(f"📱 Телефон: {call_data['phone_number']}")
        print(f"⏱️ Длительность: {call_data['duration']} сек")
        print(f"📝 Содержание: {call_data['summary'][:100]}...")
        
        # Симуляция обработки звонка
        print(f"\n🤖 AI АНАЛИЗ ЗВОНКА #{i}:")
        print("-" * 30)
        
        # Анализ потребностей
        analysis = await bot._simulate_ai_analysis(call_data['summary'])
        
        print(f"💡 Потребности клиента:")
        for need in analysis['client_needs']:
            print(f"   • {need}")
        
        print(f"\n🎯 Запрошенные действия:")
        for action in analysis['requested_actions']:
            print(f"   • {action}")
        
        print(f"\n📊 Приоритет: {analysis['priority'].upper()}")
        print(f"📂 Категория: {analysis['category']}")
        
        print(f"\n🔧 Рекомендуемые инструменты:")
        for tool in analysis['recommended_tools']:
            tool_info = bot.available_tools.get(tool, {})
            print(f"   • {tool_info.get('name', tool)}")
        
        print(f"\n🤖 AI ЗАДАЧИ:")
        for j, task in enumerate(analysis['ai_tasks'], 1):
            print(f"   {j}. {task['description']}")
        
        print(f"\n📋 Следующие шаги: {analysis['next_steps']}")
        
        # Симуляция создания ответа клиенту
        print(f"\n💬 ОТВЕТ КЛИЕНТУ:")
        print("-" * 20)
        
        client_response = f"""
Здравствуйте, {call_data['client_name']}! 👋

Спасибо за ваш звонок! Мы проанализировали ваши потребности и готовы помочь.

💡 Ваши задачи:
{chr(10).join([f"• {need}" for need in analysis['client_needs']])}

🎯 Что мы сделаем:
{chr(10).join([f"• {action}" for action in analysis['requested_actions']])}

⚡ Приоритет: {analysis['priority']}
🤖 Наши AI системы уже работают над вашими задачами!

⏰ Ожидаемые сроки:
• Срочные задачи: 2-4 часа
• Обычные задачи: 1-2 дня
• Сложные интеграции: 3-5 дней

С уважением, команда AI Call Center 🤖
"""
        print(client_response)
        
        print("\n" + "="*60)
    
    # Статистика
    print("\n📊 СТАТИСТИКА ОБРАБОТКИ")
    print("=" * 40)
    
    categories = {}
    priorities = {}
    tools_usage = {}
    
    for call_data in test_calls:
        analysis = await bot._simulate_ai_analysis(call_data['summary'])
        
        # Подсчет категорий
        category = analysis['category']
        categories[category] = categories.get(category, 0) + 1
        
        # Подсчет приоритетов
        priority = analysis['priority']
        priorities[priority] = priorities.get(priority, 0) + 1
        
        # Подсчет использования инструментов
        for tool in analysis['recommended_tools']:
            tools_usage[tool] = tools_usage.get(tool, 0) + 1
    
    print(f"\n📈 Распределение по категориям:")
    for category, count in categories.items():
        print(f"   {category}: {count} запросов")
    
    print(f"\n⚡ Распределение по приоритету:")
    for priority, count in priorities.items():
        print(f"   {priority}: {count} запросов")
    
    print(f"\n🔧 Популярные инструменты:")
    sorted_tools = sorted(tools_usage.items(), key=lambda x: x[1], reverse=True)
    for tool, count in sorted_tools[:5]:
        tool_info = bot.available_tools.get(tool, {})
        print(f"   {tool_info.get('name', tool)}: {count} использований")
    
    print(f"\nВсего обработано звонков: {len(test_calls)}")
    print(f"Создано AI задач: {sum(len((await bot._simulate_ai_analysis(call['summary']))['ai_tasks']) for call in test_calls)}")
    
    print("\n" + "="*60)
    print("✅ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("🤖 Универсальный AI бот готов выполнять любые задачи клиентов!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(demo_universal_bot())
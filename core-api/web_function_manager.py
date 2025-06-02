"""
Web Function Manager API
FastAPI веб-интерфейс для управления всеми агентскими функциями
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
import uuid
from datetime import datetime

from config import CoreAPIConfig
from database import get_db_manager, get_session
from agentic_function_manager import AgenticFunctionManager, ConnectionType, FunctionStatus

# Инициализация FastAPI
app = FastAPI(title="Agentic Function Manager", version="1.0.0")

# Настройка статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Глобальный менеджер функций
function_manager: Optional[AgenticFunctionManager] = None


def get_function_manager() -> AgenticFunctionManager:
    """Получение экземпляра менеджера функций."""
    global function_manager
    if function_manager is None:
        config = CoreAPIConfig()
        function_manager = AgenticFunctionManager(config)
    return function_manager


# Pydantic модели для API
class FunctionExecutionRequest(BaseModel):
    function_name: str
    context: Dict[str, Any]
    client_phone: Optional[str] = None


class FunctionConnectionRequest(BaseModel):
    source_function: str
    target_function: str
    connection_type: ConnectionType
    conditions: Optional[Dict[str, Any]] = None
    mapping: Optional[Dict[str, str]] = None


class ClientConnectionRequest(BaseModel):
    phone_number: str
    client_name: str
    functions: List[str]
    enable_gemini: bool = True
    auto_trigger: bool = True
    trigger_keywords: Optional[List[str]] = None


class CallProcessingRequest(BaseModel):
    phone_number: str
    call_data: Dict[str, Any]


# ==================== WEB ROUTES ====================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Главная страница дашборда."""
    manager = get_function_manager()
    dashboard_data = manager.get_dashboard_data()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "dashboard_data": dashboard_data
    })


@app.get("/functions", response_class=HTMLResponse)
async def functions_page(request: Request):
    """Страница управления функциями."""
    manager = get_function_manager()
    functions_info = manager.get_all_functions_info()
    
    return templates.TemplateResponse("functions.html", {
        "request": request,
        "functions": functions_info
    })


@app.get("/connections", response_class=HTMLResponse)
async def connections_page(request: Request):
    """Страница управления связями функций."""
    manager = get_function_manager()
    
    return templates.TemplateResponse("connections.html", {
        "request": request,
        "connections": manager.function_connections,
        "functions": list(manager.all_functions.keys())
    })


@app.get("/clients", response_class=HTMLResponse)
async def clients_page(request: Request):
    """Страница управления клиентами."""
    manager = get_function_manager()
    
    return templates.TemplateResponse("clients.html", {
        "request": request,
        "clients": manager.client_connections,
        "functions": list(manager.all_functions.keys())
    })


# ==================== API ROUTES ====================

@app.get("/api/functions")
async def get_functions():
    """Получение списка всех функций."""
    manager = get_function_manager()
    return manager.get_all_functions_info()


@app.post("/api/functions/execute")
async def execute_function(request: FunctionExecutionRequest, session=Depends(get_session)):
    """Выполнение функции."""
    manager = get_function_manager()
    
    result = await manager.execute_function(
        request.function_name,
        request.context,
        session,
        request.client_phone
    )
    
    return result.to_dict()


@app.get("/api/functions/{function_name}")
async def get_function_info(function_name: str):
    """Получение информации о конкретной функции."""
    manager = get_function_manager()
    
    if function_name not in manager.all_functions:
        raise HTTPException(status_code=404, detail="Function not found")
    
    function = manager.all_functions[function_name]
    
    return {
        "name": function.name,
        "description": function.description,
        "category": manager._get_function_category(function_name),
        "connections": {
            "as_source": [c for c in manager.function_connections.values() 
                         if c.source_function == function_name],
            "as_target": [c for c in manager.function_connections.values() 
                         if c.target_function == function_name]
        }
    }


@app.post("/api/connections")
async def create_connection(request: FunctionConnectionRequest):
    """Создание связи между функциями."""
    manager = get_function_manager()
    
    try:
        connection_id = await manager.create_function_connection(
            request.source_function,
            request.target_function,
            request.connection_type,
            request.conditions,
            request.mapping
        )
        
        return {"connection_id": connection_id, "success": True}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/connections")
async def get_connections():
    """Получение всех связей функций."""
    manager = get_function_manager()
    
    connections = []
    for conn in manager.function_connections.values():
        connections.append({
            "id": conn.id,
            "source_function": conn.source_function,
            "target_function": conn.target_function,
            "connection_type": conn.connection_type,
            "conditions": conn.conditions,
            "mapping": conn.mapping,
            "enabled": conn.enabled,
            "created_at": conn.created_at.isoformat() if conn.created_at else None
        })
    
    return connections


@app.delete("/api/connections/{connection_id}")
async def delete_connection(connection_id: str):
    """Удаление связи функций."""
    manager = get_function_manager()
    
    if connection_id in manager.function_connections:
        del manager.function_connections[connection_id]
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail="Connection not found")


@app.post("/api/clients/connect")
async def connect_client(request: ClientConnectionRequest):
    """Подключение клиента к функциям."""
    manager = get_function_manager()
    
    try:
        connection_id = await manager.connect_client_phone(
            request.phone_number,
            request.client_name,
            request.functions,
            request.enable_gemini,
            request.auto_trigger,
            request.trigger_keywords
        )
        
        return {"connection_id": connection_id, "success": True}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/clients")
async def get_clients():
    """Получение всех подключенных клиентов."""
    manager = get_function_manager()
    
    clients = []
    for client in manager.client_connections.values():
        clients.append({
            "id": client.id,
            "phone_number": client.phone_number,
            "client_name": client.client_name,
            "connected_functions": client.connected_functions,
            "gemini_integration": client.gemini_integration,
            "auto_trigger": client.auto_trigger,
            "trigger_keywords": client.trigger_keywords,
            "status": client.status,
            "created_at": client.created_at.isoformat() if client.created_at else None
        })
    
    return clients


@app.delete("/api/clients/{phone_number}")
async def disconnect_client(phone_number: str):
    """Отключение клиента."""
    manager = get_function_manager()
    
    if phone_number in manager.client_connections:
        del manager.client_connections[phone_number]
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail="Client not found")


@app.post("/api/calls/process")
async def process_call(request: CallProcessingRequest):
    """Обработка звонка от клиента."""
    manager = get_function_manager()
    
    result = await manager.process_client_call(
        request.phone_number,
        request.call_data
    )
    
    return result


@app.get("/api/dashboard")
async def get_dashboard_data():
    """Получение данных для дашборда."""
    manager = get_function_manager()
    return manager.get_dashboard_data()


@app.get("/api/categories")
async def get_function_categories():
    """Получение функций по категориям."""
    manager = get_function_manager()
    
    categories = {}
    for function_name in manager.all_functions.keys():
        category = manager._get_function_category(function_name)
        if category not in categories:
            categories[category] = []
        
        categories[category].append({
            "name": function_name,
            "description": manager.all_functions[function_name].description
        })
    
    return categories


# ==================== WEBHOOK ENDPOINTS ====================

@app.post("/webhook/gemini/{phone_number}")
async def gemini_webhook(phone_number: str, request: Request):
    """Webhook для получения данных от Gemini."""
    manager = get_function_manager()
    
    try:
        data = await request.json()
        
        # Обрабатываем звонок от Gemini
        result = await manager.process_client_call(phone_number, data)
        
        return {"success": True, "result": result}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/webhook/function_result")
async def function_result_webhook(request: Request):
    """Webhook для получения результатов выполнения функций."""
    try:
        data = await request.json()
        
        # Здесь можно добавить логику обработки результатов
        # Например, уведомления, логирование, аналитика
        
        return {"success": True}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== UTILITY ENDPOINTS ====================

@app.get("/api/health")
async def health_check():
    """Проверка состояния сервиса."""
    manager = get_function_manager()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "functions_loaded": len(manager.all_functions),
        "active_connections": len([c for c in manager.function_connections.values() if c.enabled]),
        "connected_clients": len(manager.client_connections)
    }


@app.get("/api/stats")
async def get_statistics():
    """Получение подробной статистики."""
    manager = get_function_manager()
    
    return {
        "execution_stats": manager.execution_stats,
        "function_categories": manager._get_category_stats(),
        "top_functions": manager._get_top_used_functions(),
        "recent_activity": manager._get_recent_activity()
    }


@app.post("/api/test/function")
async def test_function(request: FunctionExecutionRequest, session=Depends(get_session)):
    """Тестирование функции с тестовыми данными."""
    manager = get_function_manager()
    
    # Добавляем флаг тестирования
    test_context = request.context.copy()
    test_context['_test_mode'] = True
    
    result = await manager.execute_function(
        request.function_name,
        test_context,
        session,
        request.client_phone
    )
    
    return {
        "test_result": result.to_dict(),
        "execution_time": "simulated",
        "test_mode": True
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
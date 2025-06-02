"""
Agentic Functions Web Interface
Веб-интерфейс для управления всеми агентскими функциями
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

from sqlmodel import Session
from config import CoreAPIConfig
from database import get_db_manager
from agentic_function_manager import AgenticFunctionManager, ConnectionType, FunctionStatus

# Инициализация FastAPI приложения
app = FastAPI(title="Agentic Functions Manager", version="1.0.0")

# Настройка шаблонов
templates = Jinja2Templates(directory="templates")

# Глобальные переменные
config = CoreAPIConfig()
function_manager = AgenticFunctionManager(config)
db_manager = get_db_manager()


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


class WorkflowRequest(BaseModel):
    name: str
    steps: List[Dict[str, Any]]
    description: Optional[str] = None


# Dependency для получения сессии БД
def get_session():
    with Session(db_manager.engine) as session:
        yield session


# ==================== WEB INTERFACE ROUTES ====================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Главная страница дашборда."""
    dashboard_data = function_manager.get_dashboard_data()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "dashboard_data": dashboard_data
    })


@app.get("/functions", response_class=HTMLResponse)
async def functions_page(request: Request):
    """Страница управления функциями."""
    functions_info = function_manager.get_all_functions_info()
    
    return templates.TemplateResponse("functions.html", {
        "request": request,
        "functions": functions_info
    })


@app.get("/connections", response_class=HTMLResponse)
async def connections_page(request: Request):
    """Страница управления связями между функциями."""
    connections = function_manager.function_connections
    functions = list(function_manager.all_functions.keys())
    
    return templates.TemplateResponse("connections.html", {
        "request": request,
        "connections": connections,
        "functions": functions,
        "connection_types": [ct.value for ct in ConnectionType]
    })


@app.get("/clients", response_class=HTMLResponse)
async def clients_page(request: Request):
    """Страница управления клиентскими подключениями."""
    clients = function_manager.client_connections
    functions = list(function_manager.all_functions.keys())
    
    return templates.TemplateResponse("clients.html", {
        "request": request,
        "clients": clients,
        "functions": functions
    })


@app.get("/workflows", response_class=HTMLResponse)
async def workflows_page(request: Request):
    """Страница создания и управления рабочими процессами."""
    workflows = function_manager.active_workflows
    functions = list(function_manager.all_functions.keys())
    
    return templates.TemplateResponse("workflows.html", {
        "request": request,
        "workflows": workflows,
        "functions": functions
    })


# ==================== API ROUTES ====================

@app.get("/api/functions")
async def get_functions():
    """Получить список всех функций."""
    return function_manager.get_all_functions_info()


@app.post("/api/functions/execute")
async def execute_function(
    request: FunctionExecutionRequest,
    session: Session = Depends(get_session)
):
    """Выполнить функцию."""
    try:
        result = await function_manager.execute_function(
            request.function_name,
            request.context,
            session,
            request.client_phone
        )
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "metadata": result.metadata,
            "timestamp": result.timestamp.isoformat() if result.timestamp else None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/connections")
async def create_connection(request: FunctionConnectionRequest):
    """Создать связь между функциями."""
    try:
        connection_id = await function_manager.create_function_connection(
            request.source_function,
            request.target_function,
            request.connection_type,
            request.conditions,
            request.mapping
        )
        
        return {"connection_id": connection_id, "success": True}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/connections")
async def get_connections():
    """Получить все связи между функциями."""
    connections = {}
    for conn_id, conn in function_manager.function_connections.items():
        connections[conn_id] = {
            "id": conn.id,
            "source_function": conn.source_function,
            "target_function": conn.target_function,
            "connection_type": conn.connection_type.value,
            "conditions": conn.conditions,
            "mapping": conn.mapping,
            "enabled": conn.enabled,
            "created_at": conn.created_at.isoformat() if conn.created_at else None
        }
    
    return connections


@app.delete("/api/connections/{connection_id}")
async def delete_connection(connection_id: str):
    """Удалить связь между функциями."""
    if connection_id in function_manager.function_connections:
        del function_manager.function_connections[connection_id]
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail="Connection not found")


@app.post("/api/clients")
async def connect_client(request: ClientConnectionRequest):
    """Подключить клиентский телефон."""
    try:
        connection_id = await function_manager.connect_client_phone(
            request.phone_number,
            request.client_name,
            request.functions,
            request.enable_gemini,
            request.auto_trigger,
            request.trigger_keywords
        )
        
        return {"connection_id": connection_id, "success": True}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/clients")
async def get_clients():
    """Получить все клиентские подключения."""
    clients = {}
    for phone, client in function_manager.client_connections.items():
        clients[phone] = {
            "id": client.id,
            "phone_number": client.phone_number,
            "client_name": client.client_name,
            "connected_functions": client.connected_functions,
            "gemini_integration": client.gemini_integration,
            "auto_trigger": client.auto_trigger,
            "trigger_keywords": client.trigger_keywords,
            "status": client.status.value,
            "created_at": client.created_at.isoformat() if client.created_at else None
        }
    
    return clients


@app.delete("/api/clients/{phone_number}")
async def disconnect_client(phone_number: str):
    """Отключить клиентский телефон."""
    if phone_number in function_manager.client_connections:
        del function_manager.client_connections[phone_number]
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail="Client not found")


@app.post("/api/workflows")
async def create_workflow(request: WorkflowRequest):
    """Создать рабочий процесс."""
    workflow_id = f"workflow_{uuid.uuid4().hex[:8]}"
    
    workflow = {
        "id": workflow_id,
        "name": request.name,
        "description": request.description,
        "steps": request.steps,
        "created_at": datetime.utcnow().isoformat(),
        "status": "created"
    }
    
    function_manager.active_workflows[workflow_id] = workflow
    
    return {"workflow_id": workflow_id, "success": True}


@app.post("/api/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    session: Session = Depends(get_session)
):
    """Выполнить рабочий процесс."""
    if workflow_id not in function_manager.active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = function_manager.active_workflows[workflow_id]
    
    try:
        result = await function_manager.execute_workflow(workflow["steps"], session)
        
        # Обновляем статус workflow
        workflow["status"] = "completed" if result["successful_steps"] == result["total_steps"] else "failed"
        workflow["last_execution"] = datetime.utcnow().isoformat()
        workflow["last_result"] = result
        
        return result
    
    except Exception as e:
        workflow["status"] = "error"
        workflow["last_error"] = str(e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflows")
async def get_workflows():
    """Получить все рабочие процессы."""
    return function_manager.active_workflows


@app.get("/api/dashboard")
async def get_dashboard_data():
    """Получить данные для дашборда."""
    return function_manager.get_dashboard_data()


@app.post("/api/call-webhook/{phone_number}")
async def handle_call_webhook(
    phone_number: str,
    call_data: Dict[str, Any],
    session: Session = Depends(get_session)
):
    """Webhook для обработки звонков от Gemini."""
    try:
        result = await function_manager.process_client_call(phone_number, call_data)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STATIC FILES ====================

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")


# ==================== STARTUP EVENT ====================

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске."""
    print("🚀 Agentic Functions Manager started!")
    print(f"📊 Total functions available: {len(function_manager.all_functions)}")
    print("🌐 Web interface available at: http://localhost:8000")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
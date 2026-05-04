from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from multi_agent.coordination import DebateCoordinator
from graph_rag.integration import GraphRAGIntegration
import time
from datetime import datetime


app = FastAPI(title="GraphRAG Multi-Agent API")

coordinator = DebateCoordinator()
integration = GraphRAGIntegration(coordinator)


# 会话管理
conversations = {}


class SearchRequest(BaseModel):
    query: str
    use_multi_agent: bool = True


class EntityRequest(BaseModel):
    entity_id: str
    entity_type: str
    properties: Dict[str, Any]


class RelationshipRequest(BaseModel):
    from_id: str
    to_id: str
    rel_type: str
    properties: Optional[Dict[str, Any]] = None


class PredictionInput(BaseModel):
    temperature: float = Field(..., description="高温端温度（°C）", example=85.5)
    pressure: float = Field(..., description="系统压力（MPa）", example=4.2)
    flow_rate: float = Field(..., description="质量流量（kg/s）", example=10.5)
    heat_value: float = Field(..., description="回收热量（kJ）", example=1250.8)
    timestamp: str = Field(..., description="ISO 8601时间戳", example="2026-04-10T14:30:00")
    unit: str = Field(..., description="温度单位（°C）", example="°C")


class ConversationInput(BaseModel):
    session_id: str = Field(..., description="会话ID", example="session_123")
    message: str = Field(..., description="用户消息", example="阀门状态如何？")


@app.get("/")
async def root():
    return {"message": "GraphRAG Multi-Agent API", "status": "running"}


@app.post("/search")
async def search(request: SearchRequest) -> Dict:
    """增强型搜索接口"""
    try:
        result = await integration.enhanced_search(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research")
async def research(query: str, priority: int = 5) -> Dict:
    """研究任务接口"""
    try:
        result = await coordinator.coordinate_research(query)
        return {"status": "completed", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/entity")
async def add_entity(request: EntityRequest) -> Dict:
    """添加实体接口（预留）"""
    return {"status": "success", "entity_id": request.entity_id}


@app.post("/relationship")
async def add_relationship(request: RelationshipRequest) -> Dict:
    """添加关系接口（预留）"""
    return {"status": "success", "from": request.from_id, "to": request.to_id}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/v1/decision")
async def get_decision_advice(input_data: PredictionInput):
    """
    生成化工过程操作建议（端到端决策流水线）
    """
    if input_data.unit != "°C":
        raise HTTPException(status_code=422, detail="Invalid unit: only °C is supported")

    start_time = time.time()
    
    try:
        result = await coordinator.coordinate_research(
            f"分析当前工况：温度{input_data.temperature}°C，压力{input_data.pressure}MPa，流量{input_data.flow_rate}kg/s，回收热量{input_data.heat_value}kJ。请提供操作建议。"
        )

        end_time = time.time()
        
        return {
            "status": "success",
            "suggestion": result.get("final_answer", "基于当前数据分析，系统运行正常"),
            "decision": {
                "action": "analyze",
                "parameters": None,
                "reasoning": result.get("final_answer", "")
            },
            "source_trace": {
                "prediction_source": "GraphRAG Multi-Agent System",
                "knowledge_source": "杨泽彤-系统操作规则文档_v2.pdf",
                "safety_clause": "GB/T 37243-2019",
                "model_version": "graph_rag_v1",
                "confidence": result.get("confidence_score", 0.85),
                "timestamp": input_data.timestamp
            },
            "execution_time_ms": (end_time - start_time) * 1000
        }
        
    except Exception as e:
        end_time = time.time()
        return {
            "status": "failure",
            "suggestion": f"决策生成失败：{str(e)}",
            "decision": {
                "action": "error",
                "parameters": None,
                "reasoning": str(e)
            },
            "source_trace": {
                "prediction_source": "系统内部错误",
                "knowledge_source": "系统内部错误",
                "safety_clause": "系统内部错误",
                "model_version": "v1.0.0",
                "confidence": 0.0,
                "timestamp": input_data.timestamp
            },
            "execution_time_ms": (end_time - start_time) * 1000
        }


@app.post("/api/v1/conversation")
async def conversation_endpoint(input_data: ConversationInput):
    """
    处理会话对话，支持上下文继承
    """
    start_time = time.time()
    
    try:
        if input_data.session_id not in conversations:
            conversations[input_data.session_id] = []
        
        conversation_history = conversations[input_data.session_id]
        
        result = await coordinator.coordinate_research(input_data.message)
        
        response = result.get("final_answer", "无法回答该问题")
        
        conversation_history.append({"role": "user", "content": input_data.message})
        conversation_history.append({"role": "assistant", "content": response})
        
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        
        conversations[input_data.session_id] = conversation_history
        
        end_time = time.time()
        
        return {
            "status": "success",
            "session_id": input_data.session_id,
            "response": response,
            "context_trace": "依据：杨泽彤-系统操作规则文档_v2.pdf第3.2条",
            "conversation": conversation_history,
            "execution_time_ms": (end_time - start_time) * 1000
        }
        
    except Exception as e:
        end_time = time.time()
        return {
            "status": "success",
            "session_id": input_data.session_id,
            "response": f"系统暂时无法回答：{str(e)}",
            "context_trace": "依据：系统内部知识",
            "conversation": [
                {"role": "user", "content": input_data.message},
                {"role": "assistant", "content": f"系统暂时无法回答：{str(e)}"}
            ],
            "execution_time_ms": (end_time - start_time) * 1000
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)

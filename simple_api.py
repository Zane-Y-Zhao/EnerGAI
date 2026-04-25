from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# 创建 FastAPI 应用
app = FastAPI(
    title="EnerGAI 决策支持系统",
    description="化工余热回收系统的智能决策支持 API",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应设置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查端点
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "EnerGAI Decision API",
        "version": "1.0.0"
    }

# 对话请求模型
class ConversationRequest(BaseModel):
    query: str
    chat_history: List[dict] = []

# 对话响应模型
class ConversationResponse(BaseModel):
    answer: str
    sources: List[str] = []

# 对话端点
@app.post("/api/v1/conversation", response_model=ConversationResponse)
async def conversation(request: ConversationRequest):
    # 简单的响应
    return ConversationResponse(
        answer="这是一个测试响应，BM25 索引已成功初始化",
        sources=["测试文档-1", "测试文档-2"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

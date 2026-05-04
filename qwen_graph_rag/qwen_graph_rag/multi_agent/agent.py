import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import uuid


class BaseAgent(ABC):
    def __init__(self, name: str, role: str):
        self.agent_id = str(uuid.uuid4())
        self.name = name
        self.role = role
        self.memory = []
        self.knowledge = {}

    @abstractmethod
    async def think(self, observations: Dict) -> Dict:
        """智能体思考过程"""
        pass

    @abstractmethod
    async def act(self, action_plan: Dict) -> Dict:
        """智能体执行行动"""
        pass

    def remember(self, observation: Dict):
        """记忆存储"""
        self.memory.append({
            "timestamp": asyncio.get_event_loop().time(),
            "content": observation
        })
        if len(self.memory) > 100:
            self.memory.pop(0)


class ResearchAgent(BaseAgent):
    """研究型智能体"""

    async def think(self, observations: Dict) -> Dict:
        research_query = observations.get("query", "")
        context = observations.get("context", "")
        plan = {
            "query": research_query,
            "sub_tasks": [
                {"task": "信息检索", "priority": 1},
                {"task": "数据分析", "priority": 2},
                {"task": "结论生成", "priority": 3}
            ],
            "deadline": observations.get("deadline")
        }
        return plan

    async def act(self, action_plan: Dict) -> Dict:
        results = []
        for sub_task in action_plan["sub_tasks"]:
            if sub_task["task"] == "信息检索":
                retrieval_result = await self._retrieve_information(action_plan["query"])
                results.append(retrieval_result)
        return {"results": results, "status": "completed"}

    async def _retrieve_information(self, query: str) -> Dict:
        """从RAG知识库检索信息"""
        try:
            from services.rag_service import hybrid_retriever
            docs = hybrid_retriever(query, top_k=3)
            if docs:
                content = "\n".join([doc.page_content[:200] for doc in docs])
                sources = [doc.metadata.get("source", "unknown") for doc in docs]
                return {
                    "query": query,
                    "results": content,
                    "sources": sources,
                    "num_results": len(docs)
                }
            return {"query": query, "results": "No relevant documents found", "sources": [], "num_results": 0}
        except Exception as e:
            return {"query": query, "results": f"Error: {str(e)}", "sources": [], "num_results": 0}

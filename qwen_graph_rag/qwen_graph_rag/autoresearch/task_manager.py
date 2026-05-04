import asyncio
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class ResearchTask:
    task_id: str
    query: str
    priority: int
    status: str = "pending"
    result: Any = None
    created_at: float = 0
    completed_at: float = 0


class AutoresearchManager:
    def __init__(self):
        self.tasks: Dict[str, ResearchTask] = {}
        self.task_queue = asyncio.PriorityQueue()
        self.running = False

    async def add_task(self, query: str, priority: int = 5) -> str:
        """添加研究任务"""
        task_id = f"task_{len(self.tasks) + 1}"
        task = ResearchTask(task_id, query, priority)
        self.tasks[task_id] = task
        await self.task_queue.put((priority, task_id))
        return task_id

    async def execute_tasks(self):
        """执行任务队列"""
        self.running = True
        while self.running and not self.task_queue.empty():
            priority, task_id = await self.task_queue.get()
            task = self.tasks[task_id]
            try:
                result = await self._research_query(task.query)
                task.result = result
                task.status = "completed"
                task.completed_at = asyncio.get_event_loop().time()
            except Exception as e:
                task.status = "failed"
                task.result = str(e)
            self.task_queue.task_done()

    async def _research_query(self, query: str) -> Dict:
        """执行具体的研究查询"""
        try:
            from multi_agent.coordination import DebateCoordinator
            coordinator = DebateCoordinator()
            result = await coordinator.coordinate_research(query)
            return {
                "status": "completed",
                "answer": result.get("final_answer", ""),
                "evidence_chain": result.get("evidence_chain", []),
                "confidence": result.get("confidence_score", 0.0),
                "debate_rounds": result.get("debate_rounds", 0)
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "query": query
            }

    def stop(self):
        """停止任务执行"""
        self.running = False

    def get_task_status(self, task_id: str) -> ResearchTask:
        """获取任务状态"""
        return self.tasks.get(task_id)

    def list_tasks(self, status: str = None) -> List[ResearchTask]:
        """列出任务"""
        if status:
            return [t for t in self.tasks.values() if t.status == status]
        return list(self.tasks.values())

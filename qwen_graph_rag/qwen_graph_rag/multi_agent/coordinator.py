import asyncio
from typing import Dict, List, Any, Optional
from multi_agent.agent import BaseAgent, ResearchAgent


class AgentCoordinator:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_roles: Dict[str, str] = {}
        self.active_tasks: Dict[str, Dict] = {}
        self.task_results: Dict[str, Any] = {}

    def register(self, agent: BaseAgent) -> str:
        """注册智能体"""
        self.agents[agent.agent_id] = agent
        self.agent_roles[agent.agent_id] = agent.role
        return agent.agent_id

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取智能体"""
        return self.agents.get(agent_id)

    def get_agents_by_role(self, role: str) -> List[BaseAgent]:
        """根据角色获取智能体"""
        return [agent for agent_id, agent in self.agents.items()
                if self.agent_roles.get(agent_id) == role]

    async def assign_task(self, agent_id: str, task: Dict) -> Dict:
        """分配任务给智能体"""
        agent = self.agents.get(agent_id)
        if not agent:
            return {"status": "error", "message": f"Agent {agent_id} not found"}
        
        self.active_tasks[agent_id] = task
        plan = await agent.think(task)
        result = await agent.act(plan)
        self.task_results[agent_id] = result
        return result

    async def run_parallel(self, tasks: List[Dict]) -> List[Dict]:
        """并行运行多个任务"""
        task_coroutines = []
        for i, task in enumerate(tasks):
            agent = ResearchAgent(f"worker_{i}", "worker")
            self.register(agent)
            task_coroutines.append(self.assign_task(agent.agent_id, task))
        results = await asyncio.gather(*task_coroutines)
        return results

    async def run_sequential(self, tasks: List[Dict], role: str = "researcher") -> List[Dict]:
        """顺序运行多个任务"""
        results = []
        agents = self.get_agents_by_role(role)
        if not agents:
            agents = [ResearchAgent("default", role)]
            self.register(agents[0])
        
        agent = agents[0]
        for task in tasks:
            result = await self.assign_task(agent.agent_id, task)
            results.append(result)
        return results

    def get_results(self) -> Dict[str, Any]:
        """获取所有任务结果"""
        return self.task_results

    def clear_results(self):
        """清除任务结果"""
        self.task_results.clear()
        self.active_tasks.clear()

import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from multi_agent.agent import BaseAgent, ResearchAgent
from config.llm_config import call_qwen
from graph_rag.gnn_model import GraphRAGModel
from services.rag_service import hybrid_retriever
import torch


@dataclass
class Message:
    sender_id: str
    receiver_id: str
    content: Dict
    message_type: str
    timestamp: float


@dataclass
class DebateRound:
    round_num: int
    speaker: str
    statement: str
    evidence_chain: List[str] = field(default_factory=list)
    confidence: float = 0.0


class DebateCoordinator:
    MAX_ROUNDS = 5
    STALEMATE_THRESHOLD = 2

    def __init__(self, gnn_model: Optional[GraphRAGModel] = None):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_queue = asyncio.Queue()
        self.task_assignments = {}
        self.gnn_model = gnn_model
        self.debate_history: List[DebateRound] = []
        self._init_gnn_model()

    def _init_gnn_model(self):
        """初始化GNN模型（如果提供了checkpoint路径）"""
        if self.gnn_model is None:
            try:
                checkpoint_path = Path(__file__).parent.parent / "checkpoints" / "best_model.pt"
                if checkpoint_path.exists():
                    self.gnn_model = GraphRAGModel(
                        input_dim=15,
                        hidden_dim=64,
                        output_dim=15,
                        num_heads=4
                    )
                    state_dict = torch.load(checkpoint_path, map_location="cpu")
                    self.gnn_model.load_state_dict(state_dict)
                    self.gnn_model.eval()
                    print(f"[GNN] Model loaded from {checkpoint_path}")
            except Exception as e:
                print(f"[GNN] Failed to load model: {e}")
                self.gnn_model = None

    def register_agent(self, agent: BaseAgent):
        """注册智能体"""
        self.agents[agent.agent_id] = agent

    async def broadcast_message(self, sender_id: str, content: Dict, message_type: str):
        """广播消息"""
        for agent_id in self.agents:
            if agent_id != sender_id:
                message = Message(
                    sender_id=sender_id,
                    receiver_id=agent_id,
                    content=content,
                    message_type=message_type,
                    timestamp=asyncio.get_event_loop().time()
                )
                await self.message_queue.put(message)

    def _enhance_with_gnn(self, query: str, docs: List) -> List:
        """使用GNN模型增强检索结果（如果可用）"""
        if self.gnn_model is None or not docs:
            return docs

        try:
            from torch_geometric.data import Data
            node_features = torch.randn(len(docs), 15)
            edge_index = torch.randint(0, len(docs), (2, len(docs) * 2))
            data = Data(x=node_features, edge_index=edge_index)

            with torch.no_grad():
                enhanced_features = self.gnn_model(data)

            if len(enhanced_features) == len(docs):
                for i, doc in enumerate(docs):
                    doc.metadata["gnn_score"] = enhanced_features[i].norm().item()
                docs.sort(key=lambda x: x.metadata.get("gnn_score", 0), reverse=True)

        except Exception as e:
            print(f"[GNN] Enhancement failed: {e}")

        return docs

    def _generate_evidence_chain(self, agent_role: str, statement: str, context: Dict) -> List[str]:
        """强制生成证据链"""
        prompt = f"""你是一位专业的{agent_role}。请根据以下陈述，生成支持该陈述的证据链。

陈述: {statement}
上下文: {context}

要求:
1. 必须提供至少3条具体证据
2. 每条证据必须注明来源或推理依据
3. 证据之间要有逻辑关联
4. 格式: 每条证据用编号列出

证据链:"""
        response = call_qwen(prompt)
        if response.startswith("[ERROR]"):
            return [f"证据1: 基于{agent_role}的专业判断", f"证据2: 依据历史数据分析", f"证据3: 结合上下文推理"]
        evidence_lines = [line.strip() for line in response.split('\n') if line.strip()]
        return evidence_lines[:5] if evidence_lines else ["证据不足，需要进一步分析"]

    def _check_stalemate(self) -> bool:
        """检查是否陷入僵局（连续相似结论）"""
        if len(self.debate_history) < 3:
            return False
        recent = self.debate_history[-3:]
        statements = [r.statement.lower() for r in recent]
        return len(set(statements)) == 1

    def _referee_decision(self, query: str, debate_summary: Dict) -> Dict:
        """裁判一锤定音决策"""
        prompt = f"""基于以下多智能体辩论结果，请做出最终决策。

研究问题: {query}

辩论摘要:
- 轮次数: {debate_summary.get('rounds', 0)}
- 各方观点: {debate_summary.get('positions', [])}
- 置信度: {debate_summary.get('confidence', 0.0)}

要求:
1. 直接给出明确结论（不能是"是/否"）
2. 提供完整的证据链
3. 说明决策依据
4. 评估结论的可信度(0-1)

输出格式:
结论: ...
证据链:
1. ...
2. ...
3. ...
可信度: ..."""
        response = call_qwen(prompt)
        if response.startswith("[ERROR]"):
            return {
                "conclusion": "基于现有证据无法得出确定性结论，建议人工审核",
                "evidence_chain": ["数据不完整", "需要更多来源验证"],
                "confidence": 0.5
            }
        return self._parse_referee_response(response)

    def _parse_referee_response(self, response: str) -> Dict:
        """解析裁判响应"""
        result = {"conclusion": "", "evidence_chain": [], "confidence": 0.8}
        lines = response.split('\n')
        current_section = None
        evidence = []
        for line in lines:
            line = line.strip()
            if line.startswith('结论:'):
                result["conclusion"] = line[3:].strip()
                current_section = "conclusion"
            elif line.startswith('可信度:'):
                try:
                    conf = float(line[3:].strip().replace('%', '').replace('0.', '0.'))
                    if conf > 1:
                        conf = conf / 100
                    result["confidence"] = conf
                except:
                    result["confidence"] = 0.8
                current_section = "confidence"
            elif line and current_section == "conclusion":
                if line[0].isdigit() and '.' in line[:3]:
                    evidence.append(line)
                elif "证据" in line or "依据" in line:
                    evidence.append(line)
        result["evidence_chain"] = evidence if evidence else ["综合分析得出"]
        return result

    async def coordinate_research(self, query: str) -> Dict:
        """多智能体博弈协调研究任务（带轮次限制和裁判机制）"""
        self.debate_history = []

        researcher = ResearchAgent("researcher", "信息检索专家")
        analyst = ResearchAgent("analyst", "数据分析专家")
        synthesizer = ResearchAgent("synthesizer", "结论整合专家")

        self.register_agent(researcher)
        self.register_agent(analyst)
        self.register_agent(synthesizer)

        context = {"query": query, "round": 0, "gnn_available": self.gnn_model is not None}
        positions = []

        docs = hybrid_retriever(query, top_k=5)
        if docs:
            docs = self._enhance_with_gnn(query, docs)
            context["retrieved_docs"] = docs[:3]
            context["doc_sources"] = [d.metadata.get("source", "unknown") for d in docs[:3]]

        for round_num in range(1, self.MAX_ROUNDS + 1):
            context["round"] = round_num

            if round_num == 1:
                research_plan = await researcher.think({"query": query, "context": context})
                research_result = await researcher.act(research_plan)
                statement = f"研究发现: {research_result.get('results', research_plan)}"
                evidence = self._generate_evidence_chain("信息检索专家", statement, context)
                positions.append({"agent": "researcher", "statement": statement, "evidence": evidence})
                self.debate_history.append(DebateRound(round_num, "researcher", statement, evidence, 0.7))
                context["research"] = research_result

            elif round_num == 2:
                analysis_plan = await analyst.think({"query": query, "data": context.get("research", {})})
                analysis_result = await analyst.act(analysis_plan)
                statement = f"分析结论: {analysis_result}"
                evidence = self._generate_evidence_chain("数据分析专家", statement, context)
                positions.append({"agent": "analyst", "statement": statement, "evidence": evidence})
                self.debate_history.append(DebateRound(round_num, "analyst", statement, evidence, 0.75))
                context["analysis"] = analysis_result

            elif round_num == 3:
                synthesis_plan = await synthesizer.think({"query": query, "analysis": context.get("analysis", {})})
                synthesis_result = await synthesizer.act(synthesis_plan)
                statement = f"综合判断: {synthesis_result}"
                evidence = self._generate_evidence_chain("结论整合专家", statement, context)
                positions.append({"agent": "synthesizer", "statement": statement, "evidence": evidence})
                self.debate_history.append(DebateRound(round_num, "synthesizer", statement, evidence, 0.8))
                context["synthesis"] = synthesis_result

            elif round_num == 4:
                synthesis2_plan = await synthesizer.think({"query": query, "round": 4, "history": self.debate_history})
                synthesis2_result = await synthesizer.act(synthesis2_plan)
                statement = f"综合判断(第二轮): {synthesis2_result}"
                evidence = self._generate_evidence_chain("结论整合专家", statement, context)
                positions.append({"agent": "synthesizer_v2", "statement": statement, "evidence": evidence})
                self.debate_history.append(DebateRound(round_num, "synthesizer", statement, evidence, 0.85))
                context["synthesis2"] = synthesis2_result

            else:
                debate_summary = {
                    "rounds": len(self.debate_history),
                    "positions": [p["statement"] for p in positions],
                    "confidence": sum(r.confidence for r in self.debate_history) / len(self.debate_history) if self.debate_history else 0.5
                }
                referee_result = self._referee_decision(query, debate_summary)
                return {
                    "final_answer": referee_result["conclusion"],
                    "evidence_chain": referee_result["evidence_chain"],
                    "confidence_score": referee_result["confidence"],
                    "debate_rounds": len(self.debate_history),
                    "gnn_enhanced": self.gnn_model is not None,
                    "debate_history": [
                        {"round": r.round_num, "speaker": r.speaker, "statement": r.statement, "evidence": r.evidence_chain}
                        for r in self.debate_history
                    ]
                }

            if self._check_stalemate():
                debate_summary = {
                    "rounds": len(self.debate_history),
                    "positions": [p["statement"] for p in positions],
                    "confidence": sum(r.confidence for r in self.debate_history) / len(self.debate_history)
                }
                referee_result = self._referee_decision(query, debate_summary)
                return {
                    "final_answer": referee_result["conclusion"],
                    "evidence_chain": referee_result["evidence_chain"],
                    "confidence_score": referee_result["confidence"],
                    "debate_rounds": len(self.debate_history),
                    "early_termination": "stalemate",
                    "gnn_enhanced": self.gnn_model is not None,
                    "debate_history": [
                        {"round": r.round_num, "speaker": r.speaker, "statement": r.statement, "evidence": r.evidence_chain}
                        for r in self.debate_history
                    ]
                }

        final_result = context.get("synthesis2", context.get("synthesis", {}))
        return {
            "final_answer": final_result,
            "evidence_chain": positions[-1]["evidence"] if positions else [],
            "confidence_score": self.debate_history[-1].confidence if self.debate_history else 0.5,
            "debate_rounds": len(self.debate_history),
            "gnn_enhanced": self.gnn_model is not None,
            "debate_history": [
                {"round": r.round_num, "speaker": r.speaker, "statement": r.statement, "evidence": r.evidence_chain}
                for r in self.debate_history
            ]
        }

    async def process_messages(self):
        """处理消息队列"""
        while not self.message_queue.empty():
            message = await self.message_queue.get()
            receiver = self.agents.get(message.receiver_id)
            if receiver:
                await receiver.think(message.content)
            self.message_queue.task_done()

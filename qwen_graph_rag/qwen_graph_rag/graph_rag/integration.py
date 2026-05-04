from typing import Dict
from multi_agent.coordination import DebateCoordinator


class GraphRAGIntegration:
    def __init__(self, coordinator: DebateCoordinator):
        self.coordinator = coordinator
        self.rag_service = None

    def _get_rag_service(self):
        if self.rag_service is None:
            try:
                from services.rag_service import RAGService
                self.rag_service = RAGService()
            except Exception:
                pass
        return self.rag_service

    async def enhanced_search(self, query: str) -> Dict:
        """增强型搜索，结合多智能体协作"""
        result = await self.coordinator.coordinate_research(query)
        graph_result = await self._get_graph_rag_result(query)
        return {
            "final_answer": result,
            "supporting_evidence": graph_result,
            "confidence_score": self._calculate_confidence(result, graph_result)
        }

    async def _get_graph_rag_result(self, query: str) -> Dict:
        """获取GraphRAG 结果"""
        rag = self._get_rag_service()
        if rag is None:
            return {"content": "RAG service not available", "source": "fallback"}

        try:
            docs = rag.retrieve(query, top_k=3)
            if docs:
                content = "\n".join([doc.page_content for doc in docs])
                sources = [doc.metadata.get("source", "unknown") for doc in docs]
                return {
                    "content": content[:1000],
                    "sources": sources,
                    "num_results": len(docs)
                }
        except Exception as e:
            return {"content": f"Error: {str(e)}", "source": "error"}

        return {"content": "No relevant documents found", "source": "empty"}

    def _calculate_confidence(self, result: Dict, evidence: Dict) -> float:
        """计算置信度"""
        base_confidence = 0.85
        if evidence.get("num_results", 0) > 0:
            base_confidence += 0.1
        return min(base_confidence, 0.98)

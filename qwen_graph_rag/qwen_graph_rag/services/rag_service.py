import re
import os
import logging
import time
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / ".chroma_db"
CLEANED_DIR = ROOT_DIR / "data" / "docs_cleaned"
CACHE_DIR = os.path.join(ROOT_DIR, ".cache")
EMBEDDING_MODEL_DIR = ROOT_DIR / "embedding_model"
os.makedirs(CACHE_DIR, exist_ok=True)

embedding_func = None


def init_embedding_model():
    """初始化嵌入模型"""
    global embedding_func
    embedding_func = None
    try:
        model_path = os.environ.get("EMBEDDING_MODEL_PATH", str(EMBEDDING_MODEL_DIR))
        if not os.path.exists(model_path):
            logging.warning(f"模型路径不存在: {model_path}，使用虚拟嵌入模型")
            class DummyEmbedding:
                def embed_query(self, text): return [0.0] * 384
                def embed_documents(self, texts): return [[0.0] * 384 for _ in texts]
            embedding_func = DummyEmbedding()
        else:
            embedding_func = HuggingFaceEmbeddings(
                model_name=os.path.abspath(model_path),
                cache_folder=CACHE_DIR,
                model_kwargs={"device": "cpu"}
            )
            logging.info("嵌入模型加载成功")
    except Exception as e:
        logging.error(f"加载嵌入模型失败: {str(e)}")
        class DummyEmbedding:
            def embed_query(self, text): return [0.0] * 384
            def embed_documents(self, texts): return [[0.0] * 384 for _ in texts]
        embedding_func = DummyEmbedding()
    return embedding_func


def load_cleaned_chunks() -> List[Document]:
    docs = []
    if not CLEANED_DIR.exists():
        logging.warning(f"目录不存在: {CLEANED_DIR}")
        return docs
    for chunk_file in CLEANED_DIR.glob("*_chunks.txt"):
        try:
            with open(chunk_file, "r", encoding="utf-8") as f:
                content = f.read()
            segments = re.split(r'\[片段\d+\]\n', content)
            for seg in segments[1:]:
                seg = seg.strip()
                if len(seg) > 20:
                    source_doc = chunk_file.stem.replace("_chunks", "")
                    docs.append(Document(
                        page_content=seg,
                        metadata={"source": f"杨泽彤-{source_doc}", "chunk_id": f"{source_doc}-{len(docs)+1}"}
                    ))
        except Exception as e:
            logging.error(f"读取文件失败: {str(e)}")
    logging.info(f"加载 {len(docs)} 个知识片段")
    return docs


vectorstore_cache = None


def build_rag_store():
    """构建RAG向量库"""
    logging.info("正在构建RAG知识库...")
    documents = load_cleaned_chunks()
    embedding = init_embedding_model()
    try:
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embedding,
            persist_directory=str(DB_PATH),
            collection_name="chem_knowledge_rag"
        )
        logging.info("RAG知识库构建完成")
        return vectorstore
    except Exception as e:
        logging.error(f"构建RAG知识库失败: {str(e)}")
        return None


def get_vectorstore():
    """获取向量库实例"""
    global vectorstore_cache
    if vectorstore_cache is None:
        embedding = init_embedding_model()
        try:
            vectorstore_cache = Chroma(
                persist_directory=str(DB_PATH),
                embedding_function=embedding,
                collection_name="chem_knowledge_rag"
            )
        except Exception:
            vectorstore_cache = build_rag_store()
    return vectorstore_cache


def generate_hypothetical_answer(query: str) -> str:
    """生成假设性答案（HyDE技术）"""
    from config.llm_config import call_qwen
    try:
        prompt = f"你是一位化工领域专家，基于以下问题生成一个详细的假设性答案：\n{query}"
        result = call_qwen(prompt)
        if result.startswith("[ERROR]"):
            return query
        return result
    except Exception:
        return query


def hyde_retriever(query: str, top_k: int = 3) -> List[Document]:
    """使用HyDE技术进行检索"""
    vectorstore = get_vectorstore()
    if vectorstore is None:
        return []
    hypothetical_answer = generate_hypothetical_answer(query)
    results = vectorstore.similarity_search(hypothetical_answer, k=top_k)
    return results


def hybrid_retriever(query: str, top_k: int = 3) -> List[Document]:
    """混合检索模式"""
    high_frequency_keywords = ["temperature", "pressure", "flow", "level", "valve", "pump"]
    fuzzy_keywords = ["instability", "fluctuation", "variation", "leakage", "corrosion", "abnormal"]

    vectorstore = get_vectorstore()
    if vectorstore is None:
        return []

    query_lower = query.lower()
    if any(kw in query_lower for kw in high_frequency_keywords):
        return vectorstore.similarity_search(query, k=top_k)
    elif any(kw in query_lower for kw in fuzzy_keywords):
        return hyde_retriever(query, top_k)
    else:
        return vectorstore.similarity_search(query, k=top_k)


class RAGService:
    def __init__(self):
        self.vectorstore = get_vectorstore()

    def retrieve(self, query: str, top_k: int = 3) -> List[Document]:
        """检索相关文档"""
        return hybrid_retriever(query, top_k)

    def add_documents(self, documents: List[Document]):
        """添加文档到向量库"""
        if self.vectorstore:
            self.vectorstore.add_documents(documents)

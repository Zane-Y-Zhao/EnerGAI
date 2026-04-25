import sys
import os

# 测试基本功能
def test_simple():
    print("测试基本功能...")
    
    try:
        # 测试 rank_bm25 库的导入
        print("1. 测试 rank_bm25 库的导入...")
        from rank_bm25 import BM25Okapi
        print("[OK] 成功导入 rank_bm25 库")
        
        # 测试创建 BM25 索引
        print("\n2. 测试创建 BM25 索引...")
        test_docs = [
            "温度升高时，应检查冷却系统是否正常工作",
            "压力下降可能是由于管道泄漏导致的",
            "流量不稳定时，应检查泵的运行状态"
        ]
        import re
        tokenized_docs = [re.sub(r'[^\w\s]', '', doc.lower()).split() for doc in test_docs]
        bm25 = BM25Okapi(tokenized_docs)
        print("[OK] BM25 索引创建成功")
        
        # 测试检索
        print("\n3. 测试检索...")
        query = "温度升高"
        tokenized_query = re.sub(r'[^\w\s]', '', query.lower()).split()
        scores = bm25.get_scores(tokenized_query)
        print(f"[OK] 检索成功，得分：{scores}")
        
        print("\n测试完成！")
    except Exception as e:
        print(f"[ERROR] 测试失败：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()

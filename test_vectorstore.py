import sys
import os
import logging

# 设置根目录并添加到sys.path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 导入 get_vectorstore 函数
from knowledge_base.rag_pipeline import get_vectorstore, build_rag_store

# 测试向量存储的初始化
def test_vectorstore():
    print("测试向量存储初始化...")
    try:
        print("1. 尝试获取向量存储...")
        vectorstore = get_vectorstore()
        if vectorstore is not None:
            print("✅ 向量存储初始化成功！")
            # 尝试获取文档
            print("2. 尝试获取文档...")
            documents = vectorstore.get()
            print(f"3. 文档类型：{type(documents)}")
            print(f"4. 文档键：{list(documents.keys()) if isinstance(documents, dict) else '不是字典'}")
            if isinstance(documents, dict) and 'documents' in documents:
                print(f"5. 文档数量：{len(documents['documents'])}")
                if len(documents['documents']) > 0:
                    print(f"✅ 成功获取 {len(documents['documents'])} 个文档")
                    print(f"6. 第一个文档内容：{documents['documents'][0][:100]}...")
                else:
                    print("❌ 文档列表为空")
            else:
                print("❌ 无法获取文档")
        else:
            print("❌ 向量存储初始化失败")
            # 尝试重新构建向量库
            print("7. 尝试重新构建向量库...")
            store = build_rag_store()
            if store is not None:
                print("✅ 向量库构建成功！")
                # 再次尝试获取文档
                documents = store.get()
                print(f"8. 文档类型：{type(documents)}")
                print(f"9. 文档键：{list(documents.keys()) if isinstance(documents, dict) else '不是字典'}")
                if isinstance(documents, dict) and 'documents' in documents:
                    print(f"10. 文档数量：{len(documents['documents'])}")
                    if len(documents['documents']) > 0:
                        print(f"✅ 成功获取 {len(documents['documents'])} 个文档")
                    else:
                        print("❌ 文档列表为空")
                else:
                    print("❌ 无法获取文档")
            else:
                print("❌ 向量库构建失败")
    except Exception as e:
        print(f"❌ 测试失败：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vectorstore()

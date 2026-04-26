# knowledge_base/llm_config.py
import os
import time
from dotenv import load_dotenv
from dashscope import Generation

MODEL_NAME = "qwen-max"  # 生产环境使用max版保障复杂推理能力

def call_qwen(prompt: str) -> str:
    """封装千问调用，内置超时与错误重试"""
    print(f"[DEBUG] 开始调用大模型，prompt: {prompt[:50]}...")
    start_time = time.time()
    try:
        # 从.env文件直接读取API_KEY
        from pathlib import Path
        env_path = Path(__file__).parent.parent / ".env"
        API_KEY = None
        
        print(f"[DEBUG] 尝试读取.env文件：{env_path}")
        print(f"[DEBUG] .env文件是否存在：{env_path.exists()}")
        
        if env_path.exists():
            print(f"[DEBUG] 打开.env文件")
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"[DEBUG] .env文件行数：{len(lines)}")
                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    print(f"[DEBUG] 第{i}行：{line}")
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        print(f"[DEBUG] 解析：key={key.strip()}, value={value.strip()}")
                        if key.strip() == "DASHSCOPE_API_KEY":
                            API_KEY = value.strip()
                            print(f"[DEBUG] 找到API_KEY：{API_KEY[:10]}...")
                            break
        
        print(f"[DEBUG] 最终API_KEY：{API_KEY}")
        
        if not API_KEY:
            raise Exception("API_KEY not found in .env file")
            
        print(f"[DEBUG] API_KEY: {API_KEY[:10]}...")
        print(f"[DEBUG] MODEL_NAME: {MODEL_NAME}")
        
        response = Generation.call(
            model=MODEL_NAME,
            prompt=prompt,
            api_key=API_KEY,
            temperature=0.5,  # 平衡保守性和灵活性
            max_tokens=2048,  # 增加最大token数，支持更复杂的回答
            top_p=0.9,  # 控制生成的多样性
            timeout=15  # 增加超时时间，确保复杂问题有足够时间处理
        )
        end_time = time.time()
        print(f"[DEBUG] 大模型调用完成，耗时：{end_time - start_time:.2f}s")
        print(f"[DEBUG] 响应状态码：{response.status_code}")
        
        if response.status_code == 200:
            result = response.output.text.strip()
            print(f"[DEBUG] 响应内容：{result[:100]}...")
            return result
        else:
            error_message = f"Qwen API Error: {response.message}"
            print(f"[DEBUG] {error_message}")
            raise Exception(error_message)
    except Exception as e:
        end_time = time.time()
        print(f"[DEBUG] 大模型调用失败，耗时：{end_time - start_time:.2f}s")
        print(f"[DEBUG] 错误：{str(e)}")
        return f"[ERROR] 大模型调用失败：{str(e)}"


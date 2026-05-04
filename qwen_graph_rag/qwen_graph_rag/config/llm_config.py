import os
import time
from dotenv import load_dotenv
from dashscope import Generation

MODEL_NAME = "qwen-max"


def call_qwen(prompt: str) -> str:
    """封装千问调用，内置超时与错误重试"""
    print(f"[DEBUG] 开始调用大模型，prompt: {prompt[:50]}...")
    start_time = time.time()
    try:
        from pathlib import Path
        env_path = Path(__file__).parent.parent.parent / ".env"
        API_KEY = None

        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if key.strip() == "DASHSCOPE_API_KEY":
                            API_KEY = value.strip()
                            break

        if not API_KEY:
            raise Exception("API_KEY not found in .env file")

        response = Generation.call(
            model=MODEL_NAME,
            prompt=prompt,
            api_key=API_KEY,
            temperature=0.5,
            max_tokens=2048,
            top_p=0.9,
            timeout=15
        )
        end_time = time.time()
        print(f"[DEBUG] 大模型调用完成，耗时：{end_time - start_time:.2f}s")

        if response.status_code == 200:
            return response.output.text.strip()
        else:
            raise Exception(f"Qwen API Error: {response.message}")
    except Exception as e:
        end_time = time.time()
        print(f"[DEBUG] 大模型调用失败，耗时：{end_time - start_time:.2f}s")
        print(f"[DEBUG] 错误：{str(e)}")
        return f"[ERROR] 大模型调用失败：{str(e)}"

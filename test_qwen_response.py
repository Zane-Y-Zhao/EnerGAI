#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试千问模型的响应速度和稳定性
"""

import time
import sys
from pathlib import Path

# 设置根目录并添加到sys.path
ROOT_DIR = Path(__file__).parent
sys.path.append(str(ROOT_DIR))

from knowledge_base.llm_config import call_qwen

def test_qwen_response_speed():
    """测试千问模型的响应速度"""
    print("开始测试千问模型响应速度...")
    print("=" * 60)
    
    # 测试用例
    test_cases = [
        "什么是化工过程中的余热回收？",
        "阀门FV-101的操作规则是什么？",
        "当温度超过90°C时应该采取什么措施？",
        "化工安全操作规程的主要内容有哪些？",
        "余热回收系统的效率如何计算？"
    ]
    
    total_time = 0
    success_count = 0
    error_count = 0
    
    for i, query in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {query}")
        print("-" * 40)
        
        start_time = time.time()
        response = call_qwen(query)
        end_time = time.time()
        
        response_time = end_time - start_time
        total_time += response_time
        
        print(f"响应时间: {response_time:.2f}秒")
        print(f"响应内容: {response[:100]}...")
        
        if "[ERROR]" in response:
            print("状态: 失败")
            error_count += 1
        else:
            print("状态: 成功")
            success_count += 1
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print(f"总测试数: {len(test_cases)}")
    print(f"成功数: {success_count}")
    print(f"失败数: {error_count}")
    print(f"平均响应时间: {total_time / len(test_cases):.2f}秒")
    print(f"总耗时: {total_time:.2f}秒")
    
    # 检查是否存在无限循环问题
    print("\n检查无限循环问题...")
    # 测试一个简单的查询，确保不会无限循环
    simple_query = "你好"
    start_time = time.time()
    response = call_qwen(simple_query)
    end_time = time.time()
    
    if end_time - start_time < 30:  # 如果响应时间小于30秒，认为没有无限循环
        print("未检测到无限循环问题")
    else:
        print("可能存在无限循环问题，响应时间过长")

if __name__ == "__main__":
    test_qwen_response_speed()

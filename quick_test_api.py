#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试QQ回复消息API的脚本
"""

import requests
import json

def test_api(api_key, cookie_id="test", chat_id="test", to_user_id="test", message="test"):
    """测试API调用"""
    url = "http://localhost:8000/send-message"
    
    data = {
        "api_key": api_key,
        "cookie_id": cookie_id,
        "chat_id": chat_id,
        "to_user_id": to_user_id,
        "message": message
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        
        print(f"秘钥: {api_key}")
        print(f"状态: {response.status_code}")
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        print("-" * 50)
        
        return result.get("success", False)
        
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def main():
    print("🚀 快速API测试")
    print("=" * 50)
    
    # 测试用例
    test_cases = [
        ("默认秘钥", "xianyu_qq_reply_2024"),
        ("测试秘钥", "zhinina_test_key"),
        ("错误秘钥", "wrong_key"),
        ("空秘钥", ""),
    ]
    
    for name, key in test_cases:
        print(f"\n📋 测试: {name}")
        test_api(key)
    
    # 测试参数验证
    print("\n📋 测试参数验证:")
    
    # 测试空参数
    param_tests = [
        ("空cookie_id", {"cookie_id": ""}),
        ("空chat_id", {"chat_id": ""}),
        ("空to_user_id", {"to_user_id": ""}),
        ("空message", {"message": ""}),
    ]
    
    for name, params in param_tests:
        print(f"\n测试: {name}")
        default_params = {
            "cookie_id": "test",
            "chat_id": "test", 
            "to_user_id": "test",
            "message": "test"
        }
        default_params.update(params)
        test_api("xianyu_qq_reply_2024", **default_params)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
测试页面访问
"""

import requests
import time

BASE_URL = "http://localhost:8080"

def test_page_access():
    """测试页面访问"""
    print("🚀 测试管理员页面访问")
    print("=" * 50)
    
    pages = [
        ("主页", "/"),
        ("登录页", "/login.html"),
        ("注册页", "/register.html"),
        ("管理页", "/admin"),
        ("用户管理", "/user_management.html"),
        ("日志管理", "/log_management.html")
    ]
    
    for page_name, page_url in pages:
        try:
            print(f"测试 {page_name} ({page_url})...", end=" ")
            response = requests.get(f"{BASE_URL}{page_url}", timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {response.status_code}")
            else:
                print(f"❌ {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ 连接失败")
        except requests.exceptions.Timeout:
            print("❌ 超时")
        except Exception as e:
            print(f"❌ 错误: {e}")
    
    print("\n" + "=" * 50)
    print("测试完成！")

if __name__ == "__main__":
    test_page_access()

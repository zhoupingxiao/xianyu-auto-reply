#!/usr/bin/env python3
"""
简单的日志测试
"""

import requests
import time

BASE_URL = "http://localhost:8080"

def test_admin_login():
    """测试管理员登录的日志显示"""
    print("🔧 测试管理员登录...")
    
    # 管理员登录
    response = requests.post(f"{BASE_URL}/login", 
                           json={'username': 'admin', 'password': 'admin123'})
    
    if response.json()['success']:
        token = response.json()['token']
        headers = {'Authorization': f'Bearer {token}'}
        
        print("✅ 管理员登录成功")
        
        # 测试一些API调用
        print("📋 测试API调用...")
        
        # 1. 获取Cookie列表
        response = requests.get(f"{BASE_URL}/cookies", headers=headers)
        print(f"   Cookie列表: {response.status_code}")
        
        # 2. 获取Cookie详情
        response = requests.get(f"{BASE_URL}/cookies/details", headers=headers)
        print(f"   Cookie详情: {response.status_code}")
        
        # 3. 获取卡券列表
        response = requests.get(f"{BASE_URL}/cards", headers=headers)
        print(f"   卡券列表: {response.status_code}")
        
        # 4. 获取用户设置
        response = requests.get(f"{BASE_URL}/user-settings", headers=headers)
        print(f"   用户设置: {response.status_code}")
        
        print("✅ API调用测试完成")
        return True
    else:
        print("❌ 管理员登录失败")
        return False

def main():
    """主函数"""
    print("🚀 简单日志测试")
    print("=" * 40)
    
    print("📋 测试内容:")
    print("• 管理员登录日志")
    print("• API请求/响应日志")
    print("• 用户信息显示")
    
    print("\n🔍 请观察服务器日志输出...")
    print("应该看到类似以下格式的日志:")
    print("🌐 【admin#1】 API请求: GET /cookies")
    print("✅ 【admin#1】 API响应: GET /cookies - 200 (0.005s)")
    
    print("\n" + "-" * 40)
    
    # 执行测试
    success = test_admin_login()
    
    print("-" * 40)
    
    if success:
        print("🎉 测试完成！请检查服务器日志中的用户信息显示。")
        print("\n💡 检查要点:")
        print("1. 登录日志应显示: 【admin】尝试登录")
        print("2. API请求日志应显示: 【admin#1】")
        print("3. API响应日志应显示: 【admin#1】")
    else:
        print("❌ 测试失败")
    
    return success

if __name__ == "__main__":
    main()

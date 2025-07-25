#!/usr/bin/env python3
"""
测试token修复
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_admin_api_access():
    """测试管理员API访问"""
    print("🚀 测试管理员API访问")
    print("=" * 50)
    
    # 1. 管理员登录
    print("1. 管理员登录...")
    login_response = requests.post(f"{BASE_URL}/login", 
                                 json={'username': 'admin', 'password': 'admin123'})
    
    if not login_response.json()['success']:
        print("❌ 管理员登录失败")
        return False
    
    token = login_response.json()['token']
    headers = {'Authorization': f'Bearer {token}'}
    print(f"✅ 管理员登录成功，token: {token[:20]}...")
    
    # 2. 测试管理员API
    apis = [
        ("获取用户列表", "GET", "/admin/users"),
        ("获取系统统计", "GET", "/admin/stats"),
        ("获取系统日志", "GET", "/admin/logs?lines=10")
    ]
    
    for api_name, method, endpoint in apis:
        print(f"2. 测试 {api_name}...")
        
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        else:
            response = requests.post(f"{BASE_URL}{endpoint}", headers=headers)
        
        if response.status_code == 200:
            print(f"   ✅ {api_name} 成功 (200)")
            
            # 显示部分数据
            try:
                data = response.json()
                if endpoint == "/admin/users":
                    users = data.get('users', [])
                    print(f"      用户数量: {len(users)}")
                elif endpoint == "/admin/stats":
                    print(f"      总用户数: {data.get('users', {}).get('total', 0)}")
                    print(f"      总Cookie数: {data.get('cookies', {}).get('total', 0)}")
                elif endpoint.startswith("/admin/logs"):
                    logs = data.get('logs', [])
                    print(f"      日志条数: {len(logs)}")
            except:
                pass
                
        elif response.status_code == 401:
            print(f"   ❌ {api_name} 失败 - 401 未授权")
            return False
        elif response.status_code == 403:
            print(f"   ❌ {api_name} 失败 - 403 权限不足")
            return False
        else:
            print(f"   ❌ {api_name} 失败 - {response.status_code}")
            return False
    
    print("\n✅ 所有管理员API测试通过！")
    return True

def test_non_admin_access():
    """测试非管理员访问"""
    print("\n🔒 测试非管理员访问限制")
    print("=" * 50)
    
    # 使用无效token测试
    fake_headers = {'Authorization': 'Bearer invalid_token'}
    
    response = requests.get(f"{BASE_URL}/admin/users", headers=fake_headers)
    if response.status_code == 401:
        print("✅ 无效token被正确拒绝 (401)")
    else:
        print(f"❌ 无效token未被拒绝 ({response.status_code})")
        return False
    
    # 测试无token访问
    response = requests.get(f"{BASE_URL}/admin/users")
    if response.status_code == 401:
        print("✅ 无token访问被正确拒绝 (401)")
    else:
        print(f"❌ 无token访问未被拒绝 ({response.status_code})")
        return False
    
    return True

def main():
    """主测试函数"""
    print("🔧 Token修复验证测试")
    print("=" * 60)
    
    print("📋 测试目标:")
    print("• 验证管理员可以正常访问API")
    print("• 验证token认证正常工作")
    print("• 验证非管理员访问被拒绝")
    
    try:
        # 测试管理员API访问
        admin_success = test_admin_api_access()
        
        # 测试非管理员访问限制
        security_success = test_non_admin_access()
        
        print("\n" + "=" * 60)
        
        if admin_success and security_success:
            print("🎉 Token修复验证成功！")
            
            print("\n💡 现在可以正常使用:")
            print("1. 使用admin账号登录主页")
            print("2. 点击侧边栏的'用户管理'")
            print("3. 点击侧边栏的'系统日志'")
            print("4. 所有管理员功能都应该正常工作")
            
            print("\n🔑 Token存储统一:")
            print("• 登录页面: 设置 'auth_token'")
            print("• 主页面: 读取 'auth_token'")
            print("• 管理员页面: 读取 'auth_token'")
            print("• 所有页面现在使用统一的token key")
            
            return True
        else:
            print("❌ Token修复验证失败！")
            return False
            
    except Exception as e:
        print(f"💥 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()

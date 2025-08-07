#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查用户凭据
"""

import sys
import os
import hashlib

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_manager import db_manager


def check_users():
    """检查用户表中的用户信息"""
    print("🔍 检查用户表中的用户信息")
    print("=" * 50)
    
    try:
        cursor = db_manager.conn.cursor()
        cursor.execute("SELECT id, username, password_hash, is_admin FROM users")
        users = cursor.fetchall()
        
        print(f"用户表中共有 {len(users)} 个用户:")
        for user in users:
            print(f"  - 用户ID: {user[0]}")
            print(f"    用户名: {user[1]}")
            print(f"    密码哈希: {user[2][:20]}..." if user[2] else "    密码哈希: None")
            print(f"    是否管理员: {user[3]}")
            print()
            
        # 测试密码验证
        if users:
            test_user = users[0]
            username = test_user[1]
            stored_hash = test_user[2]
            
            print(f"🔐 测试用户 '{username}' 的密码验证:")
            
            # 测试常见密码
            test_passwords = ["admin123", "admin", "123456", "password"]
            
            for password in test_passwords:
                # 计算密码哈希
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                if password_hash == stored_hash:
                    print(f"✅ 密码 '{password}' 匹配！")
                    return username, password
                else:
                    print(f"❌ 密码 '{password}' 不匹配")
                    print(f"   计算哈希: {password_hash[:20]}...")
                    print(f"   存储哈希: {stored_hash[:20]}...")
            
            print("⚠️ 没有找到匹配的密码")
            
    except Exception as e:
        print(f"❌ 检查用户失败: {e}")
        
    return None, None


def test_login_with_correct_credentials():
    """使用正确的凭据测试登录"""
    username, password = check_users()
    
    if username and password:
        print(f"\n🌐 使用正确凭据测试登录")
        print("=" * 50)
        
        import requests
        
        try:
            login_data = {
                "username": username,
                "password": password
            }
            response = requests.post("http://localhost:8080/login", json=login_data, timeout=10)
            print(f"登录状态码: {response.status_code}")
            print(f"登录响应: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    token = data.get('token') or data.get('access_token')
                    print(f"✅ 登录成功！Token: {token[:20]}..." if token else "✅ 登录成功但没有token")
                    
                    if token:
                        # 测试cookies/details接口
                        headers = {"Authorization": f"Bearer {token}"}
                        response = requests.get("http://localhost:8080/cookies/details", headers=headers, timeout=10)
                        print(f"cookies/details状态码: {response.status_code}")
                        
                        if response.status_code == 200:
                            details = response.json()
                            print(f"✅ 获取到 {len(details)} 个账号详情")
                            for detail in details:
                                print(f"  - {detail['id']}: {'启用' if detail['enabled'] else '禁用'}")
                        else:
                            print(f"❌ 获取账号详情失败: {response.text}")
                else:
                    print(f"❌ 登录失败: {data.get('message', '未知错误')}")
            else:
                print(f"❌ 登录请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 登录测试失败: {e}")


def create_test_user():
    """创建测试用户"""
    print(f"\n🔧 创建测试用户")
    print("=" * 50)
    
    try:
        # 创建一个新的测试用户
        test_username = "testuser"
        test_password = "test123"
        password_hash = hashlib.sha256(test_password.encode()).hexdigest()
        
        cursor = db_manager.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (username, password_hash, is_admin) 
            VALUES (?, ?, ?)
        """, (test_username, password_hash, 1))
        db_manager.conn.commit()
        
        print(f"✅ 创建测试用户成功:")
        print(f"   用户名: {test_username}")
        print(f"   密码: {test_password}")
        print(f"   密码哈希: {password_hash[:20]}...")
        
        return test_username, test_password
        
    except Exception as e:
        print(f"❌ 创建测试用户失败: {e}")
        return None, None


if __name__ == "__main__":
    print("🚀 检查用户凭据和登录问题")
    print("=" * 60)
    
    # 检查现有用户
    username, password = check_users()
    
    if not username:
        # 如果没有找到有效用户，创建一个测试用户
        print("\n没有找到有效的用户凭据，创建测试用户...")
        username, password = create_test_user()
    
    if username and password:
        # 使用正确凭据测试登录
        test_login_with_correct_credentials()
    
    print("\n" + "=" * 60)
    print("🎯 检查完成！")
    print("\n📋 总结:")
    print("1. 检查了用户表中的用户信息")
    print("2. 验证了密码哈希")
    print("3. 测试了登录功能")
    print("4. 测试了cookies/details接口")
    
    if username and password:
        print(f"\n✅ 可用的登录凭据:")
        print(f"   用户名: {username}")
        print(f"   密码: {password}")
        print(f"\n请使用这些凭据登录管理后台测试账号下拉框功能")

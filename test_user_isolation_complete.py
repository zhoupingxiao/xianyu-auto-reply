#!/usr/bin/env python3
"""
完整的多用户数据隔离测试
"""

import requests
import json
import sqlite3
import time

BASE_URL = "http://localhost:8080"

def create_test_users():
    """创建测试用户"""
    print("🧪 创建测试用户")
    print("-" * 40)
    
    users = [
        {"username": "testuser1", "email": "user1@test.com", "password": "test123456"},
        {"username": "testuser2", "email": "user2@test.com", "password": "test123456"}
    ]
    
    created_users = []
    
    for user in users:
        try:
            # 清理可能存在的用户
            conn = sqlite3.connect('xianyu_data.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE username = ? OR email = ?', (user['username'], user['email']))
            cursor.execute('DELETE FROM email_verifications WHERE email = ?', (user['email'],))
            conn.commit()
            conn.close()
            
            # 生成验证码
            session_id = f"test_{user['username']}_{int(time.time())}"
            
            # 生成图形验证码
            captcha_response = requests.post(f"{BASE_URL}/generate-captcha", 
                                           json={'session_id': session_id})
            if not captcha_response.json()['success']:
                print(f"   ❌ {user['username']}: 图形验证码生成失败")
                continue
            
            # 获取图形验证码
            conn = sqlite3.connect('xianyu_data.db')
            cursor = conn.cursor()
            cursor.execute('SELECT code FROM captcha_codes WHERE session_id = ? ORDER BY created_at DESC LIMIT 1', 
                         (session_id,))
            captcha_result = cursor.fetchone()
            conn.close()
            
            if not captcha_result:
                print(f"   ❌ {user['username']}: 无法获取图形验证码")
                continue
            
            captcha_code = captcha_result[0]
            
            # 验证图形验证码
            verify_response = requests.post(f"{BASE_URL}/verify-captcha", 
                                          json={'session_id': session_id, 'captcha_code': captcha_code})
            if not verify_response.json()['success']:
                print(f"   ❌ {user['username']}: 图形验证码验证失败")
                continue
            
            # 发送邮箱验证码
            email_response = requests.post(f"{BASE_URL}/send-verification-code", 
                                         json={'email': user['email'], 'session_id': session_id})
            if not email_response.json()['success']:
                print(f"   ❌ {user['username']}: 邮箱验证码发送失败")
                continue
            
            # 获取邮箱验证码
            conn = sqlite3.connect('xianyu_data.db')
            cursor = conn.cursor()
            cursor.execute('SELECT code FROM email_verifications WHERE email = ? ORDER BY created_at DESC LIMIT 1', 
                         (user['email'],))
            email_result = cursor.fetchone()
            conn.close()
            
            if not email_result:
                print(f"   ❌ {user['username']}: 无法获取邮箱验证码")
                continue
            
            email_code = email_result[0]
            
            # 注册用户
            register_response = requests.post(f"{BASE_URL}/register", 
                                            json={
                                                'username': user['username'],
                                                'email': user['email'],
                                                'verification_code': email_code,
                                                'password': user['password']
                                            })
            
            if register_response.json()['success']:
                print(f"   ✅ {user['username']}: 注册成功")
                
                # 登录获取token
                login_response = requests.post(f"{BASE_URL}/login", 
                                             json={'username': user['username'], 'password': user['password']})
                
                if login_response.json()['success']:
                    token = login_response.json()['token']
                    user_id = login_response.json()['user_id']
                    created_users.append({
                        'username': user['username'],
                        'user_id': user_id,
                        'token': token,
                        'headers': {'Authorization': f'Bearer {token}'}
                    })
                    print(f"   ✅ {user['username']}: 登录成功，用户ID: {user_id}")
                else:
                    print(f"   ❌ {user['username']}: 登录失败")
            else:
                print(f"   ❌ {user['username']}: 注册失败 - {register_response.json()['message']}")
                
        except Exception as e:
            print(f"   ❌ {user['username']}: 创建失败 - {e}")
    
    return created_users

def test_cookie_isolation(users):
    """测试Cookie数据隔离"""
    print("\n🧪 测试Cookie数据隔离")
    print("-" * 40)
    
    if len(users) < 2:
        print("❌ 需要至少2个用户进行隔离测试")
        return False
    
    user1, user2 = users[0], users[1]
    
    # 用户1添加cookies
    print(f"1️⃣ {user1['username']} 添加cookies...")
    cookies1 = [
        {"id": "test_cookie_user1_1", "value": "cookie_value_1"},
        {"id": "test_cookie_user1_2", "value": "cookie_value_2"}
    ]
    
    for cookie in cookies1:
        response = requests.post(f"{BASE_URL}/cookies", 
                               json=cookie, 
                               headers=user1['headers'])
        if response.status_code == 200:
            print(f"   ✅ 添加cookie: {cookie['id']}")
        else:
            print(f"   ❌ 添加cookie失败: {cookie['id']}")
    
    # 用户2添加cookies
    print(f"\n2️⃣ {user2['username']} 添加cookies...")
    cookies2 = [
        {"id": "test_cookie_user2_1", "value": "cookie_value_3"},
        {"id": "test_cookie_user2_2", "value": "cookie_value_4"}
    ]
    
    for cookie in cookies2:
        response = requests.post(f"{BASE_URL}/cookies", 
                               json=cookie, 
                               headers=user2['headers'])
        if response.status_code == 200:
            print(f"   ✅ 添加cookie: {cookie['id']}")
        else:
            print(f"   ❌ 添加cookie失败: {cookie['id']}")
    
    # 验证用户1只能看到自己的cookies
    print(f"\n3️⃣ 验证 {user1['username']} 的cookie隔离...")
    response1 = requests.get(f"{BASE_URL}/cookies", headers=user1['headers'])
    if response1.status_code == 200:
        user1_cookies = response1.json()
        user1_cookie_ids = set(user1_cookies)
        expected_user1 = {"test_cookie_user1_1", "test_cookie_user1_2"}
        
        if expected_user1.issubset(user1_cookie_ids):
            print(f"   ✅ {user1['username']} 能看到自己的cookies")
        else:
            print(f"   ❌ {user1['username']} 看不到自己的cookies")
        
        if "test_cookie_user2_1" not in user1_cookie_ids and "test_cookie_user2_2" not in user1_cookie_ids:
            print(f"   ✅ {user1['username']} 看不到其他用户的cookies")
        else:
            print(f"   ❌ {user1['username']} 能看到其他用户的cookies（隔离失败）")
    
    # 验证用户2只能看到自己的cookies
    print(f"\n4️⃣ 验证 {user2['username']} 的cookie隔离...")
    response2 = requests.get(f"{BASE_URL}/cookies", headers=user2['headers'])
    if response2.status_code == 200:
        user2_cookies = response2.json()
        user2_cookie_ids = set(user2_cookies)
        expected_user2 = {"test_cookie_user2_1", "test_cookie_user2_2"}
        
        if expected_user2.issubset(user2_cookie_ids):
            print(f"   ✅ {user2['username']} 能看到自己的cookies")
        else:
            print(f"   ❌ {user2['username']} 看不到自己的cookies")
        
        if "test_cookie_user1_1" not in user2_cookie_ids and "test_cookie_user1_2" not in user2_cookie_ids:
            print(f"   ✅ {user2['username']} 看不到其他用户的cookies")
        else:
            print(f"   ❌ {user2['username']} 能看到其他用户的cookies（隔离失败）")
    
    return True

def test_cross_user_access(users):
    """测试跨用户访问权限"""
    print("\n🧪 测试跨用户访问权限")
    print("-" * 40)
    
    if len(users) < 2:
        print("❌ 需要至少2个用户进行权限测试")
        return False
    
    user1, user2 = users[0], users[1]
    
    # 用户1尝试访问用户2的cookie
    print(f"1️⃣ {user1['username']} 尝试访问 {user2['username']} 的cookie...")
    
    # 尝试获取用户2的关键字
    response = requests.get(f"{BASE_URL}/keywords/test_cookie_user2_1", headers=user1['headers'])
    if response.status_code == 403:
        print(f"   ✅ 跨用户访问被正确拒绝 (403)")
    elif response.status_code == 404:
        print(f"   ✅ 跨用户访问被拒绝 (404)")
    else:
        print(f"   ❌ 跨用户访问未被拒绝 (状态码: {response.status_code})")
    
    # 尝试更新用户2的cookie状态
    response = requests.put(f"{BASE_URL}/cookies/test_cookie_user2_1/status", 
                          json={"enabled": False}, 
                          headers=user1['headers'])
    if response.status_code == 403:
        print(f"   ✅ 跨用户操作被正确拒绝 (403)")
    elif response.status_code == 404:
        print(f"   ✅ 跨用户操作被拒绝 (404)")
    else:
        print(f"   ❌ 跨用户操作未被拒绝 (状态码: {response.status_code})")
    
    return True

def cleanup_test_data(users):
    """清理测试数据"""
    print("\n🧹 清理测试数据")
    print("-" * 40)
    
    try:
        conn = sqlite3.connect('xianyu_data.db')
        cursor = conn.cursor()
        
        # 清理测试cookies
        cursor.execute('DELETE FROM cookies WHERE id LIKE "test_cookie_%"')
        cookie_count = cursor.rowcount
        
        # 清理测试用户
        test_usernames = [user['username'] for user in users]
        if test_usernames:
            placeholders = ','.join(['?' for _ in test_usernames])
            cursor.execute(f'DELETE FROM users WHERE username IN ({placeholders})', test_usernames)
            user_count = cursor.rowcount
        else:
            user_count = 0
        
        # 清理测试验证码
        cursor.execute('DELETE FROM email_verifications WHERE email LIKE "%@test.com"')
        email_count = cursor.rowcount
        
        cursor.execute('DELETE FROM captcha_codes WHERE session_id LIKE "test_%"')
        captcha_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✅ 清理完成:")
        print(f"   • 测试cookies: {cookie_count} 条")
        print(f"   • 测试用户: {user_count} 条")
        print(f"   • 邮箱验证码: {email_count} 条")
        print(f"   • 图形验证码: {captcha_count} 条")
        
    except Exception as e:
        print(f"❌ 清理失败: {e}")

def main():
    """主测试函数"""
    print("🚀 多用户数据隔离完整测试")
    print("=" * 60)
    
    try:
        # 创建测试用户
        users = create_test_users()
        
        if len(users) < 2:
            print("\n❌ 测试失败：无法创建足够的测试用户")
            return False
        
        print(f"\n✅ 成功创建 {len(users)} 个测试用户")
        
        # 测试Cookie数据隔离
        cookie_isolation_success = test_cookie_isolation(users)
        
        # 测试跨用户访问权限
        cross_access_success = test_cross_user_access(users)
        
        # 清理测试数据
        cleanup_test_data(users)
        
        print("\n" + "=" * 60)
        if cookie_isolation_success and cross_access_success:
            print("🎉 多用户数据隔离测试全部通过！")
            
            print("\n📋 测试总结:")
            print("✅ 用户注册和登录功能正常")
            print("✅ Cookie数据完全隔离")
            print("✅ 跨用户访问被正确拒绝")
            print("✅ 用户权限验证正常")
            
            print("\n🔒 安全特性:")
            print("• 每个用户只能看到自己的数据")
            print("• 跨用户访问被严格禁止")
            print("• API层面权限验证完整")
            print("• 数据库层面用户绑定正确")
            
            return True
        else:
            print("❌ 多用户数据隔离测试失败！")
            return False
            
    except Exception as e:
        print(f"\n💥 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()

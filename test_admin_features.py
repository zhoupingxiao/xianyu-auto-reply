#!/usr/bin/env python3
"""
测试管理员功能
"""

import requests
import json
import time
import sqlite3
from loguru import logger

BASE_URL = "http://localhost:8080"

def test_admin_login():
    """测试管理员登录"""
    logger.info("测试管理员登录...")
    
    response = requests.post(f"{BASE_URL}/login", 
                           json={'username': 'admin', 'password': 'admin123'})
    
    if response.json()['success']:
        token = response.json()['token']
        user_id = response.json()['user_id']
        
        logger.info(f"管理员登录成功，token: {token[:20]}...")
        return {
            'token': token,
            'user_id': user_id,
            'headers': {'Authorization': f'Bearer {token}'}
        }
    else:
        logger.error("管理员登录失败")
        return None

def test_user_management(admin):
    """测试用户管理功能"""
    logger.info("测试用户管理功能...")
    
    # 1. 获取所有用户
    response = requests.get(f"{BASE_URL}/admin/users", headers=admin['headers'])
    if response.status_code == 200:
        users = response.json()['users']
        logger.info(f"✅ 获取用户列表成功，共 {len(users)} 个用户")
        
        for user in users:
            logger.info(f"   用户: {user['username']} (ID: {user['id']}) - Cookie: {user.get('cookie_count', 0)}, 卡券: {user.get('card_count', 0)}")
    else:
        logger.error(f"❌ 获取用户列表失败: {response.status_code}")
        return False
    
    # 2. 测试非管理员权限验证
    logger.info("测试非管理员权限验证...")
    
    # 创建一个普通用户token（模拟）
    fake_headers = {'Authorization': 'Bearer fake_token'}
    response = requests.get(f"{BASE_URL}/admin/users", headers=fake_headers)
    
    if response.status_code == 401 or response.status_code == 403:
        logger.info("✅ 非管理员权限验证正常")
    else:
        logger.warning(f"⚠️ 权限验证可能有问题: {response.status_code}")
    
    return True

def test_system_stats(admin):
    """测试系统统计功能"""
    logger.info("测试系统统计功能...")
    
    response = requests.get(f"{BASE_URL}/admin/stats", headers=admin['headers'])
    if response.status_code == 200:
        stats = response.json()
        logger.info("✅ 获取系统统计成功:")
        logger.info(f"   总用户数: {stats['users']['total']}")
        logger.info(f"   总Cookie数: {stats['cookies']['total']}")
        logger.info(f"   总卡券数: {stats['cards']['total']}")
        logger.info(f"   系统版本: {stats['system']['version']}")
        return True
    else:
        logger.error(f"❌ 获取系统统计失败: {response.status_code}")
        return False

def test_log_management(admin):
    """测试日志管理功能"""
    logger.info("测试日志管理功能...")
    
    # 1. 获取系统日志
    response = requests.get(f"{BASE_URL}/admin/logs?lines=50", headers=admin['headers'])
    if response.status_code == 200:
        log_data = response.json()
        logs = log_data.get('logs', [])
        logger.info(f"✅ 获取系统日志成功，共 {len(logs)} 条")
        
        if logs:
            logger.info("   最新几条日志:")
            for i, log in enumerate(logs[-3:]):  # 显示最后3条
                logger.info(f"   {i+1}. {log[:100]}...")
    else:
        logger.error(f"❌ 获取系统日志失败: {response.status_code}")
        return False
    
    # 2. 测试日志级别过滤
    response = requests.get(f"{BASE_URL}/admin/logs?lines=20&level=info", headers=admin['headers'])
    if response.status_code == 200:
        log_data = response.json()
        info_logs = log_data.get('logs', [])
        logger.info(f"✅ INFO级别日志过滤成功，共 {len(info_logs)} 条")
    else:
        logger.error(f"❌ 日志级别过滤失败: {response.status_code}")
        return False
    
    return True

def create_test_user_for_deletion():
    """创建一个测试用户用于删除测试"""
    logger.info("创建测试用户用于删除测试...")
    
    user_data = {
        "username": "test_delete_user",
        "email": "delete@test.com",
        "password": "test123456"
    }
    
    try:
        # 清理可能存在的用户
        conn = sqlite3.connect('xianyu_data.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE username = ? OR email = ?', (user_data['username'], user_data['email']))
        cursor.execute('DELETE FROM email_verifications WHERE email = ?', (user_data['email'],))
        conn.commit()
        conn.close()
        
        # 生成验证码
        session_id = f"delete_test_{int(time.time())}"
        
        # 生成图形验证码
        captcha_response = requests.post(f"{BASE_URL}/generate-captcha", 
                                       json={'session_id': session_id})
        if not captcha_response.json()['success']:
            logger.error("图形验证码生成失败")
            return None
        
        # 获取图形验证码
        conn = sqlite3.connect('xianyu_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT code FROM captcha_codes WHERE session_id = ? ORDER BY created_at DESC LIMIT 1', 
                     (session_id,))
        captcha_result = cursor.fetchone()
        conn.close()
        
        if not captcha_result:
            logger.error("无法获取图形验证码")
            return None
        
        captcha_code = captcha_result[0]
        
        # 验证图形验证码
        verify_response = requests.post(f"{BASE_URL}/verify-captcha", 
                                      json={'session_id': session_id, 'captcha_code': captcha_code})
        if not verify_response.json()['success']:
            logger.error("图形验证码验证失败")
            return None
        
        # 发送邮箱验证码
        email_response = requests.post(f"{BASE_URL}/send-verification-code", 
                                     json={'email': user_data['email'], 'session_id': session_id})
        if not email_response.json()['success']:
            logger.error("邮箱验证码发送失败")
            return None
        
        # 获取邮箱验证码
        conn = sqlite3.connect('xianyu_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT code FROM email_verifications WHERE email = ? ORDER BY created_at DESC LIMIT 1', 
                     (user_data['email'],))
        email_result = cursor.fetchone()
        conn.close()
        
        if not email_result:
            logger.error("无法获取邮箱验证码")
            return None
        
        email_code = email_result[0]
        
        # 注册用户
        register_response = requests.post(f"{BASE_URL}/register", 
                                        json={
                                            'username': user_data['username'],
                                            'email': user_data['email'],
                                            'verification_code': email_code,
                                            'password': user_data['password']
                                        })
        
        if register_response.json()['success']:
            logger.info(f"测试用户创建成功: {user_data['username']}")
            
            # 获取用户ID
            conn = sqlite3.connect('xianyu_data.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE username = ?', (user_data['username'],))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'user_id': result[0],
                    'username': user_data['username']
                }
        
        logger.error("测试用户创建失败")
        return None
        
    except Exception as e:
        logger.error(f"创建测试用户失败: {e}")
        return None

def test_user_deletion(admin):
    """测试用户删除功能"""
    logger.info("测试用户删除功能...")
    
    # 创建测试用户
    test_user = create_test_user_for_deletion()
    if not test_user:
        logger.error("无法创建测试用户，跳过删除测试")
        return False
    
    user_id = test_user['user_id']
    username = test_user['username']
    
    # 删除用户
    response = requests.delete(f"{BASE_URL}/admin/users/{user_id}", headers=admin['headers'])
    if response.status_code == 200:
        logger.info(f"✅ 用户删除成功: {username}")
        
        # 验证用户确实被删除
        conn = sqlite3.connect('xianyu_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            logger.info("✅ 用户删除验证通过")
            return True
        else:
            logger.error("❌ 用户删除验证失败，用户仍然存在")
            return False
    else:
        logger.error(f"❌ 用户删除失败: {response.status_code}")
        return False

def test_admin_self_deletion_protection(admin):
    """测试管理员自删除保护"""
    logger.info("测试管理员自删除保护...")
    
    admin_user_id = admin['user_id']
    
    response = requests.delete(f"{BASE_URL}/admin/users/{admin_user_id}", headers=admin['headers'])
    if response.status_code == 400:
        logger.info("✅ 管理员自删除保护正常")
        return True
    else:
        logger.error(f"❌ 管理员自删除保护失败: {response.status_code}")
        return False

def main():
    """主测试函数"""
    print("🚀 管理员功能测试")
    print("=" * 60)
    
    print("📋 测试内容:")
    print("• 管理员登录")
    print("• 用户管理功能")
    print("• 系统统计功能")
    print("• 日志管理功能")
    print("• 用户删除功能")
    print("• 管理员保护机制")
    
    try:
        # 管理员登录
        admin = test_admin_login()
        if not admin:
            print("❌ 测试失败：管理员登录失败")
            return False
        
        print("✅ 管理员登录成功")
        
        # 测试各项功能
        tests = [
            ("用户管理", lambda: test_user_management(admin)),
            ("系统统计", lambda: test_system_stats(admin)),
            ("日志管理", lambda: test_log_management(admin)),
            ("用户删除", lambda: test_user_deletion(admin)),
            ("管理员保护", lambda: test_admin_self_deletion_protection(admin))
        ]
        
        results = []
        for test_name, test_func in tests:
            print(f"\n🧪 测试 {test_name}...")
            try:
                result = test_func()
                results.append((test_name, result))
                if result:
                    print(f"✅ {test_name} 测试通过")
                else:
                    print(f"❌ {test_name} 测试失败")
            except Exception as e:
                print(f"💥 {test_name} 测试异常: {e}")
                results.append((test_name, False))
        
        print("\n" + "=" * 60)
        print("🎉 管理员功能测试完成！")
        
        print("\n📊 测试结果:")
        passed = 0
        for test_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n📈 总体结果: {passed}/{len(results)} 项测试通过")
        
        if passed == len(results):
            print("🎊 所有测试都通过了！管理员功能正常工作。")
            
            print("\n💡 使用说明:")
            print("1. 使用admin账号登录系统")
            print("2. 在侧边栏可以看到'管理员功能'菜单")
            print("3. 点击'用户管理'可以查看和删除用户")
            print("4. 点击'系统日志'可以查看系统运行日志")
            print("5. 这些功能只有admin用户可以访问")
            
            return True
        else:
            print("⚠️ 部分测试失败，请检查相关功能。")
            return False
            
    except Exception as e:
        print(f"💥 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
测试用户日志显示功能
"""

import requests
import json
import time
import sqlite3
from loguru import logger

BASE_URL = "http://localhost:8080"

def create_test_user():
    """创建测试用户"""
    logger.info("创建测试用户...")
    
    user_data = {
        "username": "logtest_user",
        "email": "logtest@test.com",
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
        session_id = f"logtest_{int(time.time())}"
        
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
            logger.info(f"用户注册成功: {user_data['username']}")
            
            # 登录获取token
            login_response = requests.post(f"{BASE_URL}/login", 
                                         json={'username': user_data['username'], 'password': user_data['password']})
            
            if login_response.json()['success']:
                token = login_response.json()['token']
                user_id = login_response.json()['user_id']
                return {
                    'username': user_data['username'],
                    'user_id': user_id,
                    'token': token,
                    'headers': {'Authorization': f'Bearer {token}'}
                }
            else:
                logger.error("用户登录失败")
                return None
        else:
            logger.error(f"用户注册失败: {register_response.json()['message']}")
            return None
            
    except Exception as e:
        logger.error(f"创建用户失败: {e}")
        return None

def test_user_operations(user):
    """测试用户操作的日志显示"""
    logger.info("测试用户操作的日志显示...")
    
    print(f"\n🧪 开始测试用户 {user['username']} 的操作日志")
    print("请观察服务器日志，应该显示用户信息...")
    print("-" * 50)
    
    # 1. 测试Cookie操作
    print("1️⃣ 测试Cookie操作...")
    cookie_data = {
        "id": "logtest_cookie",
        "value": "test_cookie_value"
    }
    
    response = requests.post(f"{BASE_URL}/cookies", json=cookie_data, headers=user['headers'])
    if response.status_code == 200:
        print("   ✅ Cookie添加成功")
    else:
        print(f"   ❌ Cookie添加失败: {response.text}")
    
    # 2. 测试获取Cookie列表
    print("2️⃣ 测试获取Cookie列表...")
    response = requests.get(f"{BASE_URL}/cookies", headers=user['headers'])
    if response.status_code == 200:
        print("   ✅ 获取Cookie列表成功")
    else:
        print(f"   ❌ 获取Cookie列表失败: {response.text}")
    
    # 3. 测试关键字操作
    print("3️⃣ 测试关键字操作...")
    keywords_data = {
        "keywords": {
            "你好": "您好，欢迎咨询！",
            "价格": "价格请看商品详情"
        }
    }
    
    response = requests.post(f"{BASE_URL}/keywords/logtest_cookie", 
                           json=keywords_data, headers=user['headers'])
    if response.status_code == 200:
        print("   ✅ 关键字更新成功")
    else:
        print(f"   ❌ 关键字更新失败: {response.text}")
    
    # 4. 测试卡券操作
    print("4️⃣ 测试卡券操作...")
    card_data = {
        "name": "测试卡券",
        "type": "text",
        "text_content": "这是一个测试卡券",
        "description": "用于测试日志显示的卡券"
    }
    
    response = requests.post(f"{BASE_URL}/cards", json=card_data, headers=user['headers'])
    if response.status_code == 200:
        print("   ✅ 卡券创建成功")
    else:
        print(f"   ❌ 卡券创建失败: {response.text}")
    
    # 5. 测试用户设置
    print("5️⃣ 测试用户设置...")
    setting_data = {
        "value": "#ff6600",
        "description": "测试主题颜色"
    }
    
    response = requests.put(f"{BASE_URL}/user-settings/theme_color", 
                          json=setting_data, headers=user['headers'])
    if response.status_code == 200:
        print("   ✅ 用户设置更新成功")
    else:
        print(f"   ❌ 用户设置更新失败: {response.text}")
    
    # 6. 测试权限验证（尝试访问不存在的Cookie）
    print("6️⃣ 测试权限验证...")
    response = requests.get(f"{BASE_URL}/keywords/nonexistent_cookie", headers=user['headers'])
    if response.status_code == 403:
        print("   ✅ 权限验证正常（403错误）")
    else:
        print(f"   ⚠️ 权限验证结果: {response.status_code}")
    
    print("-" * 50)
    print("🎯 操作测试完成，请检查服务器日志中的用户信息显示")

def test_admin_operations():
    """测试管理员操作"""
    print("\n🔧 测试管理员操作...")
    
    # 管理员登录
    admin_login = requests.post(f"{BASE_URL}/login", 
                              json={'username': 'admin', 'password': 'admin123'})
    
    if admin_login.json()['success']:
        admin_token = admin_login.json()['token']
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        
        print("   ✅ 管理员登录成功")
        
        # 测试管理员获取Cookie列表
        response = requests.get(f"{BASE_URL}/cookies", headers=admin_headers)
        if response.status_code == 200:
            print("   ✅ 管理员获取Cookie列表成功")
        else:
            print(f"   ❌ 管理员获取Cookie列表失败: {response.text}")
    else:
        print("   ❌ 管理员登录失败")

def cleanup_test_data(user):
    """清理测试数据"""
    logger.info("清理测试数据...")
    
    try:
        conn = sqlite3.connect('xianyu_data.db')
        cursor = conn.cursor()
        
        # 清理测试用户
        cursor.execute('DELETE FROM users WHERE username = ?', (user['username'],))
        user_count = cursor.rowcount
        
        # 清理测试Cookie
        cursor.execute('DELETE FROM cookies WHERE id = "logtest_cookie"')
        cookie_count = cursor.rowcount
        
        # 清理测试卡券
        cursor.execute('DELETE FROM cards WHERE name = "测试卡券"')
        card_count = cursor.rowcount
        
        # 清理测试验证码
        cursor.execute('DELETE FROM email_verifications WHERE email = "logtest@test.com"')
        email_count = cursor.rowcount
        
        cursor.execute('DELETE FROM captcha_codes WHERE session_id LIKE "logtest_%"')
        captcha_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"清理完成: 用户{user_count}个, Cookie{cookie_count}个, 卡券{card_count}个, 邮箱验证码{email_count}个, 图形验证码{captcha_count}个")
        
    except Exception as e:
        logger.error(f"清理失败: {e}")

def main():
    """主测试函数"""
    print("🚀 用户日志显示功能测试")
    print("=" * 60)
    
    print("📋 测试目标:")
    print("• 验证API请求日志显示用户信息")
    print("• 验证业务操作日志显示用户信息")
    print("• 验证权限验证日志显示用户信息")
    print("• 验证管理员操作日志显示")
    
    try:
        # 创建测试用户
        user = create_test_user()
        
        if not user:
            print("❌ 测试失败：无法创建测试用户")
            return False
        
        print(f"✅ 成功创建测试用户: {user['username']}")
        
        # 测试用户操作
        test_user_operations(user)
        
        # 测试管理员操作
        test_admin_operations()
        
        # 清理测试数据
        cleanup_test_data(user)
        
        print("\n" + "=" * 60)
        print("🎉 用户日志显示功能测试完成！")
        
        print("\n📋 检查要点:")
        print("✅ 1. API请求日志应显示: 【用户名#用户ID】")
        print("✅ 2. 业务操作日志应显示用户信息")
        print("✅ 3. 权限验证日志应显示操作用户")
        print("✅ 4. 管理员操作应显示: 【admin#1】")
        
        print("\n💡 日志格式示例:")
        print("🌐 【logtest_user#2】 API请求: POST /cookies")
        print("✅ 【logtest_user#2】 API响应: POST /cookies - 200 (0.005s)")
        print("📝 【logtest_user#2】 尝试添加Cookie: logtest_cookie")
        print("✅ 【logtest_user#2】 Cookie添加成功: logtest_cookie")
        
        return True
        
    except Exception as e:
        print(f"💥 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()

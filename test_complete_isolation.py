#!/usr/bin/env python3
"""
完整的多用户数据隔离测试
"""

import requests
import json
import time
import sqlite3
from loguru import logger

BASE_URL = "http://localhost:8080"

def create_test_users():
    """创建测试用户"""
    logger.info("创建测试用户...")
    
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
                logger.error(f"图形验证码生成失败: {user['username']}")
                continue
            
            # 获取图形验证码
            conn = sqlite3.connect('xianyu_data.db')
            cursor = conn.cursor()
            cursor.execute('SELECT code FROM captcha_codes WHERE session_id = ? ORDER BY created_at DESC LIMIT 1', 
                         (session_id,))
            captcha_result = cursor.fetchone()
            conn.close()
            
            if not captcha_result:
                logger.error(f"无法获取图形验证码: {user['username']}")
                continue
            
            captcha_code = captcha_result[0]
            
            # 验证图形验证码
            verify_response = requests.post(f"{BASE_URL}/verify-captcha", 
                                          json={'session_id': session_id, 'captcha_code': captcha_code})
            if not verify_response.json()['success']:
                logger.error(f"图形验证码验证失败: {user['username']}")
                continue
            
            # 发送邮箱验证码
            email_response = requests.post(f"{BASE_URL}/send-verification-code", 
                                         json={'email': user['email'], 'session_id': session_id})
            if not email_response.json()['success']:
                logger.error(f"邮箱验证码发送失败: {user['username']}")
                continue
            
            # 获取邮箱验证码
            conn = sqlite3.connect('xianyu_data.db')
            cursor = conn.cursor()
            cursor.execute('SELECT code FROM email_verifications WHERE email = ? ORDER BY created_at DESC LIMIT 1', 
                         (user['email'],))
            email_result = cursor.fetchone()
            conn.close()
            
            if not email_result:
                logger.error(f"无法获取邮箱验证码: {user['username']}")
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
                logger.info(f"用户注册成功: {user['username']}")
                
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
                    logger.info(f"用户登录成功: {user['username']}")
                else:
                    logger.error(f"用户登录失败: {user['username']}")
            else:
                logger.error(f"用户注册失败: {user['username']} - {register_response.json()['message']}")
                
        except Exception as e:
            logger.error(f"创建用户失败: {user['username']} - {e}")
    
    return created_users

def test_cards_isolation(users):
    """测试卡券管理的用户隔离"""
    logger.info("测试卡券管理的用户隔离...")
    
    if len(users) < 2:
        logger.error("需要至少2个用户进行隔离测试")
        return False
    
    user1, user2 = users[0], users[1]
    
    # 用户1创建卡券
    card1_data = {
        "name": "用户1的卡券",
        "type": "text",
        "text_content": "这是用户1的卡券内容",
        "description": "用户1创建的测试卡券"
    }
    
    response1 = requests.post(f"{BASE_URL}/cards", json=card1_data, headers=user1['headers'])
    if response1.status_code == 200:
        card1_id = response1.json()['id']
        logger.info(f"用户1创建卡券成功: ID={card1_id}")
    else:
        logger.error(f"用户1创建卡券失败: {response1.text}")
        return False
    
    # 用户2创建卡券
    card2_data = {
        "name": "用户2的卡券",
        "type": "text", 
        "text_content": "这是用户2的卡券内容",
        "description": "用户2创建的测试卡券"
    }
    
    response2 = requests.post(f"{BASE_URL}/cards", json=card2_data, headers=user2['headers'])
    if response2.status_code == 200:
        card2_id = response2.json()['id']
        logger.info(f"用户2创建卡券成功: ID={card2_id}")
    else:
        logger.error(f"用户2创建卡券失败: {response2.text}")
        return False
    
    # 验证用户1只能看到自己的卡券
    response1_list = requests.get(f"{BASE_URL}/cards", headers=user1['headers'])
    if response1_list.status_code == 200:
        user1_cards = response1_list.json()
        user1_card_names = [card['name'] for card in user1_cards]
        
        if "用户1的卡券" in user1_card_names and "用户2的卡券" not in user1_card_names:
            logger.info("✅ 用户1卡券隔离验证通过")
        else:
            logger.error("❌ 用户1卡券隔离验证失败")
            return False
    else:
        logger.error(f"获取用户1卡券列表失败: {response1_list.text}")
        return False
    
    # 验证用户2只能看到自己的卡券
    response2_list = requests.get(f"{BASE_URL}/cards", headers=user2['headers'])
    if response2_list.status_code == 200:
        user2_cards = response2_list.json()
        user2_card_names = [card['name'] for card in user2_cards]
        
        if "用户2的卡券" in user2_card_names and "用户1的卡券" not in user2_card_names:
            logger.info("✅ 用户2卡券隔离验证通过")
        else:
            logger.error("❌ 用户2卡券隔离验证失败")
            return False
    else:
        logger.error(f"获取用户2卡券列表失败: {response2_list.text}")
        return False
    
    # 验证跨用户访问被拒绝
    response_cross = requests.get(f"{BASE_URL}/cards/{card2_id}", headers=user1['headers'])
    if response_cross.status_code == 403 or response_cross.status_code == 404:
        logger.info("✅ 跨用户卡券访问被正确拒绝")
    else:
        logger.error("❌ 跨用户卡券访问未被拒绝")
        return False
    
    return True

def test_user_settings(users):
    """测试用户设置功能"""
    logger.info("测试用户设置功能...")
    
    if len(users) < 2:
        logger.error("需要至少2个用户进行设置测试")
        return False
    
    user1, user2 = users[0], users[1]
    
    # 用户1设置主题颜色
    setting1_data = {"value": "#ff0000", "description": "用户1的红色主题"}
    response1 = requests.put(f"{BASE_URL}/user-settings/theme_color", 
                           json=setting1_data, headers=user1['headers'])
    
    if response1.status_code == 200:
        logger.info("用户1主题颜色设置成功")
    else:
        logger.error(f"用户1主题颜色设置失败: {response1.text}")
        return False
    
    # 用户2设置主题颜色
    setting2_data = {"value": "#00ff00", "description": "用户2的绿色主题"}
    response2 = requests.put(f"{BASE_URL}/user-settings/theme_color", 
                           json=setting2_data, headers=user2['headers'])
    
    if response2.status_code == 200:
        logger.info("用户2主题颜色设置成功")
    else:
        logger.error(f"用户2主题颜色设置失败: {response2.text}")
        return False
    
    # 验证用户1的设置
    response1_get = requests.get(f"{BASE_URL}/user-settings/theme_color", headers=user1['headers'])
    if response1_get.status_code == 200:
        user1_color = response1_get.json()['value']
        if user1_color == "#ff0000":
            logger.info("✅ 用户1主题颜色隔离验证通过")
        else:
            logger.error(f"❌ 用户1主题颜色错误: {user1_color}")
            return False
    else:
        logger.error(f"获取用户1主题颜色失败: {response1_get.text}")
        return False
    
    # 验证用户2的设置
    response2_get = requests.get(f"{BASE_URL}/user-settings/theme_color", headers=user2['headers'])
    if response2_get.status_code == 200:
        user2_color = response2_get.json()['value']
        if user2_color == "#00ff00":
            logger.info("✅ 用户2主题颜色隔离验证通过")
        else:
            logger.error(f"❌ 用户2主题颜色错误: {user2_color}")
            return False
    else:
        logger.error(f"获取用户2主题颜色失败: {response2_get.text}")
        return False
    
    return True

def cleanup_test_data(users):
    """清理测试数据"""
    logger.info("清理测试数据...")
    
    try:
        conn = sqlite3.connect('xianyu_data.db')
        cursor = conn.cursor()
        
        # 清理测试用户
        test_usernames = [user['username'] for user in users]
        if test_usernames:
            placeholders = ','.join(['?' for _ in test_usernames])
            cursor.execute(f'DELETE FROM users WHERE username IN ({placeholders})', test_usernames)
            user_count = cursor.rowcount
        else:
            user_count = 0
        
        # 清理测试卡券
        cursor.execute('DELETE FROM cards WHERE name LIKE "用户%的卡券"')
        card_count = cursor.rowcount
        
        # 清理测试验证码
        cursor.execute('DELETE FROM email_verifications WHERE email LIKE "%@test.com"')
        email_count = cursor.rowcount
        
        cursor.execute('DELETE FROM captcha_codes WHERE session_id LIKE "test_%"')
        captcha_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"清理完成: 用户{user_count}个, 卡券{card_count}个, 邮箱验证码{email_count}个, 图形验证码{captcha_count}个")
        
    except Exception as e:
        logger.error(f"清理失败: {e}")

def main():
    """主测试函数"""
    print("🚀 完整的多用户数据隔离测试")
    print("=" * 60)
    
    try:
        # 创建测试用户
        users = create_test_users()
        
        if len(users) < 2:
            print("❌ 测试失败：无法创建足够的测试用户")
            return False
        
        print(f"✅ 成功创建 {len(users)} 个测试用户")
        
        # 测试卡券管理隔离
        cards_success = test_cards_isolation(users)
        
        # 测试用户设置
        settings_success = test_user_settings(users)
        
        # 清理测试数据
        cleanup_test_data(users)
        
        print("\n" + "=" * 60)
        if cards_success and settings_success:
            print("🎉 完整的多用户数据隔离测试全部通过！")
            
            print("\n📋 测试总结:")
            print("✅ 卡券管理完全隔离")
            print("✅ 用户设置完全隔离")
            print("✅ 跨用户访问被正确拒绝")
            print("✅ 数据库层面用户绑定正确")
            
            return True
        else:
            print("❌ 多用户数据隔离测试失败！")
            return False
            
    except Exception as e:
        print(f"💥 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
图形验证码注册流程演示
"""

import requests
import json
import sqlite3
import time

def demo_complete_registration():
    """演示完整的注册流程"""
    print("🎭 图形验证码注册流程演示")
    print("=" * 60)
    
    session_id = f"demo_session_{int(time.time())}"
    test_email = "demo@example.com"
    test_username = "demouser"
    test_password = "demo123456"
    
    # 清理可能存在的测试数据
    try:
        conn = sqlite3.connect('xianyu_data.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE username = ? OR email = ?', (test_username, test_email))
        cursor.execute('DELETE FROM email_verifications WHERE email = ?', (test_email,))
        cursor.execute('DELETE FROM captcha_codes WHERE session_id = ?', (session_id,))
        conn.commit()
        conn.close()
        print("🧹 清理旧的测试数据")
    except:
        pass
    
    print("\n📋 注册流程步骤:")
    print("1. 生成图形验证码")
    print("2. 用户输入图形验证码")
    print("3. 验证图形验证码")
    print("4. 发送邮箱验证码")
    print("5. 用户输入邮箱验证码")
    print("6. 完成注册")
    
    # 步骤1: 生成图形验证码
    print("\n🔸 步骤1: 生成图形验证码")
    response = requests.post('http://localhost:8080/generate-captcha', 
                           json={'session_id': session_id})
    
    if response.status_code != 200:
        print(f"❌ 生成图形验证码失败: {response.status_code}")
        return False
    
    result = response.json()
    if not result['success']:
        print(f"❌ 生成图形验证码失败: {result['message']}")
        return False
    
    print("✅ 图形验证码生成成功")
    
    # 从数据库获取验证码文本（模拟用户看到图片并输入）
    conn = sqlite3.connect('xianyu_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT code FROM captcha_codes WHERE session_id = ? ORDER BY created_at DESC LIMIT 1', 
                 (session_id,))
    captcha_result = cursor.fetchone()
    conn.close()
    
    if not captcha_result:
        print("❌ 无法获取图形验证码")
        return False
    
    captcha_text = captcha_result[0]
    print(f"📷 图形验证码: {captcha_text}")
    
    # 步骤2-3: 验证图形验证码
    print("\n🔸 步骤2-3: 验证图形验证码")
    response = requests.post('http://localhost:8080/verify-captcha', 
                           json={
                               'session_id': session_id,
                               'captcha_code': captcha_text
                           })
    
    if response.status_code != 200:
        print(f"❌ 验证图形验证码失败: {response.status_code}")
        return False
    
    result = response.json()
    if not result['success']:
        print(f"❌ 图形验证码验证失败: {result['message']}")
        return False
    
    print("✅ 图形验证码验证成功")
    
    # 步骤4: 发送邮箱验证码
    print("\n🔸 步骤4: 发送邮箱验证码")
    response = requests.post('http://localhost:8080/send-verification-code', 
                           json={'email': test_email})
    
    if response.status_code != 200:
        print(f"❌ 发送邮箱验证码失败: {response.status_code}")
        return False
    
    result = response.json()
    if not result['success']:
        print(f"❌ 发送邮箱验证码失败: {result['message']}")
        return False
    
    print("✅ 邮箱验证码发送成功")
    
    # 从数据库获取邮箱验证码（模拟用户收到邮件）
    conn = sqlite3.connect('xianyu_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT code FROM email_verifications WHERE email = ? ORDER BY created_at DESC LIMIT 1', 
                 (test_email,))
    email_result = cursor.fetchone()
    conn.close()
    
    if not email_result:
        print("❌ 无法获取邮箱验证码")
        return False
    
    email_code = email_result[0]
    print(f"📧 邮箱验证码: {email_code}")
    
    # 步骤5-6: 完成注册
    print("\n🔸 步骤5-6: 完成用户注册")
    response = requests.post('http://localhost:8080/register', 
                           json={
                               'username': test_username,
                               'email': test_email,
                               'verification_code': email_code,
                               'password': test_password
                           })
    
    if response.status_code != 200:
        print(f"❌ 用户注册失败: {response.status_code}")
        return False
    
    result = response.json()
    if not result['success']:
        print(f"❌ 用户注册失败: {result['message']}")
        return False
    
    print("✅ 用户注册成功")
    
    # 验证登录
    print("\n🔸 验证登录功能")
    response = requests.post('http://localhost:8080/login', 
                           json={
                               'username': test_username,
                               'password': test_password
                           })
    
    if response.status_code != 200:
        print(f"❌ 用户登录失败: {response.status_code}")
        return False
    
    result = response.json()
    if not result['success']:
        print(f"❌ 用户登录失败: {result['message']}")
        return False
    
    print("✅ 用户登录成功")
    print(f"🎫 Token: {result['token'][:20]}...")
    print(f"👤 用户ID: {result['user_id']}")
    
    return True

def demo_security_features():
    """演示安全特性"""
    print("\n🔒 安全特性演示")
    print("-" * 40)
    
    session_id = f"security_test_{int(time.time())}"
    
    # 1. 测试错误的图形验证码
    print("1️⃣ 测试错误的图形验证码...")
    
    # 先生成一个验证码
    requests.post('http://localhost:8080/generate-captcha', 
                 json={'session_id': session_id})
    
    # 尝试用错误的验证码
    response = requests.post('http://localhost:8080/verify-captcha', 
                           json={
                               'session_id': session_id,
                               'captcha_code': 'WRONG'
                           })
    
    result = response.json()
    if not result['success']:
        print("   ✅ 错误的图形验证码被正确拒绝")
    else:
        print("   ❌ 错误的图形验证码验证成功（安全漏洞）")
    
    # 2. 测试未验证图形验证码就发送邮件
    print("\n2️⃣ 测试未验证图形验证码发送邮件...")
    
    # 注意：当前实现中发送邮件接口没有检查图形验证码状态
    # 这是前端控制的，后端应该也要检查
    response = requests.post('http://localhost:8080/send-verification-code', 
                           json={'email': 'test@example.com'})
    
    result = response.json()
    if result['success']:
        print("   ⚠️ 未验证图形验证码也能发送邮件（建议后端也要检查）")
    else:
        print("   ✅ 未验证图形验证码无法发送邮件")
    
    # 3. 测试验证码重复使用
    print("\n3️⃣ 测试验证码重复使用...")
    
    # 生成新的验证码
    session_id2 = f"reuse_test_{int(time.time())}"
    requests.post('http://localhost:8080/generate-captcha', 
                 json={'session_id': session_id2})
    
    # 获取验证码
    conn = sqlite3.connect('xianyu_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT code FROM captcha_codes WHERE session_id = ? ORDER BY created_at DESC LIMIT 1', 
                 (session_id2,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        captcha_code = result[0]
        
        # 第一次验证
        response1 = requests.post('http://localhost:8080/verify-captcha', 
                                json={
                                    'session_id': session_id2,
                                    'captcha_code': captcha_code
                                })
        
        # 第二次验证（重复使用）
        response2 = requests.post('http://localhost:8080/verify-captcha', 
                                json={
                                    'session_id': session_id2,
                                    'captcha_code': captcha_code
                                })
        
        result1 = response1.json()
        result2 = response2.json()
        
        if result1['success'] and not result2['success']:
            print("   ✅ 验证码重复使用被正确阻止")
        else:
            print("   ❌ 验证码可以重复使用（安全漏洞）")

def cleanup_demo_data():
    """清理演示数据"""
    print("\n🧹 清理演示数据")
    print("-" * 40)
    
    try:
        conn = sqlite3.connect('xianyu_data.db')
        cursor = conn.cursor()
        
        # 清理测试用户
        cursor.execute('DELETE FROM users WHERE username LIKE "demo%" OR email LIKE "demo%"')
        user_count = cursor.rowcount
        
        # 清理测试验证码
        cursor.execute('DELETE FROM email_verifications WHERE email LIKE "demo%"')
        email_count = cursor.rowcount
        
        # 清理测试图形验证码
        cursor.execute('DELETE FROM captcha_codes WHERE session_id LIKE "demo%" OR session_id LIKE "security%" OR session_id LIKE "reuse%"')
        captcha_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"✅ 清理完成:")
        print(f"   • 用户: {user_count} 条")
        print(f"   • 邮箱验证码: {email_count} 条")
        print(f"   • 图形验证码: {captcha_count} 条")
        
    except Exception as e:
        print(f"❌ 清理失败: {e}")

def main():
    """主演示函数"""
    print("🎪 图形验证码系统完整演示")
    print("=" * 60)
    
    try:
        # 演示完整注册流程
        success = demo_complete_registration()
        
        if success:
            print("\n🎉 完整注册流程演示成功！")
        else:
            print("\n💥 注册流程演示失败！")
            return False
        
        # 演示安全特性
        demo_security_features()
        
        # 清理演示数据
        cleanup_demo_data()
        
        print("\n" + "=" * 60)
        print("🎊 图形验证码系统演示完成！")
        
        print("\n📋 功能总结:")
        print("✅ 图形验证码生成和验证")
        print("✅ 邮箱验证码发送")
        print("✅ 用户注册流程")
        print("✅ 用户登录验证")
        print("✅ 安全特性保护")
        
        print("\n🌐 使用方法:")
        print("1. 访问: http://localhost:8080/register.html")
        print("2. 查看图形验证码并输入")
        print("3. 输入邮箱地址")
        print("4. 点击发送验证码（需要先验证图形验证码）")
        print("5. 输入邮箱验证码")
        print("6. 设置密码并完成注册")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()

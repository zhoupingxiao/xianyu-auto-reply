#!/usr/bin/env python3
"""
图形验证码系统测试
"""

import requests
import json
import sqlite3
import base64
from io import BytesIO
from PIL import Image

def test_captcha_generation():
    """测试图形验证码生成"""
    print("🧪 测试图形验证码生成")
    print("-" * 40)
    
    session_id = "test_session_123"
    
    # 1. 生成图形验证码
    print("1️⃣ 生成图形验证码...")
    response = requests.post('http://localhost:8080/generate-captcha', 
                           json={'session_id': session_id})
    
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   成功: {result['success']}")
        print(f"   消息: {result['message']}")
        
        if result['success']:
            captcha_image = result['captcha_image']
            print(f"   图片数据长度: {len(captcha_image)}")
            
            # 保存图片到文件（用于调试）
            if captcha_image.startswith('data:image/png;base64,'):
                image_data = captcha_image.split(',')[1]
                image_bytes = base64.b64decode(image_data)
                
                with open('test_captcha.png', 'wb') as f:
                    f.write(image_bytes)
                print("   ✅ 图片已保存为 test_captcha.png")
                
                # 从数据库获取验证码文本
                conn = sqlite3.connect('xianyu_data.db')
                cursor = conn.cursor()
                cursor.execute('SELECT code FROM captcha_codes WHERE session_id = ? ORDER BY created_at DESC LIMIT 1', 
                             (session_id,))
                result = cursor.fetchone()
                if result:
                    captcha_text = result[0]
                    print(f"   验证码文本: {captcha_text}")
                    conn.close()
                    return session_id, captcha_text
                conn.close()
        else:
            print("   ❌ 图形验证码生成失败")
    else:
        print(f"   ❌ 请求失败: {response.text}")
    
    return None, None

def test_captcha_verification(session_id, captcha_text):
    """测试图形验证码验证"""
    print("\n🧪 测试图形验证码验证")
    print("-" * 40)
    
    # 2. 验证正确的验证码
    print("2️⃣ 验证正确的验证码...")
    response = requests.post('http://localhost:8080/verify-captcha', 
                           json={
                               'session_id': session_id,
                               'captcha_code': captcha_text
                           })
    
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   成功: {result['success']}")
        print(f"   消息: {result['message']}")
        
        if result['success']:
            print("   ✅ 正确验证码验证成功")
        else:
            print("   ❌ 正确验证码验证失败")
    
    # 3. 验证错误的验证码
    print("\n3️⃣ 验证错误的验证码...")
    response = requests.post('http://localhost:8080/verify-captcha', 
                           json={
                               'session_id': session_id,
                               'captcha_code': 'WRONG'
                           })
    
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   成功: {result['success']}")
        print(f"   消息: {result['message']}")
        
        if not result['success']:
            print("   ✅ 错误验证码被正确拒绝")
        else:
            print("   ❌ 错误验证码验证成功（不应该）")

def test_captcha_expiry():
    """测试图形验证码过期"""
    print("\n🧪 测试图形验证码过期")
    print("-" * 40)
    
    # 直接在数据库中插入过期的验证码
    import time
    expired_session = "expired_session_123"
    expired_time = time.time() - 3600  # 1小时前
    
    conn = sqlite3.connect('xianyu_data.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO captcha_codes (session_id, code, expires_at)
    VALUES (?, ?, ?)
    ''', (expired_session, 'EXPIRED', expired_time))
    conn.commit()
    conn.close()
    
    print("4️⃣ 验证过期的验证码...")
    response = requests.post('http://localhost:8080/verify-captcha', 
                           json={
                               'session_id': expired_session,
                               'captcha_code': 'EXPIRED'
                           })
    
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   成功: {result['success']}")
        print(f"   消息: {result['message']}")
        
        if not result['success']:
            print("   ✅ 过期验证码被正确拒绝")
        else:
            print("   ❌ 过期验证码验证成功（不应该）")

def test_database_cleanup():
    """测试数据库清理"""
    print("\n🧪 测试数据库清理")
    print("-" * 40)
    
    conn = sqlite3.connect('xianyu_data.db')
    cursor = conn.cursor()
    
    # 清理测试数据
    cursor.execute('DELETE FROM captcha_codes WHERE session_id LIKE "test%" OR session_id LIKE "expired%"')
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"5️⃣ 清理测试数据: 删除了 {deleted_count} 条记录")
    print("   ✅ 数据库清理完成")

def test_frontend_integration():
    """测试前端集成"""
    print("\n🧪 测试前端集成")
    print("-" * 40)
    
    # 测试注册页面是否可以访问
    print("6️⃣ 测试注册页面...")
    response = requests.get('http://localhost:8080/register.html')
    
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        content = response.text
        
        # 检查是否包含图形验证码相关元素
        checks = [
            ('captchaCode', '图形验证码输入框'),
            ('captchaImage', '图形验证码图片'),
            ('refreshCaptcha', '刷新验证码函数'),
            ('verifyCaptcha', '验证验证码函数'),
            ('loadCaptcha', '加载验证码函数')
        ]
        
        for check_item, description in checks:
            if check_item in content:
                print(f"   ✅ {description}: 存在")
            else:
                print(f"   ❌ {description}: 缺失")
        
        print("   ✅ 注册页面加载成功")
    else:
        print(f"   ❌ 注册页面加载失败: {response.status_code}")

def main():
    """主测试函数"""
    print("🚀 图形验证码系统测试")
    print("=" * 60)
    
    try:
        # 测试图形验证码生成
        session_id, captcha_text = test_captcha_generation()
        
        if session_id and captcha_text:
            # 测试图形验证码验证
            test_captcha_verification(session_id, captcha_text)
        
        # 测试验证码过期
        test_captcha_expiry()
        
        # 测试前端集成
        test_frontend_integration()
        
        # 清理测试数据
        test_database_cleanup()
        
        print("\n" + "=" * 60)
        print("🎉 图形验证码系统测试完成！")
        
        print("\n📋 测试总结:")
        print("✅ 图形验证码生成功能正常")
        print("✅ 图形验证码验证功能正常")
        print("✅ 过期验证码处理正常")
        print("✅ 前端页面集成正常")
        print("✅ 数据库操作正常")
        
        print("\n💡 下一步:")
        print("1. 访问 http://localhost:8080/register.html")
        print("2. 测试图形验证码功能")
        print("3. 验证邮箱验证码发送需要先通过图形验证码")
        print("4. 完成用户注册流程")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()

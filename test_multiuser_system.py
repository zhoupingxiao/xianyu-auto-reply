#!/usr/bin/env python3
"""
多用户系统功能测试
"""

import asyncio
import json
import time
from db_manager import db_manager

async def test_user_registration():
    """测试用户注册功能"""
    print("🧪 测试用户注册功能")
    print("-" * 40)
    
    # 测试邮箱验证码生成
    print("1️⃣ 测试验证码生成...")
    code = db_manager.generate_verification_code()
    print(f"   生成的验证码: {code}")
    assert len(code) == 6 and code.isdigit(), "验证码应该是6位数字"
    print("   ✅ 验证码生成正常")
    
    # 测试保存验证码
    print("\n2️⃣ 测试验证码保存...")
    test_email = "test@example.com"
    success = db_manager.save_verification_code(test_email, code)
    assert success, "验证码保存应该成功"
    print("   ✅ 验证码保存成功")
    
    # 测试验证码验证
    print("\n3️⃣ 测试验证码验证...")
    valid = db_manager.verify_email_code(test_email, code)
    assert valid, "正确的验证码应该验证成功"
    print("   ✅ 验证码验证成功")
    
    # 测试验证码重复使用
    print("\n4️⃣ 测试验证码重复使用...")
    valid_again = db_manager.verify_email_code(test_email, code)
    assert not valid_again, "已使用的验证码不应该再次验证成功"
    print("   ✅ 验证码重复使用被正确阻止")
    
    # 测试用户创建
    print("\n5️⃣ 测试用户创建...")
    test_username = "testuser"
    test_password = "testpass123"
    
    # 先清理可能存在的测试用户
    try:
        db_manager.conn.execute("DELETE FROM users WHERE username = ? OR email = ?", (test_username, test_email))
        db_manager.conn.commit()
    except:
        pass
    
    success = db_manager.create_user(test_username, test_email, test_password)
    assert success, "用户创建应该成功"
    print("   ✅ 用户创建成功")
    
    # 测试重复用户名
    print("\n6️⃣ 测试重复用户名...")
    success = db_manager.create_user(test_username, "another@example.com", test_password)
    assert not success, "重复用户名应该创建失败"
    print("   ✅ 重复用户名被正确拒绝")
    
    # 测试重复邮箱
    print("\n7️⃣ 测试重复邮箱...")
    success = db_manager.create_user("anotheruser", test_email, test_password)
    assert not success, "重复邮箱应该创建失败"
    print("   ✅ 重复邮箱被正确拒绝")
    
    # 测试用户查询
    print("\n8️⃣ 测试用户查询...")
    user = db_manager.get_user_by_username(test_username)
    assert user is not None, "应该能查询到创建的用户"
    assert user['username'] == test_username, "用户名应该匹配"
    assert user['email'] == test_email, "邮箱应该匹配"
    print("   ✅ 用户查询成功")
    
    # 测试密码验证
    print("\n9️⃣ 测试密码验证...")
    valid = db_manager.verify_user_password(test_username, test_password)
    assert valid, "正确密码应该验证成功"
    
    invalid = db_manager.verify_user_password(test_username, "wrongpassword")
    assert not invalid, "错误密码应该验证失败"
    print("   ✅ 密码验证正常")
    
    # 清理测试数据
    print("\n🧹 清理测试数据...")
    db_manager.conn.execute("DELETE FROM users WHERE username = ?", (test_username,))
    db_manager.conn.execute("DELETE FROM email_verifications WHERE email = ?", (test_email,))
    db_manager.conn.commit()
    print("   ✅ 测试数据清理完成")

def test_user_isolation():
    """测试用户数据隔离"""
    print("\n🧪 测试用户数据隔离")
    print("-" * 40)
    
    # 创建测试用户
    print("1️⃣ 创建测试用户...")
    user1_name = "testuser1"
    user2_name = "testuser2"
    user1_email = "user1@test.com"
    user2_email = "user2@test.com"
    password = "testpass123"
    
    # 清理可能存在的测试数据
    try:
        db_manager.conn.execute("DELETE FROM cookies WHERE id LIKE 'test_%'")
        db_manager.conn.execute("DELETE FROM users WHERE username IN (?, ?)", (user1_name, user2_name))
        db_manager.conn.commit()
    except:
        pass
    
    # 创建用户
    success1 = db_manager.create_user(user1_name, user1_email, password)
    success2 = db_manager.create_user(user2_name, user2_email, password)
    assert success1 and success2, "用户创建应该成功"
    
    user1 = db_manager.get_user_by_username(user1_name)
    user2 = db_manager.get_user_by_username(user2_name)
    user1_id = user1['id']
    user2_id = user2['id']
    print(f"   ✅ 用户创建成功: {user1_name}(ID:{user1_id}), {user2_name}(ID:{user2_id})")
    
    # 测试Cookie隔离
    print("\n2️⃣ 测试Cookie数据隔离...")
    
    # 用户1添加cookies
    db_manager.save_cookie("test_cookie_1", "cookie_value_1", user1_id)
    db_manager.save_cookie("test_cookie_2", "cookie_value_2", user1_id)
    
    # 用户2添加cookies
    db_manager.save_cookie("test_cookie_3", "cookie_value_3", user2_id)
    db_manager.save_cookie("test_cookie_4", "cookie_value_4", user2_id)
    
    # 验证用户1只能看到自己的cookies
    user1_cookies = db_manager.get_all_cookies(user1_id)
    user1_cookie_ids = set(user1_cookies.keys())
    expected_user1_cookies = {"test_cookie_1", "test_cookie_2"}
    
    assert expected_user1_cookies.issubset(user1_cookie_ids), f"用户1应该能看到自己的cookies: {expected_user1_cookies}"
    assert "test_cookie_3" not in user1_cookie_ids, "用户1不应该看到用户2的cookies"
    assert "test_cookie_4" not in user1_cookie_ids, "用户1不应该看到用户2的cookies"
    print("   ✅ 用户1的Cookie隔离正常")
    
    # 验证用户2只能看到自己的cookies
    user2_cookies = db_manager.get_all_cookies(user2_id)
    user2_cookie_ids = set(user2_cookies.keys())
    expected_user2_cookies = {"test_cookie_3", "test_cookie_4"}
    
    assert expected_user2_cookies.issubset(user2_cookie_ids), f"用户2应该能看到自己的cookies: {expected_user2_cookies}"
    assert "test_cookie_1" not in user2_cookie_ids, "用户2不应该看到用户1的cookies"
    assert "test_cookie_2" not in user2_cookie_ids, "用户2不应该看到用户1的cookies"
    print("   ✅ 用户2的Cookie隔离正常")
    
    # 测试关键字隔离
    print("\n3️⃣ 测试关键字数据隔离...")
    
    # 添加关键字
    user1_keywords = [("hello", "user1 reply"), ("price", "user1 price")]
    user2_keywords = [("hello", "user2 reply"), ("info", "user2 info")]
    
    db_manager.save_keywords("test_cookie_1", user1_keywords)
    db_manager.save_keywords("test_cookie_3", user2_keywords)
    
    # 验证关键字隔离
    user1_all_keywords = db_manager.get_all_keywords(user1_id)
    user2_all_keywords = db_manager.get_all_keywords(user2_id)
    
    assert "test_cookie_1" in user1_all_keywords, "用户1应该能看到自己的关键字"
    assert "test_cookie_3" not in user1_all_keywords, "用户1不应该看到用户2的关键字"
    
    assert "test_cookie_3" in user2_all_keywords, "用户2应该能看到自己的关键字"
    assert "test_cookie_1" not in user2_all_keywords, "用户2不应该看到用户1的关键字"
    print("   ✅ 关键字数据隔离正常")
    
    # 测试备份隔离
    print("\n4️⃣ 测试备份数据隔离...")
    
    # 用户1备份
    user1_backup = db_manager.export_backup(user1_id)
    user1_backup_cookies = [row[0] for row in user1_backup['data']['cookies']['rows']]
    
    assert "test_cookie_1" in user1_backup_cookies, "用户1备份应该包含自己的cookies"
    assert "test_cookie_2" in user1_backup_cookies, "用户1备份应该包含自己的cookies"
    assert "test_cookie_3" not in user1_backup_cookies, "用户1备份不应该包含其他用户的cookies"
    assert "test_cookie_4" not in user1_backup_cookies, "用户1备份不应该包含其他用户的cookies"
    print("   ✅ 用户1备份隔离正常")
    
    # 用户2备份
    user2_backup = db_manager.export_backup(user2_id)
    user2_backup_cookies = [row[0] for row in user2_backup['data']['cookies']['rows']]
    
    assert "test_cookie_3" in user2_backup_cookies, "用户2备份应该包含自己的cookies"
    assert "test_cookie_4" in user2_backup_cookies, "用户2备份应该包含自己的cookies"
    assert "test_cookie_1" not in user2_backup_cookies, "用户2备份不应该包含其他用户的cookies"
    assert "test_cookie_2" not in user2_backup_cookies, "用户2备份不应该包含其他用户的cookies"
    print("   ✅ 用户2备份隔离正常")
    
    # 清理测试数据
    print("\n🧹 清理测试数据...")
    db_manager.conn.execute("DELETE FROM keywords WHERE cookie_id LIKE 'test_%'")
    db_manager.conn.execute("DELETE FROM cookies WHERE id LIKE 'test_%'")
    db_manager.conn.execute("DELETE FROM users WHERE username IN (?, ?)", (user1_name, user2_name))
    db_manager.conn.commit()
    print("   ✅ 测试数据清理完成")

async def test_email_sending():
    """测试邮件发送功能（模拟）"""
    print("\n🧪 测试邮件发送功能")
    print("-" * 40)
    
    print("📧 邮件发送功能测试（需要网络连接）")
    print("   注意：这将发送真实的邮件，请确保邮箱地址正确")
    
    test_email = input("请输入测试邮箱地址（回车跳过）: ").strip()
    
    if test_email:
        print(f"   正在发送测试邮件到: {test_email}")
        code = db_manager.generate_verification_code()
        
        try:
            success = await db_manager.send_verification_email(test_email, code)
            if success:
                print("   ✅ 邮件发送成功！请检查邮箱")
            else:
                print("   ❌ 邮件发送失败")
        except Exception as e:
            print(f"   ❌ 邮件发送异常: {e}")
    else:
        print("   ⏭️ 跳过邮件发送测试")

async def main():
    """主测试函数"""
    print("🚀 多用户系统功能测试")
    print("=" * 60)
    
    try:
        # 测试用户注册功能
        await test_user_registration()
        
        # 测试用户数据隔离
        test_user_isolation()
        
        # 测试邮件发送（可选）
        await test_email_sending()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！多用户系统功能正常")
        
        print("\n📋 测试总结:")
        print("✅ 用户注册功能正常")
        print("✅ 邮箱验证码功能正常")
        print("✅ 用户数据隔离正常")
        print("✅ Cookie数据隔离正常")
        print("✅ 关键字数据隔离正常")
        print("✅ 备份数据隔离正常")
        
        print("\n💡 下一步:")
        print("1. 运行迁移脚本: python migrate_to_multiuser.py")
        print("2. 重启应用程序")
        print("3. 访问 /register.html 测试用户注册")
        print("4. 测试多用户登录和数据隔离")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n💥 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(main())

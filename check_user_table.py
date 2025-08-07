#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查用户表结构
"""

import sys
import os
import hashlib

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_manager import db_manager


def check_user_table_structure():
    """检查用户表结构"""
    print("🔍 检查用户表结构")
    print("=" * 50)
    
    try:
        cursor = db_manager.conn.cursor()
        
        # 检查用户表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ users表存在")
            
            # 检查表结构
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            print("users表结构:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'} - {'PRIMARY KEY' if col[5] else ''}")
            
            # 查看表中的数据
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            print(f"\nusers表中共有 {len(users)} 条记录:")
            for i, user in enumerate(users):
                print(f"  记录{i+1}: {user}")
                
        else:
            print("❌ users表不存在")
            
    except Exception as e:
        print(f"❌ 检查用户表失败: {e}")


def fix_user_table():
    """修复用户表"""
    print("\n🔧 修复用户表")
    print("=" * 50)
    
    try:
        cursor = db_manager.conn.cursor()
        
        # 检查是否有is_admin列
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'is_admin' not in column_names:
            print("添加is_admin列...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 1")
            db_manager.conn.commit()
            print("✅ 添加is_admin列成功")
        
        # 检查是否有用户数据
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            print("创建默认管理员用户...")
            username = "admin"
            password = "admin123"
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute("""
                INSERT INTO users (username, password_hash, is_admin) 
                VALUES (?, ?, ?)
            """, (username, password_hash, 1))
            db_manager.conn.commit()
            
            print(f"✅ 创建默认用户成功:")
            print(f"   用户名: {username}")
            print(f"   密码: {password}")
            
            return username, password
        else:
            # 获取第一个用户并重置密码
            cursor.execute("SELECT username FROM users LIMIT 1")
            username = cursor.fetchone()[0]
            password = "admin123"
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute("""
                UPDATE users SET password_hash = ?, is_admin = 1 
                WHERE username = ?
            """, (password_hash, username))
            db_manager.conn.commit()
            
            print(f"✅ 重置用户密码成功:")
            print(f"   用户名: {username}")
            print(f"   密码: {password}")
            
            return username, password
            
    except Exception as e:
        print(f"❌ 修复用户表失败: {e}")
        return None, None


def test_login_after_fix():
    """修复后测试登录"""
    username, password = fix_user_table()
    
    if username and password:
        print(f"\n🌐 测试修复后的登录")
        print("=" * 50)
        
        import requests
        
        try:
            login_data = {
                "username": username,
                "password": password
            }
            response = requests.post("http://localhost:8080/login", json=login_data, timeout=10)
            print(f"登录状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"登录响应: {data}")
                
                if data.get('success'):
                    token = data.get('token') or data.get('access_token')
                    print(f"✅ 登录成功！")
                    
                    if token:
                        print(f"Token: {token[:20]}...")
                        
                        # 测试cookies/details接口
                        headers = {"Authorization": f"Bearer {token}"}
                        response = requests.get("http://localhost:8080/cookies/details", headers=headers, timeout=10)
                        print(f"cookies/details状态码: {response.status_code}")
                        
                        if response.status_code == 200:
                            details = response.json()
                            print(f"✅ 获取到 {len(details)} 个账号详情")
                            
                            if len(details) > 0:
                                print("🎉 账号下拉框应该有数据了！")
                                print("账号列表:")
                                for detail in details:
                                    status = "🟢" if detail['enabled'] else "🔴"
                                    print(f"  {status} {detail['id']}")
                            else:
                                print("⚠️ 账号列表为空，但API接口正常")
                        else:
                            print(f"❌ 获取账号详情失败: {response.text}")
                    else:
                        print("⚠️ 登录成功但没有获取到token")
                else:
                    print(f"❌ 登录失败: {data.get('message', '未知错误')}")
            else:
                print(f"❌ 登录请求失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ 登录测试失败: {e}")


if __name__ == "__main__":
    print("🚀 检查和修复用户表")
    print("=" * 60)
    
    # 检查用户表结构
    check_user_table_structure()
    
    # 修复用户表并测试登录
    test_login_after_fix()
    
    print("\n" + "=" * 60)
    print("🎯 修复完成！")
    print("\n📋 现在可以:")
    print("1. 使用 admin/admin123 登录管理后台")
    print("2. 进入指定商品回复界面")
    print("3. 检查账号下拉框是否有数据")
    print("4. 如果仍然没有数据，请检查浏览器开发者工具")

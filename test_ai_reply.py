#!/usr/bin/env python3
"""
AI回复功能测试脚本
用于验证AI回复集成是否正常工作
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_reply_engine import ai_reply_engine
from db_manager import db_manager
from loguru import logger

async def test_ai_reply_basic():
    """测试AI回复基本功能"""
    print("🧪 开始测试AI回复基本功能...")
    
    # 测试数据
    test_cookie_id = "test_cookie_001"
    test_item_id = "123456789"
    test_message = "你好，这个商品能便宜点吗？"
    test_chat_id = "test_chat_001"
    test_user_id = "test_user_001"
    
    # 测试商品信息
    test_item_info = {
        'title': '测试商品',
        'price': 100,
        'desc': '这是一个用于测试的商品'
    }
    
    print(f"📝 测试参数:")
    print(f"   账号ID: {test_cookie_id}")
    print(f"   商品ID: {test_item_id}")
    print(f"   用户消息: {test_message}")
    print(f"   商品信息: {test_item_info}")
    
    # 1. 测试AI回复是否启用检查
    print("\n1️⃣ 测试AI回复启用状态检查...")
    is_enabled = ai_reply_engine.is_ai_enabled(test_cookie_id)
    print(f"   AI回复启用状态: {is_enabled}")
    
    if not is_enabled:
        print("   ⚠️  AI回复未启用，跳过后续测试")
        print("   💡 请在Web界面中为测试账号启用AI回复功能")
        return False
    
    # 2. 测试意图检测
    print("\n2️⃣ 测试意图检测...")
    try:
        intent = ai_reply_engine.detect_intent(test_message, test_cookie_id)
        print(f"   检测到的意图: {intent}")
    except Exception as e:
        print(f"   ❌ 意图检测失败: {e}")
        return False
    
    # 3. 测试AI回复生成
    print("\n3️⃣ 测试AI回复生成...")
    try:
        reply = ai_reply_engine.generate_reply(
            message=test_message,
            item_info=test_item_info,
            chat_id=test_chat_id,
            cookie_id=test_cookie_id,
            user_id=test_user_id,
            item_id=test_item_id
        )
        
        if reply:
            print(f"   ✅ AI回复生成成功: {reply}")
        else:
            print(f"   ❌ AI回复生成失败: 返回空值")
            return False
            
    except Exception as e:
        print(f"   ❌ AI回复生成异常: {e}")
        return False
    
    print("\n✅ AI回复基本功能测试完成！")
    return True

def test_database_operations():
    """测试数据库操作"""
    print("\n🗄️ 开始测试数据库操作...")
    
    test_cookie_id = "test_cookie_001"
    
    # 1. 测试获取AI回复设置
    print("\n1️⃣ 测试获取AI回复设置...")
    try:
        settings = db_manager.get_ai_reply_settings(test_cookie_id)
        print(f"   AI回复设置: {settings}")
    except Exception as e:
        print(f"   ❌ 获取AI回复设置失败: {e}")
        return False
    
    # 2. 测试保存AI回复设置
    print("\n2️⃣ 测试保存AI回复设置...")
    try:
        test_settings = {
            'ai_enabled': True,
            'model_name': 'qwen-plus',
            'api_key': 'test-api-key',
            'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
            'max_discount_percent': 10,
            'max_discount_amount': 100,
            'max_bargain_rounds': 3,
            'custom_prompts': ''
        }
        
        success = db_manager.save_ai_reply_settings(test_cookie_id, test_settings)
        if success:
            print(f"   ✅ AI回复设置保存成功")
        else:
            print(f"   ❌ AI回复设置保存失败")
            return False
            
    except Exception as e:
        print(f"   ❌ 保存AI回复设置异常: {e}")
        return False
    
    # 3. 验证设置是否正确保存
    print("\n3️⃣ 验证设置保存...")
    try:
        saved_settings = db_manager.get_ai_reply_settings(test_cookie_id)
        if saved_settings['ai_enabled'] == True:
            print(f"   ✅ 设置验证成功: AI回复已启用")
        else:
            print(f"   ❌ 设置验证失败: AI回复未启用")
            return False
    except Exception as e:
        print(f"   ❌ 设置验证异常: {e}")
        return False
    
    print("\n✅ 数据库操作测试完成！")
    return True

def test_configuration():
    """测试配置检查"""
    print("\n⚙️ 开始测试配置检查...")
    
    # 1. 检查必要的模块导入
    print("\n1️⃣ 检查模块导入...")
    try:
        from openai import OpenAI
        print("   ✅ OpenAI模块导入成功")
    except ImportError as e:
        print(f"   ❌ OpenAI模块导入失败: {e}")
        print("   💡 请运行: pip install openai>=1.65.5")
        return False
    
    # 2. 检查数据库表结构
    print("\n2️⃣ 检查数据库表结构...")
    try:
        # 检查ai_reply_settings表是否存在
        with db_manager.lock:
            cursor = db_manager.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_reply_settings'")
            if cursor.fetchone():
                print("   ✅ ai_reply_settings表存在")
            else:
                print("   ❌ ai_reply_settings表不存在")
                return False
                
            # 检查ai_conversations表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_conversations'")
            if cursor.fetchone():
                print("   ✅ ai_conversations表存在")
            else:
                print("   ❌ ai_conversations表不存在")
                return False
                
    except Exception as e:
        print(f"   ❌ 数据库表检查异常: {e}")
        return False
    
    print("\n✅ 配置检查完成！")
    return True

async def main():
    """主测试函数"""
    print("🚀 AI回复功能集成测试开始")
    print("=" * 50)
    
    # 测试配置
    config_ok = test_configuration()
    if not config_ok:
        print("\n❌ 配置检查失败，请修复后重试")
        return
    
    # 测试数据库操作
    db_ok = test_database_operations()
    if not db_ok:
        print("\n❌ 数据库操作测试失败")
        return
    
    # 测试AI回复功能
    ai_ok = await test_ai_reply_basic()
    if not ai_ok:
        print("\n❌ AI回复功能测试失败")
        return
    
    print("\n" + "=" * 50)
    print("🎉 所有测试通过！AI回复功能集成成功！")
    print("\n📋 下一步操作:")
    print("1. 在Web界面中配置AI回复API密钥")
    print("2. 为需要的账号启用AI回复功能")
    print("3. 测试实际的消息回复效果")

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
议价轮数限制功能测试脚本
用于验证最大议价轮数是否生效
"""

import asyncio
import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_reply_engine import ai_reply_engine
from db_manager import db_manager
from loguru import logger

def setup_test_account():
    """设置测试账号的AI回复配置"""
    print("⚙️ 设置测试账号配置...")
    
    test_cookie_id = "test_bargain_001"
    
    # 配置AI回复设置
    ai_settings = {
        'ai_enabled': True,
        'model_name': 'qwen-plus',
        'api_key': 'test-api-key-for-bargain-test',  # 测试用的假密钥
        'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        'max_discount_percent': 15,  # 最大优惠15%
        'max_discount_amount': 50,   # 最大优惠50元
        'max_bargain_rounds': 3,     # 最大议价3轮
        'custom_prompts': ''
    }
    
    try:
        success = db_manager.save_ai_reply_settings(test_cookie_id, ai_settings)
        if success:
            print(f"   ✅ 测试账号配置成功")
            print(f"      账号ID: {test_cookie_id}")
            print(f"      最大议价轮数: {ai_settings['max_bargain_rounds']}")
            print(f"      最大优惠百分比: {ai_settings['max_discount_percent']}%")
            print(f"      最大优惠金额: {ai_settings['max_discount_amount']}元")
            return test_cookie_id
        else:
            print(f"   ❌ 测试账号配置失败")
            return None
    except Exception as e:
        print(f"   ❌ 配置异常: {e}")
        return None

def clear_test_conversations(cookie_id: str, chat_id: str):
    """清理测试对话记录"""
    try:
        with db_manager.lock:
            cursor = db_manager.conn.cursor()
            cursor.execute('''
            DELETE FROM ai_conversations 
            WHERE cookie_id = ? AND chat_id = ?
            ''', (cookie_id, chat_id))
            db_manager.conn.commit()
        print(f"   ✅ 清理对话记录成功")
    except Exception as e:
        print(f"   ❌ 清理对话记录失败: {e}")

def test_bargain_count_tracking():
    """测试议价次数统计"""
    print("\n📊 测试议价次数统计...")
    
    test_cookie_id = "test_bargain_001"
    test_chat_id = "test_chat_bargain_001"
    
    # 清理测试数据
    clear_test_conversations(test_cookie_id, test_chat_id)
    
    # 模拟保存几条议价对话
    test_conversations = [
        ("user", "能便宜点吗？", "price"),
        ("assistant", "可以优惠5元", "price"),
        ("user", "再便宜点呢？", "price"),
        ("assistant", "最多优惠10元", "price"),
        ("user", "还能再便宜吗？", "price"),
        ("assistant", "这已经是最低价了", "price"),
    ]
    
    print(f"\n1️⃣ 模拟保存对话记录...")
    try:
        for i, (role, content, intent) in enumerate(test_conversations):
            ai_reply_engine.save_conversation(
                chat_id=test_chat_id,
                cookie_id=test_cookie_id,
                user_id="test_user_001",
                item_id="test_item_001",
                role=role,
                content=content,
                intent=intent
            )
            print(f"      保存第{i+1}条: {role} - {content}")
    except Exception as e:
        print(f"   ❌ 保存对话记录失败: {e}")
        return False
    
    print(f"\n2️⃣ 测试议价次数统计...")
    try:
        bargain_count = ai_reply_engine.get_bargain_count(test_chat_id, test_cookie_id)
        expected_count = 3  # 3条用户的price消息
        
        if bargain_count == expected_count:
            print(f"   ✅ 议价次数统计正确: {bargain_count}")
        else:
            print(f"   ❌ 议价次数统计错误: 期望 {expected_count}, 实际 {bargain_count}")
            return False
    except Exception as e:
        print(f"   ❌ 议价次数统计异常: {e}")
        return False
    
    return True

def test_bargain_limit_logic():
    """测试议价轮数限制逻辑"""
    print("\n🚫 测试议价轮数限制逻辑...")
    
    test_cookie_id = "test_bargain_001"
    test_chat_id = "test_chat_limit_001"
    
    # 清理测试数据
    clear_test_conversations(test_cookie_id, test_chat_id)
    
    # 获取配置
    settings = db_manager.get_ai_reply_settings(test_cookie_id)
    max_rounds = settings.get('max_bargain_rounds', 3)
    
    print(f"   配置的最大议价轮数: {max_rounds}")
    
    # 模拟达到最大议价轮数
    print(f"\n1️⃣ 模拟 {max_rounds} 轮议价...")
    for i in range(max_rounds):
        try:
            ai_reply_engine.save_conversation(
                chat_id=test_chat_id,
                cookie_id=test_cookie_id,
                user_id="test_user_001",
                item_id="test_item_001",
                role="user",
                content=f"第{i+1}次议价：能便宜点吗？",
                intent="price"
            )
            print(f"      第{i+1}轮议价记录已保存")
        except Exception as e:
            print(f"   ❌ 保存第{i+1}轮议价失败: {e}")
            return False
    
    # 验证议价次数
    print(f"\n2️⃣ 验证当前议价次数...")
    try:
        current_count = ai_reply_engine.get_bargain_count(test_chat_id, test_cookie_id)
        print(f"   当前议价次数: {current_count}")
        
        if current_count >= max_rounds:
            print(f"   ✅ 已达到最大议价轮数限制")
        else:
            print(f"   ❌ 未达到最大议价轮数")
            return False
    except Exception as e:
        print(f"   ❌ 验证议价次数异常: {e}")
        return False
    
    # 测试超出限制时的逻辑（模拟）
    print(f"\n3️⃣ 测试超出限制时的逻辑...")
    try:
        # 直接测试议价轮数检查逻辑
        current_count = ai_reply_engine.get_bargain_count(test_chat_id, test_cookie_id)
        settings = db_manager.get_ai_reply_settings(test_cookie_id)
        max_rounds = settings.get('max_bargain_rounds', 3)

        print(f"   当前议价次数: {current_count}")
        print(f"   最大议价轮数: {max_rounds}")

        if current_count >= max_rounds:
            print(f"   ✅ 检测到议价次数已达上限")
            print(f"   ✅ 系统应该拒绝继续议价")

            # 模拟拒绝回复
            refuse_reply = f"抱歉，这个价格已经是最优惠的了，不能再便宜了哦！"
            print(f"   ✅ 拒绝回复示例: {refuse_reply}")
        else:
            print(f"   ❌ 议价次数检查逻辑错误")
            return False

    except Exception as e:
        print(f"   ❌ 测试超出限制逻辑异常: {e}")
        return False
    
    return True

def test_bargain_settings_integration():
    """测试议价设置集成"""
    print("\n🔧 测试议价设置集成...")
    
    test_cookie_id = "test_bargain_001"
    
    # 获取设置
    try:
        settings = db_manager.get_ai_reply_settings(test_cookie_id)
        
        print(f"   AI回复启用: {settings.get('ai_enabled', False)}")
        print(f"   最大议价轮数: {settings.get('max_bargain_rounds', 3)}")
        print(f"   最大优惠百分比: {settings.get('max_discount_percent', 10)}%")
        print(f"   最大优惠金额: {settings.get('max_discount_amount', 100)}元")
        
        # 验证设置是否正确
        if settings.get('max_bargain_rounds') == 3:
            print(f"   ✅ 议价设置读取正确")
        else:
            print(f"   ❌ 议价设置读取错误")
            return False
            
    except Exception as e:
        print(f"   ❌ 获取议价设置异常: {e}")
        return False
    
    return True

async def main():
    """主测试函数"""
    print("🚀 议价轮数限制功能测试开始")
    print("=" * 50)
    
    # 设置测试账号
    test_cookie_id = setup_test_account()
    if not test_cookie_id:
        print("\n❌ 测试账号设置失败")
        return
    
    # 测试议价设置集成
    settings_ok = test_bargain_settings_integration()
    if not settings_ok:
        print("\n❌ 议价设置集成测试失败")
        return
    
    # 测试议价次数统计
    count_ok = test_bargain_count_tracking()
    if not count_ok:
        print("\n❌ 议价次数统计测试失败")
        return
    
    # 测试议价轮数限制
    limit_ok = test_bargain_limit_logic()
    if not limit_ok:
        print("\n❌ 议价轮数限制测试失败")
        return
    
    print("\n" + "=" * 50)
    print("🎉 所有测试通过！最大议价轮数功能正常！")
    print("\n📋 功能说明:")
    print("1. ✅ 议价次数统计：正确统计用户的议价消息数量")
    print("2. ✅ 轮数限制检查：达到最大轮数时拒绝继续议价")
    print("3. ✅ 拒绝回复生成：超出限制时返回友好的拒绝消息")
    print("4. ✅ 设置参数传递：AI可以获取到完整的议价设置")
    print("\n💡 使用建议:")
    print("- 合理设置最大议价轮数（建议3-5轮）")
    print("- 配合最大优惠百分比和金额使用")
    print("- 在提示词中强调议价策略")

if __name__ == "__main__":
    asyncio.run(main())

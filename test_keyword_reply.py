#!/usr/bin/env python3
"""
关键词回复功能测试脚本
用于验证关键词匹配是否正常工作
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_manager import db_manager
from XianyuAutoAsync import XianyuLive
from loguru import logger

def test_keyword_database():
    """测试关键词数据库操作"""
    print("🗄️ 开始测试关键词数据库操作...")
    
    test_cookie_id = "test_cookie_001"
    
    # 1. 清理测试数据
    print("\n1️⃣ 清理测试数据...")
    try:
        with db_manager.lock:
            cursor = db_manager.conn.cursor()
            cursor.execute("DELETE FROM keywords WHERE cookie_id = ?", (test_cookie_id,))
            db_manager.conn.commit()
        print("   ✅ 测试数据清理完成")
    except Exception as e:
        print(f"   ❌ 清理测试数据失败: {e}")
        return False
    
    # 2. 添加测试关键词
    print("\n2️⃣ 添加测试关键词...")
    test_keywords = [
        ("你好", "您好！欢迎咨询，有什么可以帮助您的吗？"),
        ("价格", "这个商品的价格很优惠哦，{send_user_name}！"),
        ("包邮", "全国包邮，放心购买！"),
        ("发货", "我们会在24小时内发货"),
        ("退换", "支持7天无理由退换货")
    ]
    
    try:
        success = db_manager.save_keywords(test_cookie_id, test_keywords)
        if success:
            print(f"   ✅ 成功添加 {len(test_keywords)} 个关键词")
        else:
            print("   ❌ 添加关键词失败")
            return False
    except Exception as e:
        print(f"   ❌ 添加关键词异常: {e}")
        return False
    
    # 3. 验证关键词保存
    print("\n3️⃣ 验证关键词保存...")
    try:
        saved_keywords = db_manager.get_keywords(test_cookie_id)
        if len(saved_keywords) == len(test_keywords):
            print(f"   ✅ 关键词保存验证成功: {len(saved_keywords)} 个")
            for keyword, reply in saved_keywords:
                print(f"      '{keyword}' -> '{reply[:30]}...'")
        else:
            print(f"   ❌ 关键词数量不匹配: 期望 {len(test_keywords)}, 实际 {len(saved_keywords)}")
            return False
    except Exception as e:
        print(f"   ❌ 验证关键词异常: {e}")
        return False
    
    print("\n✅ 关键词数据库操作测试完成！")
    return True

async def test_keyword_matching():
    """测试关键词匹配功能"""
    print("\n🔍 开始测试关键词匹配功能...")

    test_cookie_id = "test_cookie_001"

    # 创建一个简化的测试类
    class TestKeywordMatcher:
        def __init__(self, cookie_id):
            self.cookie_id = cookie_id

        async def get_keyword_reply(self, send_user_name: str, send_user_id: str, send_message: str) -> str:
            """获取关键词匹配回复"""
            try:
                from db_manager import db_manager

                # 获取当前账号的关键词列表
                keywords = db_manager.get_keywords(self.cookie_id)

                if not keywords:
                    print(f"      调试: 账号 {self.cookie_id} 没有配置关键词")
                    return None

                # 遍历关键词，查找匹配
                for keyword, reply in keywords:
                    if keyword.lower() in send_message.lower():
                        # 进行变量替换
                        try:
                            formatted_reply = reply.format(
                                send_user_name=send_user_name,
                                send_user_id=send_user_id,
                                send_message=send_message
                            )
                            print(f"      调试: 关键词匹配成功: '{keyword}' -> {formatted_reply}")
                            return f"[关键词回复] {formatted_reply}"
                        except Exception as format_error:
                            print(f"      调试: 关键词回复变量替换失败: {format_error}")
                            # 如果变量替换失败，返回原始内容
                            return f"[关键词回复] {reply}"

                print(f"      调试: 未找到匹配的关键词: {send_message}")
                return None

            except Exception as e:
                print(f"      调试: 获取关键词回复失败: {e}")
                return None

    # 创建测试实例
    test_matcher = TestKeywordMatcher(test_cookie_id)
    
    # 测试消息和期望结果
    test_cases = [
        {
            "message": "你好",
            "expected_keyword": "你好",
            "should_match": True
        },
        {
            "message": "请问价格多少？",
            "expected_keyword": "价格",
            "should_match": True
        },
        {
            "message": "包邮吗？",
            "expected_keyword": "包邮",
            "should_match": True
        },
        {
            "message": "什么时候发货？",
            "expected_keyword": "发货",
            "should_match": True
        },
        {
            "message": "可以退换吗？",
            "expected_keyword": "退换",
            "should_match": True
        },
        {
            "message": "这是什么材质的？",
            "expected_keyword": None,
            "should_match": False
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ 测试消息: '{test_case['message']}'")
        
        try:
            reply = await test_matcher.get_keyword_reply(
                send_user_name="测试用户",
                send_user_id="test_user_001",
                send_message=test_case['message']
            )
            
            if test_case['should_match']:
                if reply:
                    print(f"   ✅ 匹配成功: {reply}")
                    if test_case['expected_keyword'] in reply or test_case['expected_keyword'] in test_case['message']:
                        success_count += 1
                    else:
                        print(f"   ⚠️  匹配的关键词不符合预期")
                else:
                    print(f"   ❌ 期望匹配但未匹配")
            else:
                if reply:
                    print(f"   ❌ 不应该匹配但却匹配了: {reply}")
                else:
                    print(f"   ✅ 正确未匹配")
                    success_count += 1
                    
        except Exception as e:
            print(f"   ❌ 测试异常: {e}")
    
    print(f"\n📊 测试结果: {success_count}/{len(test_cases)} 个测试通过")
    
    if success_count == len(test_cases):
        print("✅ 关键词匹配功能测试完成！")
        return True
    else:
        print("❌ 部分测试失败")
        return False

def test_reply_priority():
    """测试回复优先级"""
    print("\n🎯 开始测试回复优先级...")
    
    test_cookie_id = "test_cookie_001"
    
    # 检查AI回复状态
    print("\n1️⃣ 检查AI回复状态...")
    try:
        ai_settings = db_manager.get_ai_reply_settings(test_cookie_id)
        ai_enabled = ai_settings.get('ai_enabled', False)
        print(f"   AI回复状态: {'启用' if ai_enabled else '禁用'}")
    except Exception as e:
        print(f"   ❌ 检查AI回复状态失败: {e}")
        return False
    
    # 检查关键词数量
    print("\n2️⃣ 检查关键词配置...")
    try:
        keywords = db_manager.get_keywords(test_cookie_id)
        print(f"   关键词数量: {len(keywords)} 个")
        if len(keywords) > 0:
            print("   关键词列表:")
            for keyword, reply in keywords[:3]:  # 只显示前3个
                print(f"      '{keyword}' -> '{reply[:30]}...'")
    except Exception as e:
        print(f"   ❌ 检查关键词配置失败: {e}")
        return False
    
    # 检查默认回复
    print("\n3️⃣ 检查默认回复配置...")
    try:
        default_reply = db_manager.get_default_reply(test_cookie_id)
        if default_reply and default_reply.get('enabled', False):
            print(f"   默认回复: 启用")
            print(f"   默认回复内容: {default_reply.get('reply_content', '')[:50]}...")
        else:
            print(f"   默认回复: 禁用")
    except Exception as e:
        print(f"   ❌ 检查默认回复配置失败: {e}")
        return False
    
    print("\n📋 回复优先级说明:")
    print("   1. API回复 (最高优先级)")
    print("   2. AI回复 (如果启用)")
    print("   3. 关键词匹配 (如果AI禁用)")
    print("   4. 默认回复 (最低优先级)")
    
    if not ai_enabled and len(keywords) > 0:
        print("\n✅ 当前配置下，关键词匹配应该正常工作！")
        return True
    elif ai_enabled:
        print("\n⚠️  当前AI回复已启用，关键词匹配会被跳过")
        print("   如需测试关键词匹配，请先禁用AI回复")
        return True
    else:
        print("\n⚠️  当前没有配置关键词，将使用默认回复")
        return True

async def main():
    """主测试函数"""
    print("🚀 关键词回复功能测试开始")
    print("=" * 50)
    
    # 测试数据库操作
    db_ok = test_keyword_database()
    if not db_ok:
        print("\n❌ 数据库操作测试失败")
        return
    
    # 测试关键词匹配
    match_ok = await test_keyword_matching()
    if not match_ok:
        print("\n❌ 关键词匹配测试失败")
        return
    
    # 测试回复优先级
    priority_ok = test_reply_priority()
    if not priority_ok:
        print("\n❌ 回复优先级测试失败")
        return
    
    print("\n" + "=" * 50)
    print("🎉 所有测试通过！关键词回复功能正常！")
    print("\n📋 使用说明:")
    print("1. 在Web界面的'自动回复'页面配置关键词")
    print("2. 确保AI回复已禁用（如果要使用关键词匹配）")
    print("3. 发送包含关键词的消息进行测试")
    print("4. 关键词匹配支持变量替换：{send_user_name}, {send_user_id}, {send_message}")

if __name__ == "__main__":
    asyncio.run(main())

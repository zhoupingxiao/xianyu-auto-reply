#!/usr/bin/env python3
"""
测试令牌过期通知过滤功能
验证正常的令牌过期不会发送通知
"""

import asyncio
import time
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_token_expiry_filter():
    """测试令牌过期通知过滤"""
    print("🧪 测试令牌过期通知过滤功能")
    print("=" * 60)
    
    # 动态导入
    try:
        from XianyuAutoAsync import XianyuLive
        print("✅ 成功导入 XianyuLive")
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return
    
    # 创建测试实例
    test_cookies = "unb=test123; _m_h5_tk=test_token_123456789"
    
    try:
        xianyu = XianyuLive(test_cookies, "test_account")
        print("✅ XianyuLive 实例创建成功")
    except Exception as e:
        print(f"❌ 创建实例失败: {e}")
        return
    
    # Mock外部依赖
    with patch('db_manager.db_manager') as mock_db:
        # 配置数据库mock
        mock_db.get_account_notifications.return_value = [
            {
                'enabled': True,
                'channel_type': 'qq',
                'channel_name': 'Test QQ',
                'channel_config': {'qq_number': '123456', 'api_url': 'http://test.com'}
            }
        ]
        
        # Mock QQ通知发送方法
        xianyu._send_qq_notification = AsyncMock()
        
        print("\n📋 测试用例设计")
        print("-" * 40)
        
        # 测试用例：应该被过滤的错误消息（不发送通知）
        filtered_messages = [
            "Token刷新失败: {'ret': ['FAIL_SYS_TOKEN_EXOIRED::令牌过期']}",
            "Token刷新失败: {'ret': ['FAIL_SYS_TOKEN_EXPIRED::令牌过期']}",
            "Token刷新异常: FAIL_SYS_TOKEN_EXOIRED",
            "Token刷新异常: FAIL_SYS_TOKEN_EXPIRED",
            "Token刷新失败: 令牌过期",
        ]
        
        # 测试用例：不应该被过滤的错误消息（需要发送通知）
        unfiltered_messages = [
            "Token刷新失败: {'ret': ['FAIL_SYS_SESSION_EXPIRED::Session过期']}",
            "Token刷新异常: 网络连接超时",
            "Token刷新失败: Cookie无效",
            "初始化时无法获取有效Token",
            "Token刷新失败: 未知错误"
        ]
        
        print("🚫 应该被过滤的消息（不发送通知）:")
        for i, msg in enumerate(filtered_messages, 1):
            print(f"   {i}. {msg}")
        
        print("\n✅ 不应该被过滤的消息（需要发送通知）:")
        for i, msg in enumerate(unfiltered_messages, 1):
            print(f"   {i}. {msg}")
        
        print("\n" + "=" * 60)
        print("🧪 开始测试")
        
        # 测试1: 验证过滤功能
        print("\n1️⃣ 测试令牌过期消息过滤...")
        
        filtered_count = 0
        for i, message in enumerate(filtered_messages, 1):
            xianyu._send_qq_notification.reset_mock()
            await xianyu.send_token_refresh_notification(message, f"test_filtered_{i}")
            
            if not xianyu._send_qq_notification.called:
                print(f"   ✅ 消息 {i} 被正确过滤")
                filtered_count += 1
            else:
                print(f"   ❌ 消息 {i} 未被过滤（应该被过滤）")
        
        print(f"\n   📊 过滤结果: {filtered_count}/{len(filtered_messages)} 条消息被正确过滤")
        
        # 测试2: 验证非过滤消息正常发送
        print("\n2️⃣ 测试非令牌过期消息正常发送...")
        
        sent_count = 0
        for i, message in enumerate(unfiltered_messages, 1):
            xianyu._send_qq_notification.reset_mock()
            await xianyu.send_token_refresh_notification(message, f"test_unfiltered_{i}")
            
            if xianyu._send_qq_notification.called:
                print(f"   ✅ 消息 {i} 正常发送")
                sent_count += 1
            else:
                print(f"   ❌ 消息 {i} 未发送（应该发送）")
        
        print(f"\n   📊 发送结果: {sent_count}/{len(unfiltered_messages)} 条消息正常发送")
        
        # 测试3: 验证过滤逻辑
        print("\n3️⃣ 测试过滤逻辑详情...")
        
        test_cases = [
            ("FAIL_SYS_TOKEN_EXOIRED::令牌过期", True),
            ("FAIL_SYS_TOKEN_EXPIRED::令牌过期", True),
            ("FAIL_SYS_TOKEN_EXOIRED", True),
            ("FAIL_SYS_TOKEN_EXPIRED", True),
            ("令牌过期", True),
            ("FAIL_SYS_SESSION_EXPIRED::Session过期", False),
            ("网络连接超时", False),
            ("Cookie无效", False),
        ]
        
        for message, should_be_filtered in test_cases:
            is_filtered = xianyu._is_normal_token_expiry(message)
            if is_filtered == should_be_filtered:
                status = "✅ 正确"
            else:
                status = "❌ 错误"
            
            filter_status = "过滤" if is_filtered else "不过滤"
            expected_status = "过滤" if should_be_filtered else "不过滤"
            print(f"   {status} '{message}' -> {filter_status} (期望: {expected_status})")
        
        # 总结
        print("\n" + "=" * 60)
        print("📊 测试总结")
        
        total_filtered = len([msg for msg in filtered_messages if xianyu._is_normal_token_expiry(msg)])
        total_unfiltered = len([msg for msg in unfiltered_messages if not xianyu._is_normal_token_expiry(msg)])
        
        print(f"✅ 令牌过期消息过滤: {total_filtered}/{len(filtered_messages)} 正确")
        print(f"✅ 非令牌过期消息: {total_unfiltered}/{len(unfiltered_messages)} 正确")
        
        if total_filtered == len(filtered_messages) and total_unfiltered == len(unfiltered_messages):
            print("🎉 所有测试通过！令牌过期通知过滤功能正常工作")
        else:
            print("⚠️ 部分测试失败，需要检查过滤逻辑")

def show_filter_explanation():
    """显示过滤机制说明"""
    print("\n\n📋 令牌过期通知过滤机制说明")
    print("=" * 60)
    
    print("🎯 设计目标:")
    print("   • 避免正常的令牌过期发送通知")
    print("   • 令牌过期是正常现象，系统会自动重试")
    print("   • 只有真正的异常才需要通知用户")
    
    print("\n🔍 过滤规则:")
    print("   以下关键词的错误消息将被过滤（不发送通知）:")
    print("   • FAIL_SYS_TOKEN_EXOIRED::令牌过期")
    print("   • FAIL_SYS_TOKEN_EXPIRED::令牌过期")
    print("   • FAIL_SYS_TOKEN_EXOIRED")
    print("   • FAIL_SYS_TOKEN_EXPIRED")
    print("   • 令牌过期")
    
    print("\n✅ 仍会发送通知的情况:")
    print("   • FAIL_SYS_SESSION_EXPIRED::Session过期 (Cookie过期)")
    print("   • 网络连接异常")
    print("   • API调用失败")
    print("   • 其他未知错误")
    
    print("\n💡 优势:")
    print("   • 减少无用通知，避免用户困扰")
    print("   • 保留重要异常通知，便于及时处理")
    print("   • 提升用户体验，通知更有价值")
    
    print("\n🔧 实现方式:")
    print("   • 在发送通知前检查错误消息")
    print("   • 使用关键词匹配识别正常的令牌过期")
    print("   • 记录调试日志，便于问题排查")

if __name__ == "__main__":
    try:
        asyncio.run(test_token_expiry_filter())
        show_filter_explanation()
        
        print("\n" + "=" * 60)
        print("🎊 令牌过期通知过滤测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

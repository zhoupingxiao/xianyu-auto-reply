#!/usr/bin/env python3
"""
测试重复通知修复
验证Token刷新失败时不会发送重复通知
"""

import asyncio
import time
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_duplicate_notification_fix():
    """测试重复通知修复"""
    print("🧪 测试Token刷新失败重复通知修复")
    print("=" * 60)
    
    # 动态导入，避免配置问题
    try:
        from XianyuAutoAsync import XianyuLive
        print("✅ 成功导入 XianyuLive")
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return
    
    # 创建测试用的XianyuLive实例
    test_cookies = "unb=test123; _m_h5_tk=test_token_123456789"
    
    try:
        xianyu = XianyuLive(test_cookies, "test_account")
        print("✅ XianyuLive 实例创建成功")
    except Exception as e:
        print(f"❌ 创建 XianyuLive 实例失败: {e}")
        return
    
    # Mock外部依赖
    with patch('XianyuAutoAsync.db_manager') as mock_db, \
         patch('aiohttp.ClientSession') as mock_session:
        
        # 配置数据库mock
        mock_db.get_account_notifications.return_value = [
            {
                'enabled': True,
                'channel_type': 'qq',
                'channel_name': 'Test QQ',
                'channel_config': {'qq_number': '123456', 'api_url': 'http://test.com'}
            }
        ]
        
        # Mock HTTP session
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"ret": ["FAIL_SYS_SESSION_EXPIRED::Session过期"]}')
        mock_session_instance = AsyncMock()
        mock_session_instance.post.return_value.__aenter__.return_value = mock_response
        mock_session.return_value = mock_session_instance
        xianyu.session = mock_session_instance
        
        # Mock QQ通知发送方法
        xianyu._send_qq_notification = AsyncMock()
        
        print("\n📋 测试场景: Cookie过期导致Token刷新失败")
        print("-" * 40)
        
        # 重置状态
        xianyu.current_token = None
        xianyu.last_token_refresh_time = 0
        xianyu._send_qq_notification.reset_mock()
        
        print("1️⃣ 模拟 init() 方法调用...")
        
        # 创建一个mock websocket
        mock_ws = MagicMock()
        
        try:
            # 调用init方法，这会触发refresh_token，然后检查token
            await xianyu.init(mock_ws)
        except Exception as e:
            print(f"   预期的异常: {e}")
        
        # 检查通知发送次数
        call_count = xianyu._send_qq_notification.call_count
        print(f"\n📊 通知发送统计:")
        print(f"   总调用次数: {call_count}")
        
        if call_count == 1:
            print("   ✅ 成功！只发送了一次通知")
            print("   💡 说明: refresh_token失败后，init不会发送重复通知")
        elif call_count == 2:
            print("   ❌ 失败！发送了两次重复通知")
            print("   🔧 需要进一步优化防重复机制")
        elif call_count == 0:
            print("   ⚠️ 没有发送通知（可能是mock配置问题）")
        else:
            print(f"   ❓ 异常的调用次数: {call_count}")
        
        # 显示调用详情
        if xianyu._send_qq_notification.call_args_list:
            print(f"\n📝 通知调用详情:")
            for i, call in enumerate(xianyu._send_qq_notification.call_args_list, 1):
                args, kwargs = call
                if len(args) >= 2:
                    message = args[1]
                    # 提取关键信息
                    if "异常信息:" in message:
                        error_info = message.split("异常信息:")[1].split("\n")[0].strip()
                        print(f"   第{i}次: {error_info}")
        
        print("\n🔍 防重复机制分析:")
        print("   • 方案1: 时间冷却期 - 5分钟内不重复发送相同类型通知")
        print("   • 方案2: 逻辑判断 - init()检查是否刚刚尝试过refresh_token")
        print("   • 当前使用: 方案2 (更精确，避免逻辑重复)")
        
        print(f"\n⏰ 通知时间记录:")
        for notification_type, last_time in xianyu.last_notification_time.items():
            print(f"   {notification_type}: {time.strftime('%H:%M:%S', time.localtime(last_time))}")

def show_optimization_summary():
    """显示优化总结"""
    print("\n\n📋 优化总结")
    print("=" * 60)
    
    print("🎯 问题描述:")
    print("   用户反馈每次Token刷新异常都会收到两个相同的通知")
    
    print("\n🔍 问题根因:")
    print("   1. refresh_token() 失败时发送第一次通知")
    print("   2. init() 检查 current_token 为空时发送第二次通知")
    print("   3. 两次通知内容基本相同，造成用户困扰")
    
    print("\n🛠️ 解决方案:")
    print("   方案A: 添加通知防重复机制")
    print("     • 为不同场景使用不同的通知类型")
    print("     • 设置5分钟冷却期，避免短时间重复通知")
    print("     • 保留详细的错误信息用于调试")
    
    print("\n   方案B: 优化逻辑判断")
    print("     • 在 init() 中跟踪是否刚刚尝试过 refresh_token")
    print("     • 如果刚刚尝试过且失败，则不发送重复通知")
    print("     • 更精确地避免逻辑重复")
    
    print("\n✅ 实施的优化:")
    print("   • 采用方案A + 方案B的组合")
    print("   • 添加了通知防重复机制（时间冷却）")
    print("   • 优化了 init() 方法的逻辑判断")
    print("   • 为不同错误场景使用不同的通知类型")
    
    print("\n🎉 预期效果:")
    print("   • 用户只会收到一次Token刷新异常通知")
    print("   • 通知内容更加精确，便于问题定位")
    print("   • 避免了通知轰炸，改善用户体验")
    print("   • 保留了完整的错误信息用于调试")

if __name__ == "__main__":
    try:
        asyncio.run(test_duplicate_notification_fix())
        show_optimization_summary()
        
        print("\n" + "=" * 60)
        print("🎊 Token刷新重复通知修复测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

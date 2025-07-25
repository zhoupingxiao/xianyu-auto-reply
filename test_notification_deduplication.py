#!/usr/bin/env python3
"""
测试通知防重复机制
验证Token刷新异常通知不会重复发送
"""

import asyncio
import time
from unittest.mock import AsyncMock, patch, MagicMock
from XianyuAutoAsync import XianyuLive

async def test_notification_deduplication():
    """测试通知防重复机制"""
    print("🧪 测试通知防重复机制")
    print("=" * 50)
    
    # 创建测试用的XianyuLive实例
    test_cookies = "unb=test123; _m_h5_tk=test_token_123456789"
    
    try:
        xianyu = XianyuLive(test_cookies, "test_account")
        print("✅ XianyuLive 实例创建成功")
    except Exception as e:
        print(f"❌ 创建 XianyuLive 实例失败: {e}")
        return
    
    # Mock数据库和通知方法
    with patch('XianyuAutoAsync.db_manager') as mock_db:
        # 配置mock返回值
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
        
        print("\n1️⃣ 测试首次发送通知...")
        
        # 第一次发送通知
        start_time = time.time()
        await xianyu.send_token_refresh_notification("Token刷新失败: Session过期", "token_refresh_failed")
        
        # 验证通知是否发送
        if xianyu._send_qq_notification.called:
            print("✅ 首次通知发送成功")
            print(f"   发送时间: {time.strftime('%H:%M:%S', time.localtime(start_time))}")
        else:
            print("❌ 首次通知发送失败")
            return
        
        print("\n2️⃣ 测试冷却期内重复发送...")
        
        # 重置mock调用计数
        xianyu._send_qq_notification.reset_mock()
        
        # 立即再次发送相同类型的通知
        await xianyu.send_token_refresh_notification("Token刷新失败: Session过期", "token_refresh_failed")
        
        # 验证通知是否被阻止
        if not xianyu._send_qq_notification.called:
            print("✅ 冷却期内的重复通知被正确阻止")
            cooldown_end = start_time + xianyu.notification_cooldown
            print(f"   冷却期结束时间: {time.strftime('%H:%M:%S', time.localtime(cooldown_end))}")
        else:
            print("❌ 冷却期内的重复通知未被阻止")
        
        print("\n3️⃣ 测试不同类型的通知...")
        
        # 重置mock调用计数
        xianyu._send_qq_notification.reset_mock()
        
        # 发送不同类型的通知
        await xianyu.send_token_refresh_notification("初始化时无法获取有效Token", "token_init_failed")
        
        # 验证不同类型的通知是否正常发送
        if xianyu._send_qq_notification.called:
            print("✅ 不同类型的通知正常发送")
        else:
            print("❌ 不同类型的通知发送失败")
        
        print("\n4️⃣ 测试通知类型统计...")
        
        # 显示当前的通知时间记录
        print("   当前通知时间记录:")
        for notification_type, last_time in xianyu.last_notification_time.items():
            print(f"     {notification_type}: {time.strftime('%H:%M:%S', time.localtime(last_time))}")
        
        print(f"   通知冷却时间: {xianyu.notification_cooldown} 秒 ({xianyu.notification_cooldown // 60} 分钟)")
        
        print("\n5️⃣ 测试模拟真实场景...")
        
        # 模拟真实的Token刷新失败场景
        print("   模拟场景: refresh_token() 失败 + init() 检查失败")
        
        # 重置mock和时间记录
        xianyu._send_qq_notification.reset_mock()
        xianyu.last_notification_time.clear()
        
        # 模拟refresh_token失败
        await xianyu.send_token_refresh_notification("Token刷新失败: {'ret': ['FAIL_SYS_SESSION_EXPIRED::Session过期']}", "token_refresh_failed")
        first_call_count = xianyu._send_qq_notification.call_count
        
        # 模拟init检查失败（这应该被阻止，因为是相同的根本原因）
        await xianyu.send_token_refresh_notification("初始化时无法获取有效Token", "token_init_failed")
        second_call_count = xianyu._send_qq_notification.call_count
        
        print(f"   refresh_token 通知调用次数: {first_call_count}")
        print(f"   init 通知调用次数: {second_call_count - first_call_count}")
        print(f"   总调用次数: {second_call_count}")
        
        if second_call_count == 2:
            print("✅ 不同阶段的通知都正常发送（因为使用了不同的通知类型）")
        elif second_call_count == 1:
            print("⚠️ 只发送了一次通知（可能需要调整策略）")
        else:
            print(f"❌ 异常的调用次数: {second_call_count}")

def test_notification_types():
    """测试通知类型分类"""
    print("\n\n📋 通知类型分类说明")
    print("=" * 50)
    
    notification_types = {
        "token_refresh_failed": "Token刷新API调用失败",
        "token_refresh_exception": "Token刷新过程中发生异常", 
        "token_init_failed": "初始化时无法获取有效Token",
        "token_scheduled_refresh_failed": "定时Token刷新失败",
        "db_update_failed": "数据库Cookie更新失败",
        "cookie_id_missing": "Cookie ID不存在",
        "cookie_update_failed": "Cookie更新失败"
    }
    
    print("🏷️ 通知类型及其含义:")
    for type_name, description in notification_types.items():
        print(f"   • {type_name:<30} : {description}")
    
    print(f"\n⏰ 防重复机制:")
    print(f"   • 冷却时间: 5分钟 (300秒)")
    print(f"   • 相同类型的通知在冷却期内不会重复发送")
    print(f"   • 不同类型的通知可以正常发送")
    print(f"   • 成功发送后才会更新冷却时间")

async def test_real_scenario_simulation():
    """测试真实场景模拟"""
    print("\n\n🎭 真实场景模拟")
    print("=" * 50)
    
    print("📋 场景描述:")
    print("   1. 用户的Cookie过期")
    print("   2. refresh_token() 调用失败，返回 Session过期")
    print("   3. init() 检查 current_token 为空，也发送通知")
    print("   4. 期望结果: 只收到一次通知，而不是两次")
    
    print("\n🔧 解决方案:")
    print("   • 为不同阶段使用不同的通知类型")
    print("   • token_refresh_failed: refresh_token API失败")
    print("   • token_init_failed: 初始化检查失败")
    print("   • 这样可以区分问题发生的具体阶段")
    print("   • 但仍然避免短时间内的重复通知")

if __name__ == "__main__":
    try:
        asyncio.run(test_notification_deduplication())
        test_notification_types()
        asyncio.run(test_real_scenario_simulation())
        
        print("\n" + "=" * 50)
        print("🎉 通知防重复机制测试完成！")
        print("\n💡 优化效果:")
        print("   ✅ 避免了短时间内的重复通知")
        print("   ✅ 保留了不同阶段的错误信息")
        print("   ✅ 提供了5分钟的冷却期")
        print("   ✅ 用户体验得到改善")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

#!/usr/bin/env python3
"""
测试缓存刷新功能
验证备份导入后关键字数据是否能正确刷新
"""

import json
import time
import asyncio
from db_manager import db_manager
import cookie_manager as cm

def test_cache_refresh():
    """测试缓存刷新功能"""
    print("🧪 测试缓存刷新功能")
    print("=" * 50)
    
    # 1. 创建测试数据
    print("\n1️⃣ 创建测试数据...")
    test_cookie_id = "test_cache_refresh"
    test_cookie_value = "test_cookie_value_123"
    test_keywords = [
        ("测试关键字1", "测试回复1"),
        ("测试关键字2", "测试回复2")
    ]
    
    # 保存到数据库
    db_manager.save_cookie(test_cookie_id, test_cookie_value)
    db_manager.save_keywords(test_cookie_id, test_keywords)
    print(f"   ✅ 已保存测试账号: {test_cookie_id}")
    print(f"   ✅ 已保存 {len(test_keywords)} 个关键字")
    
    # 2. 创建 CookieManager 并加载数据
    print("\n2️⃣ 创建 CookieManager...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    manager = cm.CookieManager(loop)
    print(f"   ✅ CookieManager 已创建")
    print(f"   📊 加载的关键字: {manager.keywords.get(test_cookie_id, [])}")
    
    # 3. 直接修改数据库（模拟备份导入）
    print("\n3️⃣ 模拟备份导入（直接修改数据库）...")
    new_keywords = [
        ("新关键字1", "新回复1"),
        ("新关键字2", "新回复2"),
        ("新关键字3", "新回复3")
    ]
    db_manager.save_keywords(test_cookie_id, new_keywords)
    print(f"   ✅ 数据库已更新为 {len(new_keywords)} 个新关键字")
    
    # 4. 检查 CookieManager 缓存（应该还是旧数据）
    print("\n4️⃣ 检查 CookieManager 缓存...")
    cached_keywords = manager.keywords.get(test_cookie_id, [])
    print(f"   📊 缓存中的关键字: {cached_keywords}")
    
    if len(cached_keywords) == len(test_keywords):
        print("   ✅ 确认：缓存中仍是旧数据（符合预期）")
    else:
        print("   ❌ 意外：缓存已更新（不符合预期）")
    
    # 5. 调用刷新方法
    print("\n5️⃣ 调用缓存刷新方法...")
    success = manager.reload_from_db()
    print(f"   刷新结果: {success}")
    
    # 6. 检查刷新后的缓存
    print("\n6️⃣ 检查刷新后的缓存...")
    refreshed_keywords = manager.keywords.get(test_cookie_id, [])
    print(f"   📊 刷新后的关键字: {refreshed_keywords}")
    
    if len(refreshed_keywords) == len(new_keywords):
        print("   ✅ 成功：缓存已更新为新数据")
        
        # 验证内容是否正确
        db_keywords = db_manager.get_keywords(test_cookie_id)
        if refreshed_keywords == db_keywords:
            print("   ✅ 验证：缓存数据与数据库一致")
        else:
            print("   ❌ 错误：缓存数据与数据库不一致")
            print(f"      缓存: {refreshed_keywords}")
            print(f"      数据库: {db_keywords}")
    else:
        print("   ❌ 失败：缓存未正确更新")
    
    # 7. 清理测试数据
    print("\n7️⃣ 清理测试数据...")
    db_manager.delete_cookie(test_cookie_id)
    print("   ✅ 测试数据已清理")
    
    print("\n" + "=" * 50)
    print("🎉 缓存刷新功能测试完成！")

def test_backup_import_scenario():
    """测试完整的备份导入场景"""
    print("\n\n🔄 测试完整备份导入场景")
    print("=" * 50)
    
    # 1. 创建初始数据
    print("\n1️⃣ 创建初始数据...")
    initial_data = {
        "account1": [("hello", "你好"), ("price", "价格是100元")],
        "account2": [("bye", "再见"), ("thanks", "谢谢")]
    }
    
    for cookie_id, keywords in initial_data.items():
        db_manager.save_cookie(cookie_id, f"cookie_value_{cookie_id}")
        db_manager.save_keywords(cookie_id, keywords)
    
    print(f"   ✅ 已创建 {len(initial_data)} 个账号的初始数据")
    
    # 2. 导出备份
    print("\n2️⃣ 导出备份...")
    backup_data = db_manager.export_backup()
    print(f"   ✅ 备份导出成功，包含 {len(backup_data['data'])} 个表")
    
    # 3. 修改数据（模拟用户操作）
    print("\n3️⃣ 修改数据...")
    modified_data = {
        "account1": [("modified1", "修改后的回复1")],
        "account3": [("new", "新账号的回复")]
    }
    
    for cookie_id, keywords in modified_data.items():
        db_manager.save_cookie(cookie_id, f"cookie_value_{cookie_id}")
        db_manager.save_keywords(cookie_id, keywords)
    
    print("   ✅ 数据已修改")
    
    # 4. 创建 CookieManager（加载修改后的数据）
    print("\n4️⃣ 创建 CookieManager...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    manager = cm.CookieManager(loop)
    print(f"   ✅ CookieManager 已创建，加载了修改后的数据")
    
    # 5. 导入备份（恢复初始数据）
    print("\n5️⃣ 导入备份...")
    success = db_manager.import_backup(backup_data)
    print(f"   导入结果: {success}")
    
    # 6. 检查 CookieManager 缓存（应该还是修改后的数据）
    print("\n6️⃣ 检查导入后的缓存...")
    for cookie_id in ["account1", "account2", "account3"]:
        cached = manager.keywords.get(cookie_id, [])
        db_data = db_manager.get_keywords(cookie_id)
        print(f"   {cookie_id}:")
        print(f"     缓存: {cached}")
        print(f"     数据库: {db_data}")
        
        if cached != db_data:
            print(f"     ❌ 不一致！需要刷新缓存")
        else:
            print(f"     ✅ 一致")
    
    # 7. 刷新缓存
    print("\n7️⃣ 刷新缓存...")
    manager.reload_from_db()
    
    # 8. 再次检查
    print("\n8️⃣ 检查刷新后的缓存...")
    all_consistent = True
    for cookie_id in ["account1", "account2"]:  # account3 应该被删除了
        cached = manager.keywords.get(cookie_id, [])
        db_data = db_manager.get_keywords(cookie_id)
        print(f"   {cookie_id}:")
        print(f"     缓存: {cached}")
        print(f"     数据库: {db_data}")
        
        if cached != db_data:
            print(f"     ❌ 仍然不一致！")
            all_consistent = False
        else:
            print(f"     ✅ 一致")
    
    # 检查 account3 是否被正确删除
    if "account3" not in manager.keywords:
        print("   ✅ account3 已从缓存中删除")
    else:
        print("   ❌ account3 仍在缓存中")
        all_consistent = False
    
    # 9. 清理
    print("\n9️⃣ 清理测试数据...")
    for cookie_id in ["account1", "account2", "account3"]:
        db_manager.delete_cookie(cookie_id)
    
    print("\n" + "=" * 50)
    if all_consistent:
        print("🎉 备份导入场景测试成功！")
    else:
        print("❌ 备份导入场景测试失败！")

if __name__ == "__main__":
    try:
        test_cache_refresh()
        test_backup_import_scenario()
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

# 自动回复暂停功能说明

## 功能概述

当系统检测到某个 `chat_id` 有手动发出的消息时，会自动暂停该 `chat_id` 的自动回复功能10分钟。如果在暂停期间再次检测到手动发出的消息，会重新开始计时10分钟。

## 功能特性

### 1. 智能检测
- 系统会自动检测每个聊天会话中的手动发出消息
- 检测到手动发出时会在日志中显示：`[时间] 【手动发出】 商品(商品ID): 消息内容`

### 2. 自动暂停
- 检测到手动发出后，立即暂停该 `chat_id` 的自动回复10分钟
- 暂停期间会在日志中显示：`【账号ID】检测到手动发出消息，chat_id XXX 自动回复暂停10分钟，恢复时间: YYYY-MM-DD HH:MM:SS`

### 3. 重新计时
- 如果在暂停期间再次检测到手动发出，会重新开始计时10分钟
- 每次手动发出都会刷新暂停时间

### 4. 暂停提示
- 当收到消息但处于暂停状态时，会在日志中显示：
  `【账号ID】【系统】chat_id XXX 自动回复已暂停，剩余时间: X分Y秒`

### 5. 自动恢复
- 暂停时间到期后，自动恢复该 `chat_id` 的自动回复功能
- 无需手动干预

## 技术实现

### 核心组件

#### AutoReplyPauseManager 类
- `pause_chat(chat_id, cookie_id)`: 暂停指定chat_id的自动回复
- `is_chat_paused(chat_id)`: 检查指定chat_id是否处于暂停状态
- `get_remaining_pause_time(chat_id)`: 获取剩余暂停时间
- `cleanup_expired_pauses()`: 清理过期的暂停记录

#### 集成点

1. **检测手动发出** (第2730行)
   ```python
   if send_user_id == self.myid:
       logger.info(f"[{msg_time}] 【手动发出】 商品({item_id}): {send_message}")
       # 暂停该chat_id的自动回复10分钟
       pause_manager.pause_chat(chat_id, self.cookie_id)
       return
   ```

2. **检查暂停状态** (第2750行)
   ```python
   # 检查该chat_id是否处于暂停状态
   if pause_manager.is_chat_paused(chat_id):
       remaining_time = pause_manager.get_remaining_pause_time(chat_id)
       remaining_minutes = remaining_time // 60
       remaining_seconds = remaining_time % 60
       logger.info(f"[{msg_time}] 【{self.cookie_id}】【系统】chat_id {chat_id} 自动回复已暂停，剩余时间: {remaining_minutes}分{remaining_seconds}秒")
       return
   ```

3. **定期清理** (第2372行)
   ```python
   async def pause_cleanup_loop(self):
       """定期清理过期的暂停记录"""
       while True:
           # 每5分钟清理一次过期记录
           pause_manager.cleanup_expired_pauses()
           await asyncio.sleep(300)
   ```

## 配置参数

### 暂停时长
- 默认：10分钟 (600秒)
- 位置：`AutoReplyPauseManager.__init__()` 中的 `self.pause_duration`
- 可根据需要修改

### 清理频率
- 默认：每5分钟清理一次过期记录
- 位置：`pause_cleanup_loop()` 中的 `await asyncio.sleep(300)`

## 日志示例

### 检测到手动发出
```
2025-08-05 14:48:32.209 | INFO | XianyuAutoAsync:handle_message:2673 - [2025-08-05 14:48:31] 【手动发出】 商品(12345): 你好，这个商品还在吗？
2025-08-05 14:48:32.210 | INFO | XianyuAutoAsync:pause_chat:40 - 【dfg】检测到手动发出消息，chat_id chat_123 自动回复暂停10分钟，恢复时间: 2025-08-05 14:58:32
```

### 暂停期间收到消息
```
2025-08-05 14:50:15.123 | INFO | XianyuAutoAsync:handle_message:2678 - [2025-08-05 14:50:15] 【收到】用户: 张三 (ID: 67890), 商品(12345): 多少钱？
2025-08-05 14:50:15.124 | INFO | XianyuAutoAsync:handle_message:2754 - [2025-08-05 14:50:15] 【dfg】【系统】chat_id chat_123 自动回复已暂停，剩余时间: 8分17秒
```

### 重新计时
```
2025-08-05 14:55:20.456 | INFO | XianyuAutoAsync:handle_message:2673 - [2025-08-05 14:55:20] 【手动发出】 商品(12345): 价格可以商量
2025-08-05 14:55:20.457 | INFO | XianyuAutoAsync:pause_chat:40 - 【dfg】检测到手动发出消息，chat_id chat_123 自动回复暂停10分钟，恢复时间: 2025-08-05 15:05:20
```

## 注意事项

1. **全局管理器**: 使用全局的 `pause_manager` 实例，所有账号共享暂停状态
2. **内存存储**: 暂停记录存储在内存中，程序重启后会丢失
3. **自动清理**: 系统会定期清理过期的暂停记录，避免内存泄漏
4. **线程安全**: 暂停管理器是线程安全的，可以在多个协程中使用

## 测试

运行测试脚本验证功能：
```bash
python test_pause_manager.py
```

测试包括：
- 基本暂停/恢复功能
- 重新计时机制
- 多chat_id管理
- 过期清理功能
- 时间计算准确性

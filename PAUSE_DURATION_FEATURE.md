# 账号自动回复暂停时间配置功能

## 功能概述

为每个账号单独配置自动回复暂停时间，当检测到手动发出消息后，该账号的自动回复会暂停指定的时间长度。

## 功能特性

### 1. 个性化配置
- 每个账号可以单独设置暂停时间（1-60分钟）
- 默认暂停时间为10分钟
- 支持实时修改，立即生效

### 2. 直观界面
- 在账号管理表格中新增"暂停时间"列
- 点击暂停时间可直接编辑
- 带有说明工具提示，解释功能作用

### 3. 智能验证
- 暂停时间范围限制：1-60分钟
- 输入验证和错误提示
- 支持键盘操作（Enter保存，Escape取消）

## 界面展示

### 表格列头
```
账号ID | Cookie值 | 关键词 | 状态 | 默认回复 | AI回复 | 自动确认发货 | 备注 | 暂停时间 | 操作
```

### 暂停时间列
- 显示格式：`🕐 10分钟`
- 工具提示：`检测到手动发出消息后，自动回复暂停的时间长度（分钟）。如果在暂停期间再次手动发出消息，会重新开始计时。`
- 点击可编辑，支持数字输入框

## 技术实现

### 数据库结构
```sql
-- cookies表新增字段
ALTER TABLE cookies ADD COLUMN pause_duration INTEGER DEFAULT 10;
```

### 后端API

#### 1. 更新暂停时间
```http
PUT /cookies/{cid}/pause-duration
Content-Type: application/json
Authorization: Bearer {token}

{
  "pause_duration": 15
}
```

**响应**：
```json
{
  "message": "暂停时间更新成功",
  "pause_duration": 15
}
```

#### 2. 获取暂停时间
```http
GET /cookies/{cid}/pause-duration
Authorization: Bearer {token}
```

**响应**：
```json
{
  "pause_duration": 15,
  "message": "获取暂停时间成功"
}
```

### 前端功能

#### 1. 表格显示
- 在账号列表中显示每个账号的暂停时间
- 默认显示为"🕐 10分钟"格式

#### 2. 内联编辑
```javascript
function editPauseDuration(cookieId, currentDuration) {
    // 创建数字输入框
    // 支持1-60分钟范围
    // Enter保存，Escape取消
    // 实时验证和错误提示
}
```

#### 3. 工具提示
- 使用Bootstrap Tooltip组件
- 自动初始化和重新初始化

### 暂停管理器集成

#### 动态获取暂停时间
```python
def pause_chat(self, chat_id: str, cookie_id: str):
    """暂停指定chat_id的自动回复，使用账号特定的暂停时间"""
    # 获取账号特定的暂停时间
    try:
        from db_manager import db_manager
        pause_minutes = db_manager.get_cookie_pause_duration(cookie_id)
    except Exception as e:
        logger.error(f"获取账号 {cookie_id} 暂停时间失败: {e}，使用默认10分钟")
        pause_minutes = 10
    
    pause_duration_seconds = pause_minutes * 60
    pause_until = time.time() + pause_duration_seconds
    self.paused_chats[chat_id] = pause_until
    
    # 记录日志
    end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(pause_until))
    logger.info(f"【{cookie_id}】检测到手动发出消息，chat_id {chat_id} 自动回复暂停{pause_minutes}分钟，恢复时间: {end_time}")
```

## 使用流程

### 1. 查看当前设置
1. 登录系统，进入账号管理页面
2. 在表格中查看"暂停时间"列
3. 鼠标悬停在列头的问号图标上查看功能说明

### 2. 修改暂停时间
1. 点击要修改的账号的暂停时间（如"🕐 10分钟"）
2. 输入框出现，输入新的暂停时间（1-60分钟）
3. 按Enter键保存，或按Escape键取消
4. 系统显示成功提示

### 3. 验证生效
1. 修改后的设置立即生效
2. 下次该账号检测到手动发出消息时，会使用新的暂停时间
3. 在日志中可以看到使用的暂停时间

## 日志示例

### 使用自定义暂停时间
```
2025-08-05 15:30:15.123 | INFO | XianyuAutoAsync:pause_chat:49 - 【abc123】检测到手动发出消息，chat_id chat_456 自动回复暂停15分钟，恢复时间: 2025-08-05 15:45:15
```

### 获取暂停时间失败时使用默认值
```
2025-08-05 15:30:15.124 | ERROR | XianyuAutoAsync:pause_chat:42 - 获取账号 abc123 暂停时间失败: Database error，使用默认10分钟
2025-08-05 15:30:15.125 | INFO | XianyuAutoAsync:pause_chat:49 - 【abc123】检测到手动发出消息，chat_id chat_456 自动回复暂停10分钟，恢复时间: 2025-08-05 15:40:15
```

## 配置建议

### 不同场景的推荐设置

1. **高频互动商品**：5-10分钟
   - 适用于需要快速响应的热门商品
   - 减少客户等待时间

2. **普通商品**：10-15分钟（默认）
   - 平衡自动化和人工干预
   - 适合大多数场景

3. **低频互动商品**：20-30分钟
   - 适用于不常有咨询的商品
   - 给予更多人工处理时间

4. **特殊商品**：30-60分钟
   - 需要详细沟通的复杂商品
   - 避免自动回复干扰深度交流

## 注意事项

1. **范围限制**：暂停时间必须在1-60分钟之间
2. **立即生效**：修改后的设置立即生效，无需重启
3. **默认值**：新账号默认使用10分钟暂停时间
4. **错误处理**：获取暂停时间失败时自动使用默认10分钟
5. **权限控制**：只能修改自己账号的暂停时间设置

## 兼容性

- **向后兼容**：现有账号自动获得默认10分钟设置
- **数据迁移**：系统启动时自动添加pause_duration字段
- **API兼容**：现有API继续正常工作，新增字段可选

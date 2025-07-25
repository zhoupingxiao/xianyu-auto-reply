# 多用户系统升级指南

## 🎯 功能概述

本次升级将闲鱼自动回复系统从单用户模式升级为多用户模式，实现以下功能：

### ✨ 新增功能

1. **用户注册系统**
   - 邮箱注册，支持验证码验证
   - 用户名唯一性检查
   - 密码安全存储（SHA256哈希）

2. **数据隔离**
   - 每个用户只能看到自己的数据
   - Cookie、关键字、备份等完全隔离
   - 历史数据自动绑定到admin用户

3. **邮箱验证**
   - 集成邮件发送API
   - 6位数字验证码
   - 10分钟有效期
   - 防重复使用

## 🚀 升级步骤

### 1. 备份数据
```bash
# 备份数据库文件
cp xianyu_data.db xianyu_data.db.backup
```

### 2. 运行迁移脚本
```bash
# 迁移历史数据到admin用户
python migrate_to_multiuser.py

# 检查迁移状态
python migrate_to_multiuser.py check
```

### 3. 重启应用
```bash
# 重启应用程序
python Start.py
```

### 4. 验证功能
```bash
# 运行功能测试
python test_multiuser_system.py
```

## 📋 API变更

### 新增接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/register` | POST | 用户注册 |
| `/send-verification-code` | POST | 发送验证码 |
| `/verify` | GET | 验证token（返回用户信息） |

### 修改的接口

所有需要认证的接口现在都支持用户隔离：

- `/cookies` - 只返回当前用户的cookies
- `/cookies/details` - 只返回当前用户的cookie详情
- `/backup/export` - 只导出当前用户的数据
- `/backup/import` - 只导入到当前用户

## 🔐 认证系统

### Token格式变更
```javascript
// 旧格式
SESSION_TOKENS[token] = timestamp

// 新格式
SESSION_TOKENS[token] = {
    user_id: 1,
    username: 'admin',
    timestamp: 1234567890
}
```

### 登录响应变更
```json
{
    "success": true,
    "token": "abc123...",
    "message": "登录成功",
    "user_id": 1
}
```

## 🗄️ 数据库变更

### 新增表

1. **users** - 用户表
   ```sql
   CREATE TABLE users (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       username TEXT UNIQUE NOT NULL,
       email TEXT UNIQUE NOT NULL,
       password_hash TEXT NOT NULL,
       is_active BOOLEAN DEFAULT TRUE,
       created_at REAL NOT NULL,
       updated_at REAL NOT NULL
   );
   ```

2. **email_verifications** - 邮箱验证码表
   ```sql
   CREATE TABLE email_verifications (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       email TEXT NOT NULL,
       code TEXT NOT NULL,
       expires_at REAL NOT NULL,
       used BOOLEAN DEFAULT FALSE,
       created_at REAL DEFAULT (strftime('%s', 'now'))
   );
   ```

### 修改的表

1. **cookies** - 添加user_id字段
   ```sql
   ALTER TABLE cookies ADD COLUMN user_id INTEGER;
   ```

## 🎨 前端变更

### 新增页面

1. **注册页面** (`/register.html`)
   - 用户名、邮箱、密码输入
   - 邮箱验证码发送和验证
   - 表单验证和错误提示
   - 响应式设计

### 修改的页面

1. **登录页面** (`/login.html`)
   - 添加注册链接
   - 保持向后兼容

## 📧 邮件系统

### 邮件API配置
```
API地址: https://dy.zhinianboke.com/api/emailSend
参数:
- subject: 邮件主题
- receiveUser: 收件人邮箱
- sendHtml: 邮件内容(HTML格式)
```

### 邮件模板
- 响应式HTML设计
- 品牌化样式
- 验证码突出显示
- 安全提醒信息

## 🔒 安全特性

1. **密码安全**
   - SHA256哈希存储
   - 不可逆加密

2. **验证码安全**
   - 6位随机数字
   - 10分钟有效期
   - 一次性使用
   - 防暴力破解

3. **数据隔离**
   - 用户级别完全隔离
   - API层面权限检查
   - 数据库层面用户绑定

## 🧪 测试指南

### 功能测试
```bash
# 运行完整测试套件
python test_multiuser_system.py
```

### 手动测试步骤

1. **注册测试**
   - 访问 `/register.html`
   - 输入用户信息
   - 验证邮箱验证码
   - 完成注册

2. **登录测试**
   - 使用新注册的账号登录
   - 验证只能看到自己的数据

3. **数据隔离测试**
   - 创建多个用户账号
   - 分别添加不同的cookies
   - 验证数据完全隔离

## 🐛 故障排除

### 常见问题

1. **迁移失败**
   ```bash
   # 检查数据库文件权限
   ls -la xianyu_data.db
   
   # 检查迁移状态
   python migrate_to_multiuser.py check
   ```

2. **邮件发送失败**
   - 检查网络连接
   - 验证邮箱地址格式
   - 查看应用日志

3. **用户无法登录**
   - 检查用户名和密码
   - 确认用户状态为激活
   - 查看认证日志

### 回滚方案

如果升级出现问题，可以回滚到单用户模式：

1. 恢复数据库备份
   ```bash
   cp xianyu_data.db.backup xianyu_data.db
   ```

2. 使用旧版本代码
3. 重启应用

## 📈 性能影响

- **数据库查询**: 增加了user_id过滤条件，对性能影响微小
- **内存使用**: CookieManager仍加载所有数据，API层面进行过滤
- **响应时间**: 增加了用户验证步骤，延迟增加<10ms

## 🔮 未来规划

1. **用户管理**
   - 管理员用户管理界面
   - 用户权限控制
   - 用户状态管理

2. **高级功能**
   - 用户组和权限
   - 数据共享机制
   - 审计日志

3. **性能优化**
   - 用户级别的CookieManager
   - 数据库索引优化
   - 缓存策略

## 📞 技术支持

如有问题，请：
1. 查看应用日志
2. 运行测试脚本诊断
3. 检查数据库状态
4. 联系技术支持

---

**升级完成后，您的闲鱼自动回复系统将支持多用户使用，每个用户的数据完全隔离，提供更好的安全性和可扩展性！** 🎉

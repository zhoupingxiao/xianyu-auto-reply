# 🤝 贡献指南

感谢您对闲鱼自动回复管理系统的关注！我们欢迎任何形式的贡献，包括但不限于代码、文档、问题反馈和功能建议。

## 📋 贡献方式

### 🐛 报告问题
如果您发现了bug或有改进建议，请：
1. 检查 [Issues](https://github.com/your-repo/xianyu-auto-reply/issues) 确认问题未被报告
2. 创建新的Issue，详细描述问题
3. 提供复现步骤和环境信息
4. 如果可能，提供错误日志和截图

### 💡 功能建议
如果您有新功能的想法：
1. 在Issues中创建功能请求
2. 详细描述功能需求和使用场景
3. 说明功能的预期效果
4. 讨论实现方案的可行性

### 🔧 代码贡献
我们欢迎代码贡献，请遵循以下流程：

#### 开发环境搭建
1. **Fork项目**到您的GitHub账号
2. **克隆项目**到本地：
   ```bash
   git clone https://github.com/your-username/xianyu-auto-reply.git
   cd xianyu-auto-reply
   ```
3. **创建虚拟环境**：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate     # Windows
   ```
4. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```
5. **运行测试**确保环境正常：
   ```bash
   python Start.py
   ```

#### 开发流程
1. **创建分支**：
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **编写代码**，遵循项目的代码规范
3. **编写测试**，确保新功能有相应的测试用例
4. **运行测试**，确保所有测试通过
5. **提交代码**：
   ```bash
   git add .
   git commit -m "feat: 添加新功能描述"
   ```
6. **推送分支**：
   ```bash
   git push origin feature/your-feature-name
   ```
7. **创建Pull Request**

## 📝 代码规范

### Python代码规范
- 遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 代码风格
- 使用有意义的变量和函数名
- 添加必要的注释和文档字符串
- 保持函数简洁，单一职责原则

### 提交信息规范
使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### 提交类型
- `feat`: 新功能
- `fix`: 问题修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

#### 示例
```
feat(ai): 添加智能议价功能

- 实现阶梯式降价策略
- 支持最大优惠限制
- 添加议价轮数统计

Closes #123
```

### 文档规范
- 使用Markdown格式
- 保持文档结构清晰
- 添加必要的代码示例
- 及时更新相关文档

## 🧪 测试指南

### 运行测试
```bash
# 运行所有测试
python -m pytest

# 运行特定测试文件
python -m pytest tests/test_ai_reply.py

# 运行带覆盖率的测试
python -m pytest --cov=.
```

### 编写测试
- 为新功能编写单元测试
- 确保测试覆盖率不低于80%
- 使用有意义的测试名称
- 测试边界条件和异常情况

### 测试示例
```python
def test_ai_reply_with_valid_input():
    """测试AI回复功能的正常输入"""
    # 准备测试数据
    message = "这个商品能便宜点吗？"
    
    # 执行测试
    result = ai_reply_engine.process_message(message)
    
    # 验证结果
    assert result is not None
    assert "优惠" in result
```

## 📚 文档贡献

### 文档类型
- **用户文档**：使用说明、配置指南
- **开发文档**：API文档、架构说明
- **部署文档**：安装部署指南

### 文档更新
- 新功能需要更新相关文档
- 修复文档中的错误和过时信息
- 改进文档的可读性和准确性

## 🔍 代码审查

### 审查标准
- **功能正确性**：代码是否实现了预期功能
- **代码质量**：是否遵循代码规范
- **性能考虑**：是否有性能问题
- **安全性**：是否存在安全隐患
- **测试覆盖**：是否有足够的测试

### 审查流程
1. 提交Pull Request
2. 自动化测试运行
3. 代码审查和讨论
4. 修改和完善
5. 合并到主分支

## 🎯 贡献建议

### 适合新手的任务
- 修复文档中的错误
- 改进错误信息和提示
- 添加单元测试
- 优化用户界面

### 高级贡献
- 新功能开发
- 性能优化
- 架构改进
- 安全增强

## 📞 联系方式

### 获取帮助
- **GitHub Issues**：报告问题和讨论
- **GitHub Discussions**：一般性讨论和问答
- **Email**：紧急问题联系

### 社区参与
- 参与Issue讨论
- 帮助其他用户解决问题
- 分享使用经验和技巧
- 推广项目

## 🏆 贡献者认可

### 贡献者列表
我们会在项目中维护贡献者列表，感谢每一位贡献者的付出。

### 贡献统计
- 代码贡献
- 文档贡献
- 问题报告
- 功能建议

## 📄 许可证

通过贡献代码，您同意您的贡献将在 [MIT License](LICENSE) 下发布。

---

**再次感谢您的贡献！** 🙏

每一个贡献都让这个项目变得更好，无论大小，我们都非常感激。让我们一起构建一个更好的闲鱼自动回复管理系统！

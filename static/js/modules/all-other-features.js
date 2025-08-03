// ==================== 所有其他功能模块 ====================
// 此文件包含原app.js中除已拆分模块外的所有其他功能

// ==================== 默认回复管理功能 ====================

// 打开默认回复管理器
async function openDefaultReplyManager() {
  try {
    await loadDefaultReplies();
    const modal = new bootstrap.Modal(document.getElementById('defaultReplyModal'));
    modal.show();
  } catch (error) {
    console.error('打开默认回复管理器失败:', error);
    showToast('打开默认回复管理器失败', 'danger');
  }
}

// 加载默认回复列表
async function loadDefaultReplies() {
  try {
    // 获取所有账号
    const accountsResponse = await fetch(`${apiBase}/cookies`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    if (!accountsResponse.ok) {
      throw new Error('获取账号列表失败');
    }

    const accounts = await accountsResponse.json();

    // 获取所有默认回复设置
    const repliesResponse = await fetch(`${apiBase}/default-replies`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    let defaultReplies = {};
    if (repliesResponse.ok) {
      defaultReplies = await repliesResponse.json();
    }

    renderDefaultRepliesList(accounts, defaultReplies);
  } catch (error) {
    console.error('加载默认回复列表失败:', error);
    showToast('加载默认回复列表失败', 'danger');
  }
}

// 渲染默认回复列表
function renderDefaultRepliesList(accounts, defaultReplies) {
  const tbody = document.getElementById('defaultReplyTableBody');
  tbody.innerHTML = '';

  if (accounts.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="4" class="text-center py-4 text-muted">
          <i class="bi bi-chat-text fs-1 d-block mb-3"></i>
          <h5>暂无账号数据</h5>
          <p class="mb-0">请先添加账号</p>
        </td>
      </tr>
    `;
    return;
  }

  accounts.forEach(accountId => {
    const replySettings = defaultReplies[accountId] || { enabled: false, reply_content: '' };
    const tr = document.createElement('tr');

    // 状态标签
    const statusBadge = replySettings.enabled ?
      '<span class="badge bg-success">启用</span>' :
      '<span class="badge bg-secondary">禁用</span>';

    // 回复内容预览
    let contentPreview = replySettings.reply_content || '未设置';
    if (contentPreview.length > 50) {
      contentPreview = contentPreview.substring(0, 50) + '...';
    }

    tr.innerHTML = `
      <td>
        <strong class="text-primary">${accountId}</strong>
      </td>
      <td>${statusBadge}</td>
      <td>
        <div class="text-truncate" style="max-width: 300px;" title="${replySettings.reply_content || ''}">
          ${contentPreview}
        </div>
      </td>
      <td>
        <div class="btn-group" role="group">
          <button class="btn btn-sm btn-outline-primary" onclick="editDefaultReply('${accountId}')" title="编辑">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn btn-sm btn-outline-info" onclick="testDefaultReply('${accountId}')" title="测试">
            <i class="bi bi-play"></i>
          </button>
        </div>
      </td>
    `;

    tbody.appendChild(tr);
  });
}

// 编辑默认回复
async function editDefaultReply(accountId) {
  try {
    // 获取当前设置
    const response = await fetch(`${apiBase}/default-replies/${accountId}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    let settings = { enabled: false, reply_content: '' };
    if (response.ok) {
      settings = await response.json();
    }

    // 填充编辑表单
    document.getElementById('editAccountId').value = accountId;
    document.getElementById('editAccountIdDisplay').value = accountId;
    document.getElementById('editDefaultReplyEnabled').checked = settings.enabled;
    document.getElementById('editReplyContent').value = settings.reply_content || '';

    // 根据启用状态显示/隐藏内容输入框
    toggleReplyContentVisibility();

    // 显示编辑模态框
    const modal = new bootstrap.Modal(document.getElementById('editDefaultReplyModal'));
    modal.show();
  } catch (error) {
    console.error('获取默认回复设置失败:', error);
    showToast('获取默认回复设置失败', 'danger');
  }
}

// 切换回复内容输入框的显示/隐藏
function toggleReplyContentVisibility() {
  const enabled = document.getElementById('editDefaultReplyEnabled').checked;
  const contentGroup = document.getElementById('editReplyContentGroup');
  contentGroup.style.display = enabled ? 'block' : 'none';
}

// 保存默认回复设置
async function saveDefaultReply() {
  try {
    const accountId = document.getElementById('editAccountId').value;
    const enabled = document.getElementById('editDefaultReplyEnabled').checked;
    const replyContent = document.getElementById('editReplyContent').value;

    if (enabled && !replyContent.trim()) {
      showToast('启用默认回复时必须设置回复内容', 'warning');
      return;
    }

    const data = {
      enabled: enabled,
      reply_content: enabled ? replyContent : null
    };

    const response = await fetch(`${apiBase}/default-replies/${accountId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    if (response.ok) {
      showToast('默认回复设置保存成功', 'success');
      bootstrap.Modal.getInstance(document.getElementById('editDefaultReplyModal')).hide();
      loadDefaultReplies(); // 刷新列表
      loadCookies(); // 刷新账号列表以更新默认回复状态显示
    } else {
      const error = await response.text();
      showToast(`保存失败: ${error}`, 'danger');
    }
  } catch (error) {
    console.error('保存默认回复设置失败:', error);
    showToast('保存默认回复设置失败', 'danger');
  }
}

// 测试默认回复
function testDefaultReply(accountId) {
    console.log('测试默认回复功能，账号ID:', accountId);
    showToast('测试功能开发中...', 'info');
}

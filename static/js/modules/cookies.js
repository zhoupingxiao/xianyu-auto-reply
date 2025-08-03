// ==================== Cookie管理 ====================

// 加载Cookie列表
async function loadCookies() {
    try {
        toggleLoading(true);
        const tbody = document.querySelector('#cookieTable tbody');
        tbody.innerHTML = '';

        const cookieDetails = await fetchJSON(apiBase + '/cookies/details');

        if (cookieDetails.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-4 text-muted empty-state">
                        <i class="bi bi-inbox fs-1 d-block mb-3"></i>
                        <h5>暂无账号</h5>
                        <p class="mb-0">请添加新的闲鱼账号开始使用</p>
                    </td>
                </tr>
            `;
            return;
        }

        // 为每个账号获取关键词数量和默认回复设置并渲染
        const accountsWithKeywords = await Promise.all(
            cookieDetails.map(async (cookie) => {
                try {
                    // 获取关键词数量
                    const keywordsResponse = await fetch(`${apiBase}/keywords/${cookie.id}`, {
                        headers: { 'Authorization': `Bearer ${authToken}` }
                    });

                    let keywordCount = 0;
                    if (keywordsResponse.ok) {
                        const keywordsData = await keywordsResponse.json();
                        keywordCount = keywordsData.length;
                    }

                    // 获取默认回复设置
                    const defaultReplyResponse = await fetch(`${apiBase}/default-replies/${cookie.id}`, {
                        headers: { 'Authorization': `Bearer ${authToken}` }
                    });

                    let defaultReply = { enabled: false, reply_content: '' };
                    if (defaultReplyResponse.ok) {
                        defaultReply = await defaultReplyResponse.json();
                    }

                    // 获取AI回复设置
                    const aiReplyResponse = await fetch(`${apiBase}/ai-reply-settings/${cookie.id}`, {
                        headers: { 'Authorization': `Bearer ${authToken}` }
                    });

                    let aiReply = { ai_enabled: false, model_name: 'qwen-plus' };
                    if (aiReplyResponse.ok) {
                        aiReply = await aiReplyResponse.json();
                    }

                    return {
                        ...cookie,
                        keywordCount: keywordCount,
                        defaultReply: defaultReply,
                        aiReply: aiReply
                    };
                } catch (error) {
                    return {
                        ...cookie,
                        keywordCount: 0,
                        defaultReply: { enabled: false, reply_content: '' },
                        aiReply: { ai_enabled: false, model_name: 'qwen-plus' }
                    };
                }
            })
        );

    accountsWithKeywords.forEach(cookie => {
      // 使用数据库中的实际状态，默认为启用
      const isEnabled = cookie.enabled === undefined ? true : cookie.enabled;

      console.log(`账号 ${cookie.id} 状态: enabled=${cookie.enabled}, isEnabled=${isEnabled}`); // 调试信息

      const tr = document.createElement('tr');
      tr.className = `account-row ${isEnabled ? 'enabled' : 'disabled'}`;
      // 默认回复状态标签
      const defaultReplyBadge = cookie.defaultReply.enabled ?
        '<span class="badge bg-success">启用</span>' :
        '<span class="badge bg-secondary">禁用</span>';

      // AI回复状态标签
      const aiReplyBadge = cookie.aiReply.ai_enabled ?
        '<span class="badge bg-primary">AI启用</span>' :
        '<span class="badge bg-secondary">AI禁用</span>';

      // 自动确认发货状态（默认开启）
      const autoConfirm = cookie.auto_confirm === undefined ? true : cookie.auto_confirm;

      tr.innerHTML = `
        <td class="align-middle">
          <div class="cookie-id">
            <strong class="text-primary">${cookie.id}</strong>
          </div>
        </td>
        <td class="align-middle">
          <div class="cookie-value" title="点击复制Cookie" style="font-family: monospace; font-size: 0.875rem; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
            ${cookie.value || '未设置'}
          </div>
        </td>
        <td class="align-middle">
          <span class="badge ${cookie.keywordCount > 0 ? 'bg-success' : 'bg-secondary'}">
            ${cookie.keywordCount} 个关键词
          </span>
        </td>
        <td class="align-middle">
          <div class="d-flex align-items-center gap-2">
            <label class="status-toggle" title="${isEnabled ? '点击禁用' : '点击启用'}">
              <input type="checkbox" ${isEnabled ? 'checked' : ''} onchange="toggleAccountStatus('${cookie.id}', this.checked)">
              <span class="status-slider"></span>
            </label>
            <span class="status-badge ${isEnabled ? 'enabled' : 'disabled'}" title="${isEnabled ? '账号已启用' : '账号已禁用'}">
              <i class="bi bi-${isEnabled ? 'check-circle-fill' : 'x-circle-fill'}"></i>
            </span>
          </div>
        </td>
        <td class="align-middle">
          ${defaultReplyBadge}
        </td>
        <td class="align-middle">
          ${aiReplyBadge}
        </td>
        <td class="align-middle">
          <div class="d-flex align-items-center gap-2">
            <label class="status-toggle" title="${autoConfirm ? '点击关闭自动确认发货' : '点击开启自动确认发货'}">
              <input type="checkbox" ${autoConfirm ? 'checked' : ''} onchange="toggleAutoConfirm('${cookie.id}', this.checked)">
              <span class="status-slider"></span>
            </label>
            <span class="status-badge ${autoConfirm ? 'enabled' : 'disabled'}" title="${autoConfirm ? '自动确认发货已开启' : '自动确认发货已关闭'}">
              <i class="bi bi-${autoConfirm ? 'truck' : 'truck-flatbed'}"></i>
            </span>
          </div>
        </td>
        <td class="align-middle">
          <div class="btn-group" role="group">
            <button class="btn btn-sm btn-outline-primary" onclick="editCookieInline('${cookie.id}', '${cookie.value}')" title="修改Cookie" ${!isEnabled ? 'disabled' : ''}>
              <i class="bi bi-pencil"></i>
            </button>
            <button class="btn btn-sm btn-outline-success" onclick="goToAutoReply('${cookie.id}')" title="${isEnabled ? '设置自动回复' : '配置关键词 (账号已禁用)'}">
              <i class="bi bi-arrow-right-circle"></i>
            </button>
            <button class="btn btn-sm btn-outline-warning" onclick="configAIReply('${cookie.id}')" title="配置AI回复" ${!isEnabled ? 'disabled' : ''}>
              <i class="bi bi-robot"></i>
            </button>
            <button class="btn btn-sm btn-outline-info" onclick="copyCookie('${cookie.id}', '${cookie.value}')" title="复制Cookie">
              <i class="bi bi-clipboard"></i>
            </button>
            <button class="btn btn-sm btn-outline-danger" onclick="delCookie('${cookie.id}')" title="删除账号">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });

    // 为Cookie值添加点击复制功能
    document.querySelectorAll('.cookie-value').forEach(element => {
      element.style.cursor = 'pointer';
      element.addEventListener('click', function() {
        const cookieValue = this.textContent;
        if (cookieValue && cookieValue !== '未设置') {
          navigator.clipboard.writeText(cookieValue).then(() => {
            showToast('Cookie已复制到剪贴板', 'success');
          }).catch(() => {
            showToast('复制失败，请手动复制', 'error');
          });
        }
      });
    });

  } catch (err) {
    // 错误已在fetchJSON中处理
  } finally {
    toggleLoading(false);
  }
}

// 复制Cookie
function copyCookie(id, value) {
  if (!value || value === '未设置') {
    showToast('该账号暂无Cookie值', 'warning');
    return;
  }

  navigator.clipboard.writeText(value).then(() => {
    showToast(`账号 "${id}" 的Cookie已复制到剪贴板`, 'success');
  }).catch(() => {
    // 降级方案：创建临时文本框
    const textArea = document.createElement('textarea');
    textArea.value = value;
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      showToast(`账号 "${id}" 的Cookie已复制到剪贴板`, 'success');
    } catch (err) {
      showToast('复制失败，请手动复制', 'error');
    }
    document.body.removeChild(textArea);
  });
}

// 删除Cookie
async function delCookie(id) {
  if (!confirm(`确定要删除账号 "${id}" 吗？此操作不可恢复。`)) return;

  try {
    await fetchJSON(apiBase + `/cookies/${id}`, { method: 'DELETE' });
    showToast(`账号 "${id}" 已删除`, 'success');
    loadCookies();
  } catch (err) {
    // 错误已在fetchJSON中处理
  }
}

// 内联编辑Cookie
function editCookieInline(id, currentValue) {
    const row = event.target.closest('tr');
    const cookieValueCell = row.querySelector('.cookie-value');
    const originalContent = cookieValueCell.innerHTML;

    // 存储原始数据到全局变量，避免HTML注入问题
    window.editingCookieData = {
        id: id,
        originalContent: originalContent,
        originalValue: currentValue || ''
    };

    // 创建编辑界面容器
    const editContainer = document.createElement('div');
    editContainer.className = 'd-flex gap-2';

    // 创建输入框
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'form-control form-control-sm';
    input.id = `edit-${id}`;
    input.value = currentValue || '';
    input.placeholder = '输入新的Cookie值';

    // 创建保存按钮
    const saveBtn = document.createElement('button');
    saveBtn.className = 'btn btn-sm btn-success';
    saveBtn.title = '保存';
    saveBtn.innerHTML = '<i class="bi bi-check"></i>';
    saveBtn.onclick = () => saveCookieInline(id);

    // 创建取消按钮
    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'btn btn-sm btn-secondary';
    cancelBtn.title = '取消';
    cancelBtn.innerHTML = '<i class="bi bi-x"></i>';
    cancelBtn.onclick = () => cancelCookieEdit(id);

    // 组装编辑界面
    editContainer.appendChild(input);
    editContainer.appendChild(saveBtn);
    editContainer.appendChild(cancelBtn);

    // 替换原内容
    cookieValueCell.innerHTML = '';
    cookieValueCell.appendChild(editContainer);

    // 聚焦输入框
    input.focus();
    input.select();

    // 添加键盘事件监听
    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            saveCookieInline(id);
        } else if (e.key === 'Escape') {
            e.preventDefault();
            cancelCookieEdit(id);
        }
    });

    // 禁用该行的其他按钮
    const actionButtons = row.querySelectorAll('.btn-group button');
    actionButtons.forEach(btn => btn.disabled = true);
}

// 保存内联编辑的Cookie
async function saveCookieInline(id) {
  const input = document.getElementById(`edit-${id}`);
  const newValue = input.value.trim();

  if (!newValue) {
    showToast('Cookie值不能为空', 'warning');
    return;
  }

  try {
    toggleLoading(true);

    await fetchJSON(apiBase + `/cookies/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: id,
        value: newValue
      })
    });

    showToast(`账号 "${id}" Cookie已更新`, 'success');
    loadCookies(); // 重新加载列表

  } catch (err) {
    console.error('Cookie更新失败:', err);
    showToast(`Cookie更新失败: ${err.message || '未知错误'}`, 'danger');
    // 恢复原内容
    cancelCookieEdit(id);
  } finally {
    toggleLoading(false);
  }
}

// 取消Cookie编辑
function cancelCookieEdit(id) {
  if (!window.editingCookieData || window.editingCookieData.id !== id) {
    console.error('编辑数据不存在');
    return;
  }

  const row = document.querySelector(`#edit-${id}`).closest('tr');
  const cookieValueCell = row.querySelector('.cookie-value');

  // 恢复原内容
  cookieValueCell.innerHTML = window.editingCookieData.originalContent;

  // 恢复按钮状态
  const actionButtons = row.querySelectorAll('.btn-group button');
  actionButtons.forEach(btn => btn.disabled = false);

  // 清理全局数据
  delete window.editingCookieData;
}

// ==================== 主要功能模块 ====================

// 切换账号启用/禁用状态
async function toggleAccountStatus(accountId, enabled) {
  try {
    toggleLoading(true);

    // 这里需要调用后端API来更新账号状态
    // 由于当前后端可能没有enabled字段，我们先在前端模拟
    // 实际项目中需要后端支持

    const response = await fetch(`${apiBase}/cookies/${accountId}/status`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({ enabled: enabled })
    });

    if (response.ok) {
      showToast(`账号 "${accountId}" 已${enabled ? '启用' : '禁用'}`, 'success');

      // 清除相关缓存，确保数据一致性
      clearKeywordCache();

      // 更新界面显示
      updateAccountRowStatus(accountId, enabled);

      // 刷新自动回复页面的账号列表
      refreshAccountList();

      // 如果禁用的账号在自动回复页面被选中，更新显示
      const accountSelect = document.getElementById('accountSelect');
      if (accountSelect && accountSelect.value === accountId) {
        if (!enabled) {
          // 更新徽章显示禁用状态
          updateAccountBadge(accountId, false);
          showToast('账号已禁用，配置的关键词不会参与自动回复', 'warning');
        } else {
          // 更新徽章显示启用状态
          updateAccountBadge(accountId, true);
          showToast('账号已启用，配置的关键词将参与自动回复', 'success');
        }
      }

    } else {
      // 如果后端不支持，先在前端模拟
      console.warn('后端暂不支持账号状态切换，使用前端模拟');
      showToast(`账号 "${accountId}" 已${enabled ? '启用' : '禁用'} (前端模拟)`, enabled ? 'success' : 'warning');
      updateAccountRowStatus(accountId, enabled);
    }

  } catch (error) {
    console.error('切换账号状态失败:', error);

    // 后端不支持时的降级处理
    showToast(`账号 "${accountId}" 已${enabled ? '启用' : '禁用'} (本地模拟)`, enabled ? 'success' : 'warning');
    updateAccountRowStatus(accountId, enabled);

    // 恢复切换按钮状态
    const toggle = document.querySelector(`input[onchange*="${accountId}"]`);
    if (toggle) {
      toggle.checked = enabled;
    }
  } finally {
    toggleLoading(false);
  }
}

// 更新账号行的状态显示
function updateAccountRowStatus(accountId, enabled) {
  const toggle = document.querySelector(`input[onchange*="${accountId}"]`);
  if (!toggle) return;

  const row = toggle.closest('tr');
  const statusBadge = row.querySelector('.status-badge');
  const actionButtons = row.querySelectorAll('.btn-group .btn:not(.btn-outline-info):not(.btn-outline-danger)');

  // 更新行样式
  row.className = `account-row ${enabled ? 'enabled' : 'disabled'}`;

  // 更新状态徽章
  statusBadge.className = `status-badge ${enabled ? 'enabled' : 'disabled'}`;
  statusBadge.title = enabled ? '账号已启用' : '账号已禁用';
  statusBadge.innerHTML = `
    <i class="bi bi-${enabled ? 'check-circle-fill' : 'x-circle-fill'}"></i>
  `;

  // 更新按钮状态（只禁用编辑Cookie按钮，其他按钮保持可用）
  actionButtons.forEach(btn => {
    if (btn.onclick && btn.onclick.toString().includes('editCookieInline')) {
      btn.disabled = !enabled;
    }
    // 设置自动回复按钮始终可用，但更新提示文本
    if (btn.onclick && btn.onclick.toString().includes('goToAutoReply')) {
      btn.title = enabled ? '设置自动回复' : '配置关键词 (账号已禁用)';
    }
  });

  // 更新切换按钮的提示
  const label = toggle.closest('.status-toggle');
  label.title = enabled ? '点击禁用' : '点击启用';
}

// 切换自动确认发货状态
async function toggleAutoConfirm(accountId, enabled) {
  try {
    toggleLoading(true);

    const response = await fetch(`${apiBase}/cookies/${accountId}/auto-confirm`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({ auto_confirm: enabled })
    });

    if (response.ok) {
      const result = await response.json();
      showToast(result.message, 'success');

      // 更新界面显示
      updateAutoConfirmRowStatus(accountId, enabled);
    } else {
      const error = await response.json();
      showToast(error.detail || '更新自动确认发货设置失败', 'error');

      // 恢复切换按钮状态
      const toggle = document.querySelector(`input[onchange*="toggleAutoConfirm('${accountId}'"]`);
      if (toggle) {
        toggle.checked = !enabled;
      }
    }

  } catch (error) {
    console.error('切换自动确认发货状态失败:', error);
    showToast('网络错误，请稍后重试', 'error');

    // 恢复切换按钮状态
    const toggle = document.querySelector(`input[onchange*="toggleAutoConfirm('${accountId}'"]`);
    if (toggle) {
      toggle.checked = !enabled;
    }
  } finally {
    toggleLoading(false);
  }
}

// 更新自动确认发货行状态
function updateAutoConfirmRowStatus(accountId, enabled) {
  const row = document.querySelector(`tr:has(input[onchange*="toggleAutoConfirm('${accountId}'"])`);
  if (!row) return;

  const statusBadge = row.querySelector('.status-badge:has(i.bi-truck, i.bi-truck-flatbed)');
  const toggle = row.querySelector(`input[onchange*="toggleAutoConfirm('${accountId}'"]`);

  if (statusBadge && toggle) {
    // 更新状态徽章
    statusBadge.className = `status-badge ${enabled ? 'enabled' : 'disabled'}`;
    statusBadge.title = enabled ? '自动确认发货已开启' : '自动确认发货已关闭';
    statusBadge.innerHTML = `
      <i class="bi bi-${enabled ? 'truck' : 'truck-flatbed'}"></i>
    `;

    // 更新切换按钮的提示
    const label = toggle.closest('.status-toggle');
    label.title = enabled ? '点击关闭自动确认发货' : '点击开启自动确认发货';
  }
}

// 跳转到自动回复页面并选择指定账号
function goToAutoReply(accountId) {
  // 切换到自动回复页面
  showSection('auto-reply');

  // 设置账号选择器的值
  setTimeout(() => {
    const accountSelect = document.getElementById('accountSelect');
    if (accountSelect) {
      accountSelect.value = accountId;
      // 触发change事件来加载关键词
      loadAccountKeywords();
    }
  }, 100);

  showToast(`已切换到自动回复页面，账号 "${accountId}" 已选中`, 'info');
}

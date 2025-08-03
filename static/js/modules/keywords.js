// ==================== 关键词管理 ====================

// 加载账号关键词
async function loadAccountKeywords() {
  const accountId = document.getElementById('accountSelect').value;
  const keywordManagement = document.getElementById('keywordManagement');

  if (!accountId) {
    keywordManagement.style.display = 'none';
    return;
  }

  try {
    toggleLoading(true);
    currentCookieId = accountId;

    // 获取账号详情以检查状态
    const accountResponse = await fetch(`${apiBase}/cookies/details`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    let accountStatus = true; // 默认启用
    if (accountResponse.ok) {
      const accounts = await accountResponse.json();
      const currentAccount = accounts.find(acc => acc.id === accountId);
      accountStatus = currentAccount ? (currentAccount.enabled === undefined ? true : currentAccount.enabled) : true;
      console.log(`加载关键词时账号 ${accountId} 状态: enabled=${currentAccount?.enabled}, accountStatus=${accountStatus}`); // 调试信息
    }

    const response = await fetch(`${apiBase}/keywords-with-item-id/${accountId}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    if (response.ok) {
      const data = await response.json();
      console.log('从服务器获取的关键词数据:', data); // 调试信息

      // 后端返回的是 [{keyword, reply, item_id}, ...] 格式，直接使用
      const formattedData = data;

      console.log('格式化后的关键词数据:', formattedData); // 调试信息
      keywordsData[accountId] = formattedData;
      renderKeywordsList(formattedData);

      // 加载商品列表
      await loadItemsList(accountId);

      // 更新账号徽章显示
      updateAccountBadge(accountId, accountStatus);

      keywordManagement.style.display = 'block';
    } else {
      showToast('加载关键词失败', 'danger');
    }
  } catch (error) {
    console.error('加载关键词失败:', error);
    showToast('加载关键词失败', 'danger');
  } finally {
    toggleLoading(false);
  }
}

// 更新账号徽章显示
function updateAccountBadge(accountId, isEnabled) {
  const badge = document.getElementById('currentAccountBadge');
  if (!badge) return;

  const statusIcon = isEnabled ? '🟢' : '🔴';
  const statusText = isEnabled ? '启用' : '禁用';
  const statusClass = isEnabled ? 'bg-success' : 'bg-warning';

  badge.innerHTML = `
    <span class="badge ${statusClass} me-2">
      ${statusIcon} ${accountId}
    </span>
    <small class="text-muted">
      状态: ${statusText}
      ${!isEnabled ? ' (配置的关键词不会参与自动回复)' : ''}
    </small>
  `;
}

// 显示添加关键词表单
function showAddKeywordForm() {
  const form = document.getElementById('addKeywordForm');
  form.style.display = form.style.display === 'none' ? 'block' : 'none';

  if (form.style.display === 'block') {
    document.getElementById('newKeyword').focus();
  }
}

// 加载商品列表
async function loadItemsList(accountId) {
  try {
    const response = await fetch(`${apiBase}/items/${accountId}`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    if (response.ok) {
      const data = await response.json();
      const items = data.items || [];

      // 更新商品选择下拉框
      const selectElement = document.getElementById('newItemIdSelect');
      if (selectElement) {
        // 清空现有选项（保留第一个默认选项）
        selectElement.innerHTML = '<option value="">选择商品或留空表示通用关键词</option>';

        // 添加商品选项
        items.forEach(item => {
          const option = document.createElement('option');
          option.value = item.item_id;
          option.textContent = `${item.item_id} - ${item.item_title}`;
          selectElement.appendChild(option);
        });
      }

      console.log(`加载了 ${items.length} 个商品到选择列表`);
    } else {
      console.warn('加载商品列表失败:', response.status);
    }
  } catch (error) {
    console.error('加载商品列表时发生错误:', error);
  }
}

// 添加或更新关键词
async function addKeyword() {
  const keyword = document.getElementById('newKeyword').value.trim();
  const reply = document.getElementById('newReply').value.trim();
  const itemId = document.getElementById('newItemIdSelect').value.trim();

  if (!keyword || !reply) {
    showToast('请填写关键词和回复内容', 'warning');
    return;
  }

  if (!currentCookieId) {
    showToast('请先选择账号', 'warning');
    return;
  }

  // 检查是否为编辑模式
  const isEditMode = typeof window.editingIndex !== 'undefined';
  const actionText = isEditMode ? '更新' : '添加';

  try {
    toggleLoading(true);

    // 获取当前关键词列表
    let currentKeywords = [...(keywordsData[currentCookieId] || [])];

    // 如果是编辑模式，先移除原关键词
    if (isEditMode) {
      currentKeywords.splice(window.editingIndex, 1);
    }

    // 准备要保存的关键词列表
    let keywordsToSave = [...currentKeywords];

    // 如果是编辑模式，先移除原关键词
    if (isEditMode && typeof window.editingIndex !== 'undefined') {
      keywordsToSave.splice(window.editingIndex, 1);
    }

    // 检查关键词是否已存在（考虑商品ID）
    const existingKeyword = keywordsToSave.find(item =>
      item.keyword === keyword &&
      (item.item_id || '') === (itemId || '')
    );
    if (existingKeyword) {
      const itemIdText = itemId ? `（商品ID: ${itemId}）` : '（通用关键词）';
      showToast(`关键词 "${keyword}" ${itemIdText} 已存在，请使用其他关键词或商品ID`, 'warning');
      toggleLoading(false);
      return;
    }

    // 添加新关键词或更新的关键词
    const newKeyword = {
      keyword: keyword,
      reply: reply,
      item_id: itemId || ''
    };
    keywordsToSave.push(newKeyword);

    const response = await fetch(`${apiBase}/keywords-with-item-id/${currentCookieId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({
        keywords: keywordsToSave
      })
    });

    if (response.ok) {
      showToast(`✨ 关键词 "${keyword}" ${actionText}成功！`, 'success');

      // 清空输入框并重置样式
      const keywordInput = document.getElementById('newKeyword');
      const replyInput = document.getElementById('newReply');
      const selectElement = document.getElementById('newItemIdSelect');
      const addBtn = document.querySelector('.add-btn');

      keywordInput.value = '';
      replyInput.value = '';
      if (selectElement) {
        selectElement.value = '';
      }
      keywordInput.style.borderColor = '#e5e7eb';
      replyInput.style.borderColor = '#e5e7eb';
      addBtn.style.opacity = '0.7';
      addBtn.style.transform = 'scale(0.95)';

      // 如果是编辑模式，重置编辑状态
      if (isEditMode) {
        delete window.editingIndex;
        delete window.originalKeyword;

        // 恢复添加按钮
        addBtn.innerHTML = '<i class="bi bi-plus-lg"></i>添加';
        addBtn.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';

        // 移除取消按钮
        const cancelBtn = document.getElementById('cancelEditBtn');
        if (cancelBtn) {
          cancelBtn.remove();
        }
      }

      // 聚焦到关键词输入框，方便连续添加
      setTimeout(() => {
        keywordInput.focus();
      }, 100);

      loadAccountKeywords(); // 重新加载关键词列表
      clearKeywordCache(); // 清除缓存
    } else {
      const errorText = await response.text();
      console.error('关键词添加失败:', errorText);
      showToast('关键词添加失败', 'danger');
    }
  } catch (error) {
    console.error('添加关键词失败:', error);
    showToast('添加关键词失败', 'danger');
  } finally {
    toggleLoading(false);
  }
}

// 渲染现代化关键词列表
function renderKeywordsList(keywords) {
  console.log('渲染关键词列表:', keywords); // 调试信息
  const container = document.getElementById('keywordsList');

  if (!container) {
    console.error('找不到关键词列表容器元素');
    return;
  }

  container.innerHTML = '';

  if (!keywords || keywords.length === 0) {
    console.log('关键词列表为空，显示空状态');
    container.innerHTML = `
      <div class="empty-state">
        <i class="bi bi-chat-dots"></i>
        <h3>还没有关键词</h3>
        <p>添加第一个关键词，让您的闲鱼店铺自动回复客户消息</p>
        <button class="quick-add-btn" onclick="focusKeywordInput()">
          <i class="bi bi-plus-lg me-2"></i>立即添加
        </button>
      </div>
    `;
    return;
  }

  console.log(`开始渲染 ${keywords.length} 个关键词`);

  keywords.forEach((item, index) => {
    console.log(`渲染关键词 ${index + 1}:`, item); // 调试信息

    const keywordItem = document.createElement('div');
    keywordItem.className = 'keyword-item';
    // 商品ID显示
    const itemIdDisplay = item.item_id ?
      `<small class="text-muted d-block"><i class="bi bi-box"></i> 商品ID: ${item.item_id}</small>` :
      '<small class="text-muted d-block"><i class="bi bi-globe"></i> 通用关键词</small>';

    keywordItem.innerHTML = `
      <div class="keyword-item-header">
        <div class="keyword-tag">
          <i class="bi bi-tag-fill"></i>
          ${item.keyword}
          ${itemIdDisplay}
        </div>
        <div class="keyword-actions">
          <button class="action-btn edit-btn" onclick="editKeyword(${index})" title="编辑">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="action-btn delete-btn" onclick="deleteKeyword('${currentCookieId}', ${index})" title="删除">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </div>
      <div class="keyword-content">
        <p class="reply-text">${item.reply}</p>
      </div>
    `;
    container.appendChild(keywordItem);
  });

  console.log('关键词列表渲染完成');
}

// 聚焦到关键词输入框
function focusKeywordInput() {
  document.getElementById('newKeyword').focus();
}

// 编辑关键词 - 改进版本
function editKeyword(index) {
  const keywords = keywordsData[currentCookieId] || [];
  const keyword = keywords[index];

  if (!keyword) {
    showToast('关键词不存在', 'warning');
    return;
  }

  // 将关键词信息填入输入框
  document.getElementById('newKeyword').value = keyword.keyword;
  document.getElementById('newReply').value = keyword.reply;

  // 设置商品ID选择框
  const selectElement = document.getElementById('newItemIdSelect');
  if (selectElement) {
    selectElement.value = keyword.item_id || '';
  }

  // 设置编辑模式标识
  window.editingIndex = index;
  window.originalKeyword = keyword.keyword;
  window.originalItemId = keyword.item_id || '';

  // 更新按钮文本和样式
  const addBtn = document.querySelector('.add-btn');
  addBtn.innerHTML = '<i class="bi bi-check-lg"></i>更新';
  addBtn.style.background = 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)';

  // 显示取消按钮
  showCancelEditButton();

  // 聚焦到关键词输入框并选中文本
  setTimeout(() => {
    const keywordInput = document.getElementById('newKeyword');
    keywordInput.focus();
    keywordInput.select();
  }, 100);

  showToast('📝 编辑模式：修改后点击"更新"按钮保存', 'info');
}

// 显示取消编辑按钮
function showCancelEditButton() {
  // 检查是否已存在取消按钮
  if (document.getElementById('cancelEditBtn')) {
    return;
  }

  const addBtn = document.querySelector('.add-btn');
  const cancelBtn = document.createElement('button');
  cancelBtn.id = 'cancelEditBtn';
  cancelBtn.className = 'btn btn-outline-secondary';
  cancelBtn.style.marginLeft = '0.5rem';
  cancelBtn.innerHTML = '<i class="bi bi-x-lg"></i>取消';
  cancelBtn.onclick = cancelEdit;

  addBtn.parentNode.appendChild(cancelBtn);
}

// 取消编辑
function cancelEdit() {
  // 清空输入框
  document.getElementById('newKeyword').value = '';
  document.getElementById('newReply').value = '';

  // 清空商品ID选择框
  const selectElement = document.getElementById('newItemIdSelect');
  if (selectElement) {
    selectElement.value = '';
  }

  // 重置编辑状态
  delete window.editingIndex;
  delete window.originalKeyword;
  delete window.originalItemId;

  // 恢复添加按钮
  const addBtn = document.querySelector('.add-btn');
  addBtn.innerHTML = '<i class="bi bi-plus-lg"></i>添加';
  addBtn.style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';

  // 移除取消按钮
  const cancelBtn = document.getElementById('cancelEditBtn');
  if (cancelBtn) {
    cancelBtn.remove();
  }

  showToast('已取消编辑', 'info');
}

// 删除关键词
async function deleteKeyword(cookieId, index) {
  if (!confirm('确定要删除这个关键词吗？')) {
    return;
  }

  try {
    toggleLoading(true);

    // 获取当前关键词列表
    const currentKeywords = keywordsData[cookieId] || [];
    // 移除指定索引的关键词
    currentKeywords.splice(index, 1);

    // 更新服务器
    const response = await fetch(`${apiBase}/keywords-with-item-id/${cookieId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({
        keywords: currentKeywords
      })
    });

    if (response.ok) {
      showToast('关键词删除成功', 'success');
      keywordsData[cookieId] = currentKeywords;
      renderKeywordsList(currentKeywords);
      clearKeywordCache(); // 清除缓存
    } else {
      const errorText = await response.text();
      console.error('关键词删除失败:', errorText);
      showToast('关键词删除失败', 'danger');
    }
  } catch (error) {
    console.error('删除关键词失败:', error);
    showToast('删除关键词删除失败', 'danger');
  } finally {
    toggleLoading(false);
  }
}

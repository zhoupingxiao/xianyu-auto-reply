// ==================== 应用初始化 ====================

// 登出功能
async function logout() {
  try {
    if (authToken) {
      await fetch('/logout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
    }
    localStorage.removeItem('auth_token');
    window.location.href = '/';
  } catch (err) {
    console.error('登出失败:', err);
    localStorage.removeItem('auth_token');
    window.location.href = '/';
  }
}

// 检查认证状态
async function checkAuth() {
  if (!authToken) {
    window.location.href = '/';
    return false;
  }

  try {
    const response = await fetch('/verify', {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    const result = await response.json();

    if (!result.authenticated) {
      localStorage.removeItem('auth_token');
      window.location.href = '/';
      return false;
    }

    // 检查是否为管理员，显示管理员菜单和功能
    if (result.username === 'admin') {
      const adminMenuSection = document.getElementById('adminMenuSection');
      if (adminMenuSection) {
        adminMenuSection.style.display = 'block';
      }

      // 显示备份管理功能
      const backupManagement = document.getElementById('backup-management');
      if (backupManagement) {
        backupManagement.style.display = 'block';
      }
    }

    return true;
  } catch (err) {
    localStorage.removeItem('auth_token');
    window.location.href = '/';
    return false;
  }
}

// 初始化事件监听
document.addEventListener('DOMContentLoaded', async () => {
    // 首先检查认证状态
    const isAuthenticated = await checkAuth();
    if (!isAuthenticated) return;

    // 添加Cookie表单提交
    document.getElementById('addForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('cookieId').value.trim();
        const value = document.getElementById('cookieValue').value.trim();

        if (!id || !value) return;

        try {
            await fetchJSON(apiBase + '/cookies', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id, value })
            });

            document.getElementById('cookieId').value = '';
            document.getElementById('cookieValue').value = '';
            showToast(`账号 "${id}" 添加成功`);
            loadCookies();
        } catch (err) {
            // 错误已在fetchJSON中处理
        }
    });

    // 增强的键盘快捷键和用户体验
    document.getElementById('newKeyword')?.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            document.getElementById('newReply').focus();
        }
    });

    document.getElementById('newReply')?.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            addKeyword();
        }
    });

    // ESC键取消编辑
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && typeof window.editingIndex !== 'undefined') {
            e.preventDefault();
            cancelEdit();
        }
    });

    // 输入框实时验证和提示
    document.getElementById('newKeyword')?.addEventListener('input', function (e) {
        const value = e.target.value.trim();
        const addBtn = document.querySelector('.add-btn');
        const replyInput = document.getElementById('newReply');

        if (value.length > 0) {
            e.target.style.borderColor = '#10b981';
            if (replyInput.value.trim().length > 0) {
                addBtn.style.opacity = '1';
                addBtn.style.transform = 'scale(1)';
            }
        } else {
            e.target.style.borderColor = '#e5e7eb';
            addBtn.style.opacity = '0.7';
            addBtn.style.transform = 'scale(0.95)';
        }
    });

    document.getElementById('newReply')?.addEventListener('input', function (e) {
        const value = e.target.value.trim();
        const addBtn = document.querySelector('.add-btn');
        const keywordInput = document.getElementById('newKeyword');

        if (value.length > 0) {
            e.target.style.borderColor = '#10b981';
            if (keywordInput.value.trim().length > 0) {
                addBtn.style.opacity = '1';
                addBtn.style.transform = 'scale(1)';
            }
        } else {
            e.target.style.borderColor = '#e5e7eb';
            addBtn.style.opacity = '0.7';
            addBtn.style.transform = 'scale(0.95)';
        }
    });

    // 初始加载仪表盘
    loadDashboard();

    // 点击侧边栏外部关闭移动端菜单
    document.addEventListener('click', function (e) {
        const sidebar = document.getElementById('sidebar');
        const toggle = document.querySelector('.mobile-toggle');

        if (window.innerWidth <= 768 &&
            !sidebar.contains(e.target) &&
            !toggle.contains(e.target) &&
            sidebar.classList.contains('show')) {
            sidebar.classList.remove('show');
        }
    });
});

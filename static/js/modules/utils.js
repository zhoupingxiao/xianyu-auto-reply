// ==================== 通用工具函数 ====================

// 显示/隐藏加载动画
function toggleLoading(show) {
    document.getElementById('loading').classList.toggle('d-none', !show);
}

// 显示提示消息
function showToast(message, type = 'success') {
    const toastContainer = document.querySelector('.toast-container');
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();

    // 自动移除
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// 错误处理
async function handleApiError(err) {
    console.error(err);
    showToast(err.message || '操作失败', 'danger');
    toggleLoading(false);
}

// API请求包装
async function fetchJSON(url, opts = {}) {
    toggleLoading(true);
    try {
        // 添加认证头
        if (authToken) {
            opts.headers = opts.headers || {};
            opts.headers['Authorization'] = `Bearer ${authToken}`;
        }

        const res = await fetch(url, opts);
        if (res.status === 401) {
            // 未授权，跳转到登录页面
            localStorage.removeItem('auth_token');
            window.location.href = '/';
            return;
        }
        if (!res.ok) {
            let errorMessage = `HTTP ${res.status}`;
            try {
                const errorText = await res.text();
                if (errorText) {
                    // 尝试解析JSON错误信息
                    try {
                        const errorJson = JSON.parse(errorText);
                        errorMessage = errorJson.detail || errorJson.message || errorText;
                    } catch {
                        errorMessage = errorText;
                    }
                }
            } catch {
                errorMessage = `HTTP ${res.status} ${res.statusText}`;
            }
            throw new Error(errorMessage);
        }
        const data = await res.json();
        toggleLoading(false);
        return data;
    } catch (err) {
        handleApiError(err);
        throw err;
    }
}

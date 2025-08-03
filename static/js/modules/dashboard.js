// ==================== 仪表盘管理 ====================

// 加载仪表盘数据
async function loadDashboard() {
    try {
        toggleLoading(true);

        // 获取账号列表
        const cookiesResponse = await fetch(`${apiBase}/cookies/details`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (cookiesResponse.ok) {
            const cookiesData = await cookiesResponse.json();

            // 为每个账号获取关键词信息
            const accountsWithKeywords = await Promise.all(
                cookiesData.map(async (account) => {
                    try {
                        const keywordsResponse = await fetch(`${apiBase}/keywords/${account.id}`, {
                            headers: {
                                'Authorization': `Bearer ${authToken}`
                            }
                        });

                        if (keywordsResponse.ok) {
                            const keywordsData = await keywordsResponse.json();
                            return {
                                ...account,
                                keywords: keywordsData,
                                keywordCount: keywordsData.length
                            };
                        } else {
                            return {
                                ...account,
                                keywords: [],
                                keywordCount: 0
                            };
                        }
                    } catch (error) {
                        console.error(`获取账号 ${account.id} 关键词失败:`, error);
                        return {
                            ...account,
                            keywords: [],
                            keywordCount: 0
                        };
                    }
                })
            );

            dashboardData.accounts = accountsWithKeywords;

            // 计算统计数据
            let totalKeywords = 0;
            let activeAccounts = 0;
            let enabledAccounts = 0;

            accountsWithKeywords.forEach(account => {
                const keywordCount = account.keywordCount || 0;
                const isEnabled = account.enabled === undefined ? true : account.enabled;

                if (isEnabled) {
                    enabledAccounts++;
                    totalKeywords += keywordCount;
                    if (keywordCount > 0) {
                        activeAccounts++;
                    }
                }
            });

            dashboardData.totalKeywords = totalKeywords;

            // 更新仪表盘显示
            updateDashboardStats(accountsWithKeywords.length, totalKeywords, enabledAccounts);
            updateDashboardAccountsList(accountsWithKeywords);
        }
    } catch (error) {
        console.error('加载仪表盘数据失败:', error);
        showToast('加载仪表盘数据失败', 'danger');
    } finally {
        toggleLoading(false);
    }
}

// 更新仪表盘统计数据
function updateDashboardStats(totalAccounts, totalKeywords, enabledAccounts) {
    document.getElementById('totalAccounts').textContent = totalAccounts;
    document.getElementById('totalKeywords').textContent = totalKeywords;
    document.getElementById('activeAccounts').textContent = enabledAccounts;
}

// 更新仪表盘账号列表
function updateDashboardAccountsList(accounts) {
    const tbody = document.getElementById('dashboardAccountsList');
    tbody.innerHTML = '';

    if (accounts.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center text-muted py-4">
                    <i class="bi bi-inbox fs-1 d-block mb-2"></i>
                    暂无账号数据
                </td>
            </tr>
        `;
        return;
    }

    accounts.forEach(account => {
        const keywordCount = account.keywordCount || 0;
        const isEnabled = account.enabled === undefined ? true : account.enabled;

        let status = '';
        if (!isEnabled) {
            status = '<span class="badge bg-danger">已禁用</span>';
        } else if (keywordCount > 0) {
            status = '<span class="badge bg-success">活跃</span>';
        } else {
            status = '<span class="badge bg-secondary">未配置</span>';
        }

        const row = document.createElement('tr');
        row.className = isEnabled ? '' : 'table-secondary';
        row.innerHTML = `
            <td>
                <strong class="text-primary ${!isEnabled ? 'text-muted' : ''}">${account.id}</strong>
                ${!isEnabled ? '<i class="bi bi-pause-circle-fill text-danger ms-1" title="已禁用"></i>' : ''}
            </td>
            <td>
                <span class="badge ${isEnabled ? 'bg-primary' : 'bg-secondary'}">${keywordCount} 个关键词</span>
            </td>
            <td>${status}</td>
            <td>
                <small class="text-muted">${new Date().toLocaleString()}</small>
            </td>
        `;
        tbody.appendChild(row);
    });
}

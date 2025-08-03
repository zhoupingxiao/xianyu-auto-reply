// ==================== 账号列表管理 ====================

// 刷新账号列表（用于自动回复页面）
async function refreshAccountList() {
    try {
        toggleLoading(true);

        // 获取账号列表
        const response = await fetch(`${apiBase}/cookies/details`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const accounts = await response.json();
            const select = document.getElementById('accountSelect');
            select.innerHTML = '<option value="">🔍 请选择一个账号开始配置...</option>';

            // 为每个账号获取关键词数量
            const accountsWithKeywords = await Promise.all(
                accounts.map(async (account) => {
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
                                keywordCount: 0
                            };
                        }
                    } catch (error) {
                        console.error(`获取账号 ${account.id} 关键词失败:`, error);
                        return {
                            ...account,
                            keywordCount: 0
                        };
                    }
                })
            );

            // 渲染账号选项（显示所有账号，但标识禁用状态）
            if (accountsWithKeywords.length === 0) {
                select.innerHTML = '<option value="">❌ 暂无账号，请先添加账号</option>';
                return;
            }

            // 分组显示：先显示启用的账号，再显示禁用的账号
            const enabledAccounts = accountsWithKeywords.filter(account => {
                const enabled = account.enabled === undefined ? true : account.enabled;
                console.log(`账号 ${account.id} 过滤状态: enabled=${account.enabled}, 判断为启用=${enabled}`);
                return enabled;
            });
            const disabledAccounts = accountsWithKeywords.filter(account => {
                const enabled = account.enabled === undefined ? true : account.enabled;
                return !enabled;
            });

            // 渲染启用的账号
            enabledAccounts.forEach(account => {
                const option = document.createElement('option');
                option.value = account.id;

                // 根据关键词数量显示不同的图标和样式
                let icon = '📝';
                let status = '';
                if (account.keywordCount === 0) {
                    icon = '⚪';
                    status = ' (未配置)';
                } else if (account.keywordCount >= 5) {
                    icon = '🟢';
                    status = ` (${account.keywordCount} 个关键词)`;
                } else {
                    icon = '🟡';
                    status = ` (${account.keywordCount} 个关键词)`;
                }

                option.textContent = `${icon} ${account.id}${status}`;
                select.appendChild(option);
            });

            // 如果有禁用的账号，添加分隔线和禁用账号
            if (disabledAccounts.length > 0) {
                // 添加分隔线
                const separatorOption = document.createElement('option');
                separatorOption.disabled = true;
                separatorOption.textContent = `--- 禁用账号 (${disabledAccounts.length} 个) ---`;
                select.appendChild(separatorOption);

                // 渲染禁用的账号
                disabledAccounts.forEach(account => {
                    const option = document.createElement('option');
                    option.value = account.id;

                    // 禁用账号使用特殊图标和样式
                    let icon = '🔴';
                    let status = '';
                    if (account.keywordCount === 0) {
                        status = ' (未配置) [已禁用]';
                    } else {
                        status = ` (${account.keywordCount} 个关键词) [已禁用]`;
                    }

                    option.textContent = `${icon} ${account.id}${status}`;
                    option.style.color = '#6b7280';
                    option.style.fontStyle = 'italic';
                    select.appendChild(option);
                });
            }

            console.log('账号列表刷新完成，关键词统计:', accountsWithKeywords.map(a => ({ id: a.id, keywords: a.keywordCount })));
        } else {
            showToast('获取账号列表失败', 'danger');
        }
    } catch (error) {
        console.error('刷新账号列表失败:', error);
        showToast('刷新账号列表失败', 'danger');
    } finally {
        toggleLoading(false);
    }
}

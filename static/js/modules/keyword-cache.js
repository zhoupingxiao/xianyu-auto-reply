// ==================== 关键词缓存管理 ====================

// 获取账号关键词数量（带缓存）- 包含普通关键词和商品关键词
async function getAccountKeywordCount(accountId) {
    const now = Date.now();

    // 检查缓存
    if (accountKeywordCache[accountId] && (now - cacheTimestamp) < CACHE_DURATION) {
        return accountKeywordCache[accountId];
    }

    try {
        const response = await fetch(`${apiBase}/keywords/${accountId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const keywordsData = await response.json();
            // 现在API返回的是包含普通关键词和商品关键词的完整列表
            const count = keywordsData.length;

            // 更新缓存
            accountKeywordCache[accountId] = count;
            cacheTimestamp = now;

            return count;
        } else {
            return 0;
        }
    } catch (error) {
        console.error(`获取账号 ${accountId} 关键词失败:`, error);
        return 0;
    }
}

// 清除关键词缓存
function clearKeywordCache() {
    accountKeywordCache = {};
    cacheTimestamp = 0;
}

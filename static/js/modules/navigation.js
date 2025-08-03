// ==================== 页面导航功能 ====================

// 菜单切换功能
function showSection(sectionName) {
    console.log('切换到页面:', sectionName); // 调试信息

    // 隐藏所有内容区域
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });

    // 移除所有菜单项的active状态
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });

    // 显示选中的内容区域
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        targetSection.classList.add('active');
        console.log('页面已激活:', sectionName + '-section'); // 调试信息
    } else {
        console.error('找不到页面元素:', sectionName + '-section'); // 调试信息
    }

    // 设置对应菜单项为active（修复event.target问题）
    const menuLinks = document.querySelectorAll('.nav-link');
    menuLinks.forEach(link => {
        if (link.onclick && link.onclick.toString().includes(`showSection('${sectionName}')`)) {
            link.classList.add('active');
        }
    });

    // 根据不同section加载对应数据
    switch (sectionName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'accounts':
            loadCookies();
            break;
        case 'items':
            loadItems();
            break;
        case 'auto-reply':
            refreshAccountList();
            break;
        case 'cards':
            loadCards();
            break;
        case 'auto-delivery':
            loadDeliveryRules();
            break;
        case 'notification-channels':
            loadNotificationChannels();
            break;
        case 'message-notifications':
            loadMessageNotifications();
            break;
        case 'logs':
            // 如果没有日志数据，则加载
            setTimeout(() => {
                if (!window.allLogs || window.allLogs.length === 0) {
                    refreshLogs();
                }
            }, 100);
            break;
    }

    // 如果切换到非日志页面，停止自动刷新
    if (sectionName !== 'logs' && window.autoRefreshInterval) {
        clearInterval(window.autoRefreshInterval);
        window.autoRefreshInterval = null;
        const button = document.querySelector('#autoRefreshText');
        const icon = button?.previousElementSibling;
        if (button) {
            button.textContent = '开启自动刷新';
            if (icon) icon.className = 'bi bi-play-circle me-1';
        }
    }
}

// 移动端侧边栏切换
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('show');
}

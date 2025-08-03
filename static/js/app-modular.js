/**
 * 闲鱼自动回复系统 - 模块化主入口文件
 * 
 * 此文件负责引入所有功能模块，替代原来的单一app.js文件
 * 
 * 模块结构：
 * - globals.js: 全局变量
 * - utils.js: 通用工具函数
 * - navigation.js: 页面导航功能
 * - dashboard.js: 仪表盘管理
 * - keyword-cache.js: 关键词缓存管理
 * - account-list.js: 账号列表管理
 * - keywords.js: 关键词管理
 * - cookies.js: Cookie管理
 * - main-features.js: 主要功能
 * - all-other-features.js: 所有其他功能
 * - init.js: 应用初始化
 */

// 注意：在HTML中需要按以下顺序引入所有模块文件：
/*
<script src="/static/js/modules/globals.js"></script>
<script src="/static/js/modules/utils.js"></script>
<script src="/static/js/modules/navigation.js"></script>
<script src="/static/js/modules/dashboard.js"></script>
<script src="/static/js/modules/keyword-cache.js"></script>
<script src="/static/js/modules/account-list.js"></script>
<script src="/static/js/modules/keywords.js"></script>
<script src="/static/js/modules/cookies.js"></script>
<script src="/static/js/modules/main-features.js"></script>
<script src="/static/js/modules/all-other-features.js"></script>
<script src="/static/js/modules/init.js"></script>
*/

// 模块加载完成后的初始化检查
document.addEventListener('DOMContentLoaded', function() {
    console.log('闲鱼自动回复系统 - 模块化版本已加载');
    
    // 检查关键函数是否存在
    const requiredFunctions = [
        'showSection',
        'loadDashboard', 
        'loadCookies',
        'refreshAccountList',
        'loadAccountKeywords',
        'showToast',
        'toggleLoading'
    ];
    
    const missingFunctions = requiredFunctions.filter(func => typeof window[func] !== 'function');
    
    if (missingFunctions.length > 0) {
        console.error('缺少必要的函数:', missingFunctions);
        console.error('请检查模块文件是否正确加载');
    } else {
        console.log('所有必要的函数已加载完成');
    }
});

// 导出模块信息（用于调试）
window.moduleInfo = {
    version: '1.0.0',
    modules: [
        'globals',
        'utils', 
        'navigation',
        'dashboard',
        'keyword-cache',
        'account-list',
        'keywords',
        'cookies',
        'main-features',
        'all-other-features',
        'init'
    ],
    loadedAt: new Date().toISOString()
};

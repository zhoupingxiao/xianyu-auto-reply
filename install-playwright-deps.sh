#!/bin/bash

# 自定义 Playwright 依赖安装脚本
# 用于处理新版 Debian 中的包兼容性问题

# 不要在错误时立即退出，我们要尝试安装尽可能多的包
set +e

echo "开始安装 Playwright 依赖..."

# 更新包列表
apt-get update

# 记录安装状态
INSTALL_SUCCESS=0
INSTALL_FAILED=0

# 定义核心依赖包列表
CORE_PACKAGES=(
    "libnss3"
    "libnspr4"
    "libatk-bridge2.0-0"
    "libdrm2"
    "libxkbcommon0"
    "libxcomposite1"
    "libxdamage1"
    "libxrandr2"
    "libgbm1"
    "libxss1"
    "libasound2"
    "libatspi2.0-0"
    "libgtk-3-0"
    "libxcursor1"
    "libxi6"
    "libxrender1"
    "libxext6"
    "libx11-6"
    "libxft2"
    "libxinerama1"
    "libxtst6"
    "libappindicator3-1"
    "libx11-xcb1"
    "libxfixes3"
    "xdg-utils"
)

# 安装核心依赖包
echo "安装核心依赖包..."
for package in "${CORE_PACKAGES[@]}"; do
    if apt-get install -y --no-install-recommends "$package"; then
        echo "✅ 成功安装: $package"
        ((INSTALL_SUCCESS++))
    else
        echo "❌ 安装失败: $package"
        ((INSTALL_FAILED++))
    fi
done

# 尝试安装 gdk-pixbuf 包（兼容不同版本）
echo "安装 gdk-pixbuf 包..."
if apt-get install -y --no-install-recommends libgdk-pixbuf-2.0-0; then
    echo "✅ 成功安装: libgdk-pixbuf-2.0-0"
    ((INSTALL_SUCCESS++))
elif apt-get install -y --no-install-recommends libgdk-pixbuf2.0-0; then
    echo "✅ 成功安装: libgdk-pixbuf2.0-0"
    ((INSTALL_SUCCESS++))
else
    echo "❌ 安装失败: gdk-pixbuf packages"
    ((INSTALL_FAILED++))
fi

# 定义字体包列表
FONT_PACKAGES=(
    "fonts-unifont"
    "fonts-ubuntu"
    "fonts-noto"
    "fonts-noto-cjk"
    "fonts-noto-color-emoji"
)

# 安装字体包
echo "安装字体包..."
for package in "${FONT_PACKAGES[@]}"; do
    if apt-get install -y --no-install-recommends "$package"; then
        echo "✅ 成功安装: $package"
        ((INSTALL_SUCCESS++))
    else
        echo "❌ 安装失败: $package"
        ((INSTALL_FAILED++))
    fi
done

# 清理
apt-get clean
rm -rf /var/lib/apt/lists/*
rm -rf /tmp/*
rm -rf /var/tmp/*

# 输出安装结果
echo "=================================="
echo "Playwright 依赖安装完成"
echo "成功安装: $INSTALL_SUCCESS 个包"
echo "安装失败: $INSTALL_FAILED 个包"
echo "=================================="

# 检查关键依赖是否安装成功
CRITICAL_PACKAGES=("libnss3" "libnspr4" "libgtk-3-0" "libgbm1")
CRITICAL_MISSING=0

echo "检查关键依赖..."
for package in "${CRITICAL_PACKAGES[@]}"; do
    if dpkg -l | grep -q "^ii.*$package"; then
        echo "✅ 关键依赖已安装: $package"
    else
        echo "❌ 关键依赖缺失: $package"
        ((CRITICAL_MISSING++))
    fi
done

if [ $CRITICAL_MISSING -eq 0 ]; then
    echo "🎉 所有关键依赖都已成功安装，Playwright 应该能正常工作"
    exit 0
else
    echo "⚠️  有 $CRITICAL_MISSING 个关键依赖缺失，Playwright 可能无法正常工作"
    echo "但系统的其他功能不会受到影响"
    exit 0  # 不要让构建失败
fi

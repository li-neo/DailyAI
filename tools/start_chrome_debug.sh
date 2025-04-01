#!/bin/bash
# 启动Chrome的远程调试模式
# 简化版本，直接使用用户默认的Chrome配置

# 说明
echo "====================================================="
echo "X采集器助手 - 启动Chrome远程调试模式"
echo "====================================================="
echo "此脚本会启动一个带有远程调试功能的Chrome浏览器，"
echo "采集器将连接到这个实例，而不是启动新的浏览器窗口。"
echo ""
echo "使用步骤："
echo "1. 运行此脚本启动Chrome浏览器"
echo "2. 在浏览器中登录X账号"
echo "3. 保持此Chrome窗口打开"
echo "4. 运行采集程序"
echo ""

# 确定Chrome的路径
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    CHROME_PATH=$(which google-chrome 2>/dev/null || which chromium-browser 2>/dev/null)
elif [[ "$OSTYPE" == "msys"* ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows通过Git Bash或类似工具
    CHROME_PATH="/c/Program Files/Google/Chrome/Application/chrome.exe"
    if [ ! -f "$CHROME_PATH" ]; then
        CHROME_PATH="/c/Program Files (x86)/Google/Chrome/Application/chrome.exe"
    fi
fi

if [ ! -f "$CHROME_PATH" ]; then
    echo "错误: 找不到Chrome浏览器。请安装Chrome后再试。"
    exit 1
fi

# 设置远程调试端口
DEBUG_PORT=9222

# 检查是否已有Chrome在指定端口运行
if command -v nc &> /dev/null && nc -z localhost $DEBUG_PORT 2>/dev/null; then
    echo "检测到Chrome已在端口 $DEBUG_PORT 上运行"
    echo "您可以直接运行采集程序了"
    echo ""
    echo "如果需要重启Chrome，请关闭所有Chrome窗口，然后重新运行此脚本"
    exit 0
fi

# 启动Chrome，开启远程调试
echo "正在启动Chrome，开启远程调试端口: $DEBUG_PORT"
echo "请在新打开的Chrome窗口中登录X账号"
echo "警告: 请保持此Chrome窗口打开，直到采集完成"
echo ""

"$CHROME_PATH" --remote-debugging-port=$DEBUG_PORT --no-first-run
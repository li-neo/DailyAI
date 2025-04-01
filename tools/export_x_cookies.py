#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从 Chrome 中导出 X/Twitter 的 cookies
使用方法：python export_x_cookies.py
"""

import os
import sys
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def main():
    print("导出 Twitter/X 的 cookies")
    
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(current_dir)
    
    # 检测 Chrome 用户数据目录
    if sys.platform.startswith('darwin'):  # macOS
        chrome_path = os.path.expanduser('~/Library/Application Support/Google/Chrome')
    elif sys.platform.startswith('win'):  # Windows
        chrome_path = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Google', 'Chrome', 'User Data')
    else:  # Linux
        chrome_path = os.path.expanduser('~/.config/google-chrome')
    
    if not os.path.exists(chrome_path):
        print(f"Chrome 用户数据目录不存在: {chrome_path}")
        exit(1)
    
    print(f"使用 Chrome 用户数据目录: {chrome_path}")
    
    # 创建手动导入的工具
    print("\n由于不能直接访问正在运行的 Chrome，我们将创建一个帮助文件供您手动导入 cookies")
    print("请按照以下步骤操作：\n")
    print("1. 在 Chrome 中确保您已登录 Twitter/X")
    print("2. 安装 Chrome 扩展：'EditThisCookie' (https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg)")
    print("3. 访问 Twitter 网站 (https://twitter.com)")
    print("4. 点击 EditThisCookie 扩展图标，选择'导出 Cookies'")
    print("5. 将导出的 JSON 内容复制")
    print("6. 粘贴到以下文件中：", os.path.join(project_dir, 'data', 'x_cookies.json'))
    
    # 创建空的 cookies 文件
    data_dir = os.path.join(project_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    cookies_file = os.path.join(data_dir, 'x_cookies.json')
    
    with open(cookies_file, 'w') as f:
        f.write('[]')
    
    print(f"\n已创建空的 cookies 文件: {cookies_file}")
    print("请手动填入从 EditThisCookie 导出的 JSON 内容")
    
    return
    
    # 输出更多帮助信息
    print("\n如果你需要更详细的 Cookies 教程，请按照以下步骤：")
    print("1. 安装 Chrome 扩展 'EditThisCookie'")
    print("2. 确保你已在 Chrome 中登录 Twitter/X")
    print("3. 访问 Twitter 网站")
    print("4. 点击 EditThisCookie 扩展图标")
    print("5. 点击导出按钮（看起来像一个向外的箭头）")
    print("6. 复制所有 JSON 内容")
    print("7. 打开文件：" + cookies_file)
    print("8. 粘贴并保存")
    print("\n这样就完成了 Cookies 的导入，你可以继续运行数据采集程序了")
    print("\n如果你没有安装 EditThisCookie 扩展，可以去 Chrome 网上应用商店搜索并安装")
    print("https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg")

if __name__ == "__main__":
    main()
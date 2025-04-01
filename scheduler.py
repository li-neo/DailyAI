#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI日报采集器调度模块

负责设置和管理定时任务，确保每天在指定时间执行采集和发送任务。
"""

import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

def setup_scheduler(config, accounts):
    """
    设置定时任务调度器
    
    Args:
        config: 主配置信息
        accounts: 账号配置信息
    
    Returns:
        scheduler: 配置好的调度器实例
    """
    # 从main模块导入运行函数，避免循环导入
    from main import run_daily_collection
    
    scheduler = BackgroundScheduler()
    
    # 解析发送时间
    send_time = config['email']['send_time']
    hour, minute = map(int, send_time.split(':'))
    
    # 添加定时任务，每天指定时间运行
    scheduler.add_job(
        run_daily_collection,
        trigger=CronTrigger(hour=hour, minute=minute),
        args=[config, accounts],
        id='daily_collection',
        name='每日AI推文采集',
        misfire_grace_time=3600  # 允许的最大错过执行时间（秒）
    )
    
    return scheduler
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI日报采集器主程序

此程序是AI日报采集器的入口点，负责协调所有组件的工作，
完成X平台推文的采集、分析、排名和报告生成与发送。
"""

import os
import sys
import argparse
import yaml
from datetime import datetime

from utils.logger import setup_logger
from collectors.x_collector import XCollector
from processors.ranking import TweetRanker
from analyzers.deepseek_analyzer import DeepSeekAnalyzer
from delivery.email_sender import EmailSender
from storage.db_manager import DatabaseManager
from scheduler import setup_scheduler

def load_config(config_path="config/config.yaml"):
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        sys.exit(1)

def load_accounts(accounts_path="config/accounts.yaml"):
    """加载账号配置文件"""
    try:
        with open(accounts_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"加载账号配置文件失败: {e}")
        sys.exit(1)

def check_accounts_config(accounts):
    """检查账号配置是否完整"""
    warnings = []
    
    # 检查X账号
    if 'x_api' not in accounts or not accounts['x_api']:
        warnings.append("X账号配置缺失，采集功能可能受限")
    elif 'username' not in accounts['x_api'] or 'password' not in accounts['x_api']:
        warnings.append("X账号用户名或密码缺失，将使用未登录模式（获取的数据有限）")
    
    # 检查DeepSeek API
    if 'deepseek_api' not in accounts or not accounts['deepseek_api'] or 'api_key' not in accounts['deepseek_api']:
        warnings.append("DeepSeek API密钥缺失，分析功能将使用模拟数据")
    
    # 检查邮件配置
    if 'email_smtp' not in accounts or not accounts['email_smtp']:
        warnings.append("邮件配置缺失，无法发送报告邮件")
    
    return warnings

def run_daily_collection(config, accounts, force=False):
    """运行每日采集流程"""
    logger = setup_logger(config['logging'])
    logger.info("开始每日AI推文采集流程")
    
    # 初始化数据库
    db = DatabaseManager()
    
    # 采集X平台推文
    collector = XCollector(config['collection'], accounts['x_api'])
    raw_tweets = collector.collect()
    logger.info(f"从X平台采集了 {len(raw_tweets)} 条推文")
    
    # 对采集的推文进行排名
    ranker = TweetRanker(config['ranking'])
    ranked_tweets = ranker.rank(raw_tweets)
    
    # 选取前N条推文
    top_tweets = ranked_tweets[:config['report']['daily_tweet_count']]
    logger.info(f"已筛选出 {len(top_tweets)} 条优质推文")
    
    # 使用DeepSeek分析推文
    if config['report']['deepseek']['enabled']:
        analyzer = DeepSeekAnalyzer(accounts['deepseek_api'], config['report']['deepseek'])
        analysis_report = analyzer.analyze(top_tweets)
        logger.info("已完成DeepSeek分析")
    else:
        analysis_report = "DeepSeek分析未启用"
    
    # 保存结果到数据库
    db.save_tweets(top_tweets)
    db.save_report(analysis_report, datetime.now())
    
    # 发送邮件
    email_sender = EmailSender(accounts['email_smtp'], config['email'])
    email_sender.send_daily_report(top_tweets, analysis_report)
    logger.info("已发送AI日报邮件")
    
    return top_tweets, analysis_report

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AI日报采集器')
    parser.add_argument('--config', default='config/config.yaml', help='配置文件路径')
    parser.add_argument('--accounts', default='config/accounts.yaml', help='账号配置文件路径')
    parser.add_argument('--schedule', action='store_true', help='启动定时任务模式')
    parser.add_argument('--force-run', action='store_true', help='强制立即运行一次采集')
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 加载并检查账号配置
    try:
        accounts = load_accounts(args.accounts)
        warnings = check_accounts_config(accounts)
        if warnings:
            print("配置警告:")
            for warning in warnings:
                print(f"- {warning}")
    except Exception as e:
        print(f"加载账号配置失败: {e}")
        print("将使用默认空配置，功能将受限")
        accounts = {"x_api": {}, "deepseek_api": {}, "email_smtp": {}}
    
    if args.force_run:
        run_daily_collection(config, accounts, force=True)
        return
    
    if args.schedule:
        # 设置定时任务
        scheduler = setup_scheduler(config, accounts)
        print(f"定时任务已启动，将在每天 {config['email']['send_time']} 运行")
        scheduler.start()
    else:
        # 立即运行一次
        run_daily_collection(config, accounts)

if __name__ == "__main__":
    main()
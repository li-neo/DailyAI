#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基础数据采集器

为各种平台的采集器提供基础类和通用功能。
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

class BaseCollector(ABC):
    """
    数据采集器基类
    
    提供所有采集器共享的基础功能和接口规范。
    """
    
    def __init__(self, collection_config):
        """
        初始化采集器
        
        Args:
            collection_config: 采集配置信息
        """
        self.config = collection_config
        self.accounts = collection_config.get('accounts', [])
        self.keywords = collection_config.get('keywords', [])
        self.max_days_history = collection_config.get('max_days_history', 1)
        self.max_items = collection_config.get('max_tweets_per_day', 100)
        
    def get_start_date(self):
        """
        获取采集的起始日期
        
        Returns:
            start_date: 采集起始日期
        """
        return datetime.now(tz=timezone.utc) - timedelta(days=self.max_days_history)
    
    def is_relevant(self, content):
        """
        判断内容是否相关（包含关键词）
        
        Args:
            content: 要检查的内容文本
            
        Returns:
            bool: 内容是否相关
        """
        if not self.keywords:
            return True
            
        content_lower = content.lower()
        for keyword in self.keywords:
            if keyword.lower() in content_lower:
                return True
                
        return False
    
    @abstractmethod
    def collect(self):
        """
        执行采集操作
        
        Returns:
            list: 采集的数据列表
        """
        pass
    
    @abstractmethod
    def _connect_api(self):
        """
        连接到平台API
        
        Returns:
            api_client: API客户端
        """
        pass
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
推文去重处理器

提供推文去重功能，避免重复推送相同内容。
"""

from typing import List, Set
from models.tweet import Tweet
from utils.logger import get_logger

class TweetDeduplicator:
    """
    推文去重器
    
    基于ID和内容相似度检测和去除重复推文。
    """
    
    def __init__(self, db_manager=None):
        """
        初始化去重器
        
        Args:
            db_manager: 数据库管理器实例（用于检查历史数据）
        """
        self.db_manager = db_manager
        self.logger = get_logger(__name__)
        self.seen_ids = set()  # 当前批次已见ID集合
    
    def deduplicate(self, tweets: List[Tweet]) -> List[Tweet]:
        """
        对推文列表进行去重
        
        Args:
            tweets: 原始推文列表
            
        Returns:
            list: 去重后的推文列表
        """
        if not tweets:
            return []
            
        self.logger.info(f"开始对 {len(tweets)} 条推文进行去重")
        
        # 重置已见ID集合（仅用于当前批次）
        self.seen_ids = set()
        
        # 去重处理
        unique_tweets = []
        for tweet in tweets:
            # 检查ID是否已在当前批次中
            if tweet.id in self.seen_ids:
                continue
                
            # 检查ID是否在数据库中（如果提供了数据库管理器）
            if self.db_manager and self.db_manager.is_duplicate_tweet(tweet.id):
                self.logger.debug(f"跳过已存在的推文: {tweet.id}")
                continue
                
            # 添加到结果列表
            unique_tweets.append(tweet)
            self.seen_ids.add(tweet.id)
        
        removed_count = len(tweets) - len(unique_tweets)
        self.logger.info(f"去重完成，移除了 {removed_count} 条重复推文")
        
        return unique_tweets
    
    def filter_updates(self, tweets: List[Tweet], known_ids: Set[str]) -> List[Tweet]:
        """
        过滤出有更新的推文
        
        识别出在已知集合中但内容有更新的推文
        
        Args:
            tweets: 推文列表
            known_ids: 已知推文ID集合
            
        Returns:
            list: 有更新的推文列表
        """
        updates = []
        
        for tweet in tweets:
            if tweet.id in known_ids:
                # 此处可以添加更复杂的更新检测逻辑
                # 例如，比较点赞数、转发数等是否有明显变化
                # 当前简单实现为保留所有已知ID的推文
                updates.append(tweet)
        
        return updates
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """
        计算两段文本的相似度
        
        使用简单的Jaccard相似度计算
        
        Args:
            text1: 第一段文本
            text2: 第二段文本
            
        Returns:
            float: 相似度（0-1）
        """
        if not text1 or not text2:
            return 0.0
            
        # 分词
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # 计算Jaccard相似度
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
            
        return intersection / union
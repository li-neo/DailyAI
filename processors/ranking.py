#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
推文排名处理器

实现推文排名机制，基于配置的权重对推文进行打分和排序。
"""

import math
from datetime import datetime, timezone
from typing import List
from models.tweet import Tweet
from utils.logger import get_logger

class TweetRanker:
    """
    推文排名处理器
    
    基于多维度的权重算法对推文进行排名，支持自学习优化权重。
    """
    
    def __init__(self, ranking_config):
        """
        初始化排名器
        
        Args:
            ranking_config: 排名配置
        """
        self.config = ranking_config
        self.weights = ranking_config.get('weights', {})
        self.auto_learning = ranking_config.get('auto_learning', False)
        self.learning_rate = ranking_config.get('learning_rate', 0.01)
        self.min_engagement = ranking_config.get('min_engagement_threshold', 10)
        self.logger = get_logger(__name__)
        
    def rank(self, tweets: List[Tweet]) -> List[Tweet]:
        """
        对推文列表进行排名
        
        Args:
            tweets: 推文列表
            
        Returns:
            list: 排序后的推文列表
        """
        self.logger.info(f"开始对 {len(tweets)} 条推文进行排名")
        
        # 计算每条推文的分数
        for tweet in tweets:
            score, reason = self._calculate_score(tweet)
            tweet.rank_score = score
            tweet.rank_reason = reason
            
        # 按分数排序
        ranked_tweets = sorted(tweets, key=lambda t: t.rank_score or 0, reverse=True)
        
        self.logger.info(f"推文排名完成，最高分: {ranked_tweets[0].rank_score if ranked_tweets else 0}")
        
        # 如果启用自学习，调整权重
        if self.auto_learning and len(tweets) > 5:
            self._adjust_weights(ranked_tweets[:10])
            
        return ranked_tweets
    
    def _calculate_score(self, tweet: Tweet) -> tuple:
        """
        计算单条推文的分数
        
        Args:
            tweet: 推文对象
            
        Returns:
            tuple: (分数, 原因描述)
        """
        score_components = {}
        
        # 计算互动得分 (likes, retweets, replies, quotes)
        engagement_score = (
            self.weights.get('likes', 0.3) * tweet.likes +
            self.weights.get('retweets', 0.4) * tweet.retweets +
            self.weights.get('replies', 0.1) * tweet.replies +
            self.weights.get('quotes', 0.2) * tweet.quotes
        )
        score_components['engagement'] = engagement_score
        
        # 计算时效性得分
        recency_weight = self.weights.get('recency', 0.5)
        now = datetime.now(timezone.utc)
        if isinstance(tweet.created_at, datetime):
            age_hours = (now - tweet.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
            recency_score = recency_weight * math.exp(-0.01 * age_hours)  # 指数衰减
        else:
            recency_score = 0
        score_components['recency'] = recency_score
        
        # 计算用户影响力得分
        influence_weight = self.weights.get('user_influence', 0.6)
        # 这里可以实现更复杂的用户影响力评分，例如基于用户历史推文的互动情况
        # 目前简单实现为常量
        influence_score = influence_weight
        score_components['influence'] = influence_score
        
        # 计算关键词匹配得分
        keywords_weight = self.weights.get('keywords_match', 0.7)
        keywords_score = 0
        if hasattr(self, 'config') and 'keywords' in self.config:
            content_lower = tweet.content.lower()
            for keyword in self.config['keywords']:
                if keyword.lower() in content_lower:
                    keywords_score += keywords_weight / len(self.config['keywords'])
        score_components['keywords'] = keywords_score
        
        # 计算总分
        total_score = sum(score_components.values())
        
        # 生成排名原因描述
        reason = "排名因素: "
        for factor, score in score_components.items():
            reason += f"{factor}: {score:.2f}, "
            
        return total_score, reason.rstrip(", ")
    
    def _adjust_weights(self, top_tweets: List[Tweet]):
        """
        基于顶级推文调整权重
        
        实现简单的自学习机制，分析顶级推文的特征，调整权重
        
        Args:
            top_tweets: 排名前列的推文
        """
        if not top_tweets:
            return
            
        # 计算平均指标
        avg_likes = sum(t.likes for t in top_tweets) / len(top_tweets)
        avg_retweets = sum(t.retweets for t in top_tweets) / len(top_tweets)
        avg_replies = sum(t.replies for t in top_tweets) / len(top_tweets)
        avg_quotes = sum(t.quotes for t in top_tweets) / len(top_tweets)
        
        # 如果某项指标明显高于平均值，增加其权重
        if avg_likes > self.min_engagement:
            self.weights['likes'] += self.learning_rate
            
        if avg_retweets > self.min_engagement:
            self.weights['retweets'] += self.learning_rate
            
        if avg_replies > self.min_engagement:
            self.weights['replies'] += self.learning_rate
            
        if avg_quotes > self.min_engagement:
            self.weights['quotes'] += self.learning_rate
            
        # 归一化权重
        total = sum(self.weights.values())
        if total > 0:
            for key in self.weights:
                self.weights[key] /= total
                
        self.logger.info("已调整权重: " + ", ".join([f"{k}={v:.2f}" for k, v in self.weights.items()]))
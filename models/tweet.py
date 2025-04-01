#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
推文数据模型

定义推文的数据结构和相关操作。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class Tweet:
    """推文数据模型"""
    id: str
    author: str
    author_fullname: str
    content: str
    created_at: datetime
    url: str
    platform: str = "X"
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    quotes: int = 0
    referenced_urls: List[str] = field(default_factory=list)
    media_urls: List[str] = field(default_factory=list)
    rank_score: Optional[float] = None
    rank_reason: Optional[str] = None
    
    def to_dict(self):
        """
        将推文对象转换为字典
        
        Returns:
            dict: 推文字典表示
        """
        return {
            'id': self.id,
            'author': self.author,
            'author_fullname': self.author_fullname,
            'content': self.content,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'url': self.url,
            'platform': self.platform,
            'likes': self.likes,
            'retweets': self.retweets,
            'replies': self.replies,
            'quotes': self.quotes,
            'referenced_urls': self.referenced_urls,
            'media_urls': self.media_urls,
            'rank_score': self.rank_score,
            'rank_reason': self.rank_reason,
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        从字典创建推文对象
        
        Args:
            data: 推文字典数据
            
        Returns:
            Tweet: 推文对象
        """
        # 处理日期字段
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except ValueError:
                # 尝试其他格式
                try:
                    created_at = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%S.%fZ')
                except ValueError:
                    created_at = datetime.now()  # 兜底值
        
        return cls(
            id=data.get('id'),
            author=data.get('author'),
            author_fullname=data.get('author_fullname'),
            content=data.get('content'),
            created_at=created_at,
            url=data.get('url'),
            platform=data.get('platform', 'X'),
            likes=data.get('likes', 0),
            retweets=data.get('retweets', 0),
            replies=data.get('replies', 0),
            quotes=data.get('quotes', 0),
            referenced_urls=data.get('referenced_urls', []),
            media_urls=data.get('media_urls', []),
            rank_score=data.get('rank_score'),
            rank_reason=data.get('rank_reason'),
        )
    
    def __str__(self):
        """字符串表示"""
        return f"{self.author} ({self.created_at.strftime('%Y-%m-%d')}): {self.content[:50]}..."
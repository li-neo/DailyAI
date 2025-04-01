#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
报告数据模型

定义AI日报报告的数据结构和相关操作。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from .tweet import Tweet

@dataclass
class Report:
    """AI日报报告模型"""
    id: Optional[str] = None
    date: datetime = field(default_factory=datetime.now)
    title: str = "AI日报"
    tweets: List[Tweet] = field(default_factory=list)
    analysis: str = ""
    summary: str = ""
    trends: List[str] = field(default_factory=list)
    
    def to_dict(self):
        """
        将报告对象转换为字典
        
        Returns:
            dict: 报告字典表示
        """
        return {
            'id': self.id,
            'date': self.date.isoformat() if isinstance(self.date, datetime) else self.date,
            'title': self.title,
            'tweets': [tweet.to_dict() for tweet in self.tweets],
            'analysis': self.analysis,
            'summary': self.summary,
            'trends': self.trends,
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        从字典创建报告对象
        
        Args:
            data: 报告字典数据
            
        Returns:
            Report: 报告对象
        """
        # 处理日期字段
        date = data.get('date')
        if isinstance(date, str):
            try:
                date = datetime.fromisoformat(date)
            except ValueError:
                date = datetime.now()
        
        # 处理推文列表
        tweets = []
        for tweet_data in data.get('tweets', []):
            tweets.append(Tweet.from_dict(tweet_data))
        
        return cls(
            id=data.get('id'),
            date=date,
            title=data.get('title', 'AI日报'),
            tweets=tweets,
            analysis=data.get('analysis', ''),
            summary=data.get('summary', ''),
            trends=data.get('trends', []),
        )
    
    def format_email_html(self):
        """
        生成邮件HTML内容
        
        Returns:
            str: 邮件HTML内容
        """
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #1da1f2; }}
                h2 {{ color: #14171a; margin-top: 30px; }}
                .tweet {{ border: 1px solid #e1e8ed; border-radius: 5px; padding: 15px; margin-bottom: 15px; }}
                .tweet-header {{ display: flex; justify-content: space-between; margin-bottom: 10px; }}
                .tweet-author {{ font-weight: bold; }}
                .tweet-date {{ color: #657786; }}
                .tweet-content {{ margin-bottom: 10px; }}
                .tweet-metrics {{ color: #657786; font-size: 0.9em; }}
                .tweet-link {{ text-decoration: none; color: #1da1f2; }}
                .analysis {{ background-color: #f5f8fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .trends {{ margin-top: 30px; }}
                .trend-item {{ margin-bottom: 5px; }}
            </style>
        </head>
        <body>
            <h1>{self.title} - {self.date.strftime('%Y年%m月%d日')}</h1>
            
            <div class="summary">
                <h2>今日概述</h2>
                <p>{self.summary}</p>
            </div>
            
            <h2>热门AI推文精选</h2>
        """
        
        # 添加推文列表
        for i, tweet in enumerate(self.tweets, 1):
            created_at_str = tweet.created_at.strftime('%Y-%m-%d %H:%M') if isinstance(tweet.created_at, datetime) else tweet.created_at
            html += f"""
            <div class="tweet">
                <div class="tweet-header">
                    <span class="tweet-author">{i}. {tweet.author_fullname} (@{tweet.author})</span>
                    <span class="tweet-date">{created_at_str}</span>
                </div>
                <div class="tweet-content">{tweet.content}</div>
                <div class="tweet-metrics">
                    ❤️ {tweet.likes} | 🔄 {tweet.retweets} | 💬 {tweet.replies} | 📝 {tweet.quotes}
                </div>
                <div>
                    <a href="{tweet.url}" class="tweet-link" target="_blank">查看原文</a>
                </div>
            </div>
            """
            
        # 添加分析部分
        if self.analysis:
            html += f"""
            <div class="analysis">
                <h2>DeepSeek AI分析</h2>
                <p>{self.analysis.replace('\n', '<br>')}</p>
            </div>
            """
            
        # 添加趋势部分
        if self.trends:
            html += """
            <div class="trends">
                <h2>AI领域趋势</h2>
                <ul>
            """
            for trend in self.trends:
                html += f'<li class="trend-item">{trend}</li>\n'
            html += """
                </ul>
            </div>
            """
            
        html += """
        </body>
        </html>
        """
        
        return html
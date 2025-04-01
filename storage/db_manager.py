#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库管理模块

负责AI日报数据的持久化存储和检索。
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from models.tweet import Tweet
from utils.logger import get_logger

class DatabaseManager:
    """
    数据库管理器
    
    使用SQLite存储推文和报告数据，提供去重和历史记录功能。
    """
    
    def __init__(self, db_path="storage/daily_ai.db"):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.logger = get_logger(__name__)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建推文表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS tweets (
                id TEXT PRIMARY KEY,
                author TEXT NOT NULL,
                author_fullname TEXT,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                url TEXT NOT NULL,
                platform TEXT DEFAULT 'X',
                likes INTEGER DEFAULT 0,
                retweets INTEGER DEFAULT 0,
                replies INTEGER DEFAULT 0,
                quotes INTEGER DEFAULT 0,
                referenced_urls TEXT,
                media_urls TEXT,
                rank_score REAL,
                rank_reason TEXT,
                collection_date TEXT NOT NULL,
                report_id TEXT
            )
            ''')
            
            # 创建报告表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                title TEXT,
                analysis TEXT,
                summary TEXT,
                trends TEXT
            )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info("数据库初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化数据库失败: {e}")
            raise
    
    def save_tweets(self, tweets: List[Tweet]) -> bool:
        """
        保存推文到数据库
        
        Args:
            tweets: 推文列表
            
        Returns:
            bool: 是否保存成功
        """
        if not tweets:
            return False
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            collection_date = datetime.now().isoformat()
            
            for tweet in tweets:
                # 检查是否已存在
                cursor.execute("SELECT id FROM tweets WHERE id = ?", (tweet.id,))
                existing = cursor.fetchone()
                
                if existing:
                    # 更新已有推文
                    cursor.execute('''
                    UPDATE tweets SET
                        likes = ?,
                        retweets = ?,
                        replies = ?,
                        quotes = ?,
                        rank_score = ?,
                        rank_reason = ?,
                        collection_date = ?
                    WHERE id = ?
                    ''', (
                        tweet.likes,
                        tweet.retweets,
                        tweet.replies,
                        tweet.quotes,
                        tweet.rank_score,
                        tweet.rank_reason,
                        collection_date,
                        tweet.id
                    ))
                else:
                    # 插入新推文
                    cursor.execute('''
                    INSERT INTO tweets (
                        id, author, author_fullname, content, created_at, url, platform,
                        likes, retweets, replies, quotes, referenced_urls, media_urls,
                        rank_score, rank_reason, collection_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        tweet.id,
                        tweet.author,
                        tweet.author_fullname,
                        tweet.content,
                        tweet.created_at.isoformat() if isinstance(tweet.created_at, datetime) else tweet.created_at,
                        tweet.url,
                        tweet.platform,
                        tweet.likes,
                        tweet.retweets,
                        tweet.replies,
                        tweet.quotes,
                        json.dumps(tweet.referenced_urls),
                        json.dumps(tweet.media_urls),
                        tweet.rank_score,
                        tweet.rank_reason,
                        collection_date
                    ))
            
            conn.commit()
            conn.close()
            self.logger.info(f"成功保存 {len(tweets)} 条推文到数据库")
            return True
            
        except Exception as e:
            self.logger.error(f"保存推文到数据库失败: {e}")
            return False
    
    def save_report(self, analysis: str, date: datetime, title: str = None) -> Optional[str]:
        """
        保存分析报告
        
        Args:
            analysis: 分析报告内容
            date: 报告日期
            title: 报告标题
            
        Returns:
            str: 报告ID，保存失败返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 生成报告ID
            report_id = f"report_{date.strftime('%Y%m%d_%H%M%S')}"
            
            # 提取趋势
            trends = []
            
            # 保存报告
            cursor.execute('''
            INSERT INTO reports (id, date, title, analysis, summary, trends)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                report_id,
                date.isoformat(),
                title or f"AI日报 - {date.strftime('%Y年%m月%d日')}",
                analysis,
                "",  # 摘要在邮件发送时生成，此处为空
                json.dumps(trends)
            ))
            
            conn.commit()
            conn.close()
            self.logger.info(f"成功保存报告 {report_id} 到数据库")
            return report_id
            
        except Exception as e:
            self.logger.error(f"保存报告到数据库失败: {e}")
            return None
    
    def get_report(self, report_id: str) -> Dict[str, Any]:
        """
        获取指定报告
        
        Args:
            report_id: 报告ID
            
        Returns:
            dict: 报告数据
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取报告
            cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
            report_row = cursor.fetchone()
            
            if not report_row:
                conn.close()
                return {}
                
            report = dict(report_row)
            
            # 获取相关推文
            cursor.execute("SELECT * FROM tweets WHERE report_id = ? ORDER BY rank_score DESC", (report_id,))
            tweets_rows = cursor.fetchall()
            
            tweets = []
            for tweet_row in tweets_rows:
                tweet_dict = dict(tweet_row)
                
                # 解析JSON字段
                for field in ['referenced_urls', 'media_urls']:
                    if tweet_dict.get(field):
                        try:
                            tweet_dict[field] = json.loads(tweet_dict[field])
                        except:
                            tweet_dict[field] = []
                
                tweets.append(tweet_dict)
                
            report['tweets'] = tweets
            
            conn.close()
            return report
            
        except Exception as e:
            self.logger.error(f"获取报告失败: {e}")
            return {}
    
    def is_duplicate_tweet(self, tweet_id: str) -> bool:
        """
        检查推文是否是重复的
        
        Args:
            tweet_id: 推文ID
            
        Returns:
            bool: 是否重复
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM tweets WHERE id = ?", (tweet_id,))
            result = cursor.fetchone()
            
            conn.close()
            return result is not None
            
        except Exception as e:
            self.logger.error(f"检查重复推文失败: {e}")
            return False
    
    def get_recent_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的报告列表
        
        Args:
            limit: 返回数量限制
            
        Returns:
            list: 报告列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT id, date, title FROM reports 
            ORDER BY date DESC LIMIT ?
            """, (limit,))
            
            reports = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return reports
            
        except Exception as e:
            self.logger.error(f"获取最近报告失败: {e}")
            return []
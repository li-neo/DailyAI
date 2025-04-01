#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
时间工具模块

提供时间处理和计算的工具函数。
"""

from datetime import datetime, timedelta, timezone
import pytz

def now_utc():
    """
    获取当前UTC时间
    
    Returns:
        datetime: 当前UTC时间
    """
    return datetime.now(timezone.utc)

def now_beijing():
    """
    获取当前北京时间
    
    Returns:
        datetime: 当前北京时间
    """
    beijing_tz = pytz.timezone('Asia/Shanghai')
    return datetime.now(beijing_tz)

def format_time(dt, format_str="%Y-%m-%d %H:%M:%S"):
    """
    格式化时间
    
    Args:
        dt: datetime对象
        format_str: 格式字符串
        
    Returns:
        str: 格式化的时间字符串
    """
    if not dt:
        return ""
    
    if not isinstance(dt, datetime):
        try:
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            else:
                return str(dt)
        except ValueError:
            return str(dt)
    
    return dt.strftime(format_str)

def parse_time(time_str, default_tz=None):
    """
    解析时间字符串
    
    Args:
        time_str: 时间字符串
        default_tz: 默认时区
        
    Returns:
        datetime: 解析后的datetime对象
    """
    if not time_str:
        return None
        
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(time_str, fmt)
            # 如果没有时区信息，添加默认时区
            if default_tz and dt.tzinfo is None:
                if isinstance(default_tz, str):
                    default_tz = pytz.timezone(default_tz)
                dt = default_tz.localize(dt)
            return dt
        except ValueError:
            continue
    
    # 尝试ISO格式解析
    try:
        return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError(f"无法解析时间字符串: {time_str}")

def time_ago(dt):
    """
    计算相对于当前时间的时间差（多久之前）
    
    Args:
        dt: datetime对象
        
    Returns:
        str: 人类可读的时间差描述
    """
    if not dt:
        return ""
        
    if not isinstance(dt, datetime):
        try:
            dt = parse_time(dt)
        except ValueError:
            return str(dt)
    
    # 确保有时区信息
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
        
    now = datetime.now(timezone.utc)
    diff = now - dt
    
    if diff.days < 0:
        return "未来"
        
    if diff.days == 0:
        seconds = diff.seconds
        if seconds < 60:
            return "刚刚"
        elif seconds < 3600:
            return f"{seconds // 60}分钟前"
        else:
            return f"{seconds // 3600}小时前"
    elif diff.days < 30:
        return f"{diff.days}天前"
    elif diff.days < 365:
        return f"{diff.days // 30}个月前"
    else:
        return f"{diff.days // 365}年前"

def get_date_range(days_ago, end_date=None):
    """
    获取指定天数前到指定结束日期的日期范围
    
    Args:
        days_ago: 开始日期（多少天前）
        end_date: 结束日期，默认为今天
        
    Returns:
        tuple: (开始日期, 结束日期)
    """
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    elif not isinstance(end_date, datetime):
        end_date = parse_time(end_date)
        
    start_date = end_date - timedelta(days=days_ago)
    
    return start_date, end_date
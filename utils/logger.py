#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志工具模块

为整个项目提供统一的日志记录功能。
"""

import os
import logging
from logging.handlers import RotatingFileHandler

# 全局日志实例字典
_loggers = {}

def setup_logger(logging_config=None):
    """
    配置并返回日志记录器
    
    Args:
        logging_config: 日志配置字典
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    global _loggers
    
    # 默认配置
    log_level = logging.INFO
    log_file = "logs/daily_ai.log"
    max_size_mb = 10
    backup_count = 5
    
    # 使用提供的配置
    if logging_config:
        log_level_name = logging_config.get('level', 'INFO')
        log_level = getattr(logging, log_level_name, logging.INFO)
        log_file = logging_config.get('file', log_file)
        max_size_mb = logging_config.get('max_size_mb', max_size_mb)
        backup_count = logging_config.get('backup_count', backup_count)
    
    # 确保日志目录存在
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # 创建根日志记录器
    logger = logging.getLogger()
    
    # 避免重复设置
    if logger in _loggers:
        return logger
        
    # 清除现有处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    # 设置日志级别
    logger.setLevel(log_level)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # 创建文件处理器
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_size_mb * 1024 * 1024,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    # 缓存日志实例
    _loggers[logger] = True
    
    return logger

def get_logger(name=None):
    """
    获取指定名称的日志记录器
    
    如果根日志记录器未配置，将自动配置它。
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器
    """
    # 确保根日志记录器已配置
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        setup_logger()
    
    # 获取或创建指定名称的日志记录器
    if name:
        return logging.getLogger(name)
    else:
        return root_logger
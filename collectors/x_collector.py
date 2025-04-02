#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
X平台数据采集器

使用Selenium从X平台采集指定账号的推文数据，无需官方API。
"""

import time
import os
import json
import random
import traceback
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from .base_collector import BaseCollector
from models.tweet import Tweet
from utils.logger import get_logger

class XCollector(BaseCollector):
    """
    X平台数据采集器
    
    使用Selenium采集指定账号的推文，无需官方API。
    """
    
    def __init__(self, collection_config, api_config=None):
        """
        初始化X采集器
        
        Args:
            collection_config: 采集配置
            api_config: 如果提供，包含登录X的用户名和密码
        """
        super().__init__(collection_config)
        self.api_config = api_config
        self.logger = get_logger(__name__)
        self.client = self._init_selenium()
        
    def _connect_api(self):
        """
        实现基类的抽象方法
        
        由于使用Selenium而不是API，这里返回None
        """
        return None
        
    def _init_selenium(self):
        """
        初始化Selenium客户端
        
        Returns:
            client: Selenium包装器，失败返回None
        """
        try:
            # 尝试导入selenium
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                from selenium.webdriver.chrome.service import Service
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from webdriver_manager.chrome import ChromeDriverManager
                # 导入异常类
                from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
            except ImportError:
                self.logger.error("selenium未安装，请先安装：pip install selenium webdriver-manager")
                return None
                
            # 创建一个简单的Selenium包装器类
            class SeleniumClient:
                def __init__(self, logger, headless=True, api_config=None):
                    self.logger = logger
                    self.driver = None
                    self.headless = headless
                    self.api_config = api_config
                    self.is_logged_in = False
                    self.retry_count = 3  # 操作重试次数
                    
                    # 检查是否需要有头模式
                    if api_config and 'headless' in api_config:
                        self.headless = api_config['headless']
                    else:
                        self.headless = False  # 默认使用有头模式
                    
                    # 初始化浏览器
                    self._init_driver()
                    
                def _init_driver(self):
                    try:
                        # 导入必要的模块
                        import os
                        
                        options = Options()
                        if self.headless:
                            options.add_argument("--headless=new")  # 新的无头模式
                        options.add_argument("--no-sandbox")
                        options.add_argument("--disable-dev-shm-usage")
                        options.add_argument("--disable-notifications")
                        options.add_argument("--disable-popup-blocking")
                        options.add_argument("--disable-blink-features=AutomationControlled")  # 关键：隐藏自动化特征
                        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
                        options.add_argument("--window-size=1920,1080")
                        options.add_argument("--start-maximized")
                        options.add_argument("--lang=zh-CN,zh,en-US,en")
                        
                        # 将Chrome设置为远程调试模式
                        # 复用已经打开的Chrome浏览器，而不是启动新的浏览器窗口
                        remote_debugging_port = '9222'  # 调试端口号
                        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{remote_debugging_port}")
                        
                        try:
                            # 使用配置好的选项启动ChromeDriver
                            try:
                                chrome_driver_path = os.path.expanduser('~/chromedriver/chromedriver')
                                if os.path.exists(chrome_driver_path):
                                    from selenium.webdriver.chrome.service import Service
                                    service = Service(executable_path=chrome_driver_path)
                                    self.driver = webdriver.Chrome(service=service, options=options)
                                    self.logger.info("使用本地ChromeDriver初始化成功")
                                else:
                                    from selenium.webdriver.chrome.service import Service
                                    from webdriver_manager.chrome import ChromeDriverManager
                                    service = Service(ChromeDriverManager().install())
                                    self.driver = webdriver.Chrome(service=service, options=options)
                                    self.logger.info("使用ChromeDriverManager初始化成功")
                            except Exception as e:
                                self.logger.error(f"初始化Chrome浏览器失败: {str(e)}")
                                # 尝试不同的方式
                                self.driver = webdriver.Chrome(options=options)
                                self.logger.info("使用默认方式初始化成功")
                            
                            self.logger.info("成功初始化Chrome浏览器")
                        except Exception as e:
                            self.logger.error(f"所有初始化方式都失败: {str(e)}")
                            self.logger.info("请确保已经在命令行启动了Chrome远程调试模式")
                            self.logger.info("运行命令: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' --remote-debugging-port=9222")
                            return False
                            
                        # 设置窗口大小
                        try:
                            self.driver.set_window_size(1920, 1080)
                        except:
                            self.logger.warning("无法设置窗口大小")
                        
                        # 设置超时
                        self.driver.set_page_load_timeout(60)
                        self.driver.set_script_timeout(30)
                        
                        # 检查当前页面状态
                        try:
                            current_url = self.driver.current_url
                            title = self.driver.title
                            self.logger.info(f"当前页面URL: {current_url}")
                            self.logger.info(f"当前页面标题: {title}")
                            
                            # 检查是否已经登录
                            if "twitter.com" in current_url or "x.com" in current_url:
                                if not ("login" in current_url.lower()):
                                    self.logger.info("检测到已登录状态")
                                    self.is_logged_in = True
                                else:
                                    self.logger.warning("检测到未登录状态，请先在Chrome中登录X账号")
                        except Exception as e:
                            self.logger.error(f"检查页面状态失败: {str(e)}")
                        
                        return True
                    except Exception as e:
                        self.logger.error(f"初始化Chrome浏览器失败: {str(e)}")
                        return False
                
                def _hide_automation_flags(self):
                    """隐藏自动化特征"""
                    try:
                        # 基本的webdriver标志隐藏
                        self.driver.execute_script("""
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                        """)
                        
                        # 隐藏更多自动化特征
                        self.driver.execute_script("""
                        // 覆盖navigator属性
                        Object.defineProperty(navigator, 'maxTouchPoints', {
                            get: () => 5
                        });
                        
                        // 伪造浏览器名称
                        Object.defineProperty(navigator, 'appName', {
                            get: () => 'Netscape'
                        });
                        
                        // 伪造浏览器版本
                        Object.defineProperty(navigator, 'appVersion', {
                            get: () => '5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
                        });
                        """)
                    except Exception as e:
                        self.logger.debug(f"设置隐藏自动化特征时出错: {str(e)}")
                        pass
                
                def _safe_wait_and_find(self, by, value, timeout=10, condition=EC.presence_of_element_located):
                    """安全地等待并查找元素，带重试机制"""
                    for attempt in range(self.retry_count):
                        try:
                            element = WebDriverWait(self.driver, timeout).until(
                                condition((by, value))
                            )
                            return element
                        except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
                            if attempt < self.retry_count - 1:
                                self.logger.debug(f"查找元素 {value} 失败，重试 {attempt+1}/{self.retry_count}")
                                time.sleep(1)
                            else:
                                raise
                    return None
                        
                def sign_in(self, username, password):
                    """登录 X 账号"""
                    if not self.driver:
                        return False
                        
                    # 使用 CSS 采集器时，我们不需要真正登录，只需采集公开的数据
                    self.logger.info("使用 CSS 采集器模式，无需登录")
                    return True
                
                def get_tweets(self, username, count=10):
                    """获取用户的推文"""
                    if not self.driver:
                        return []
                        
                    tweets = []
                    try:
                        # 访问用户主页
                        self.logger.info(f"正在访问用户主页: {username}")
                        
                        # 带重试的页面访问
                        for attempt in range(self.retry_count):
                            try:
                                profile_url = f"https://x.com/{username}"
                                self.driver.get(profile_url)
                                self.logger.info(f"正在加载: {profile_url}")
                                time.sleep(5)  # 给页面足够的加载时间
                                break
                            except Exception as e:
                                if attempt < self.retry_count - 1:
                                    self.logger.warning(f"访问用户页面失败，重试 {attempt+1}/{self.retry_count}")
                                    time.sleep(2)
                                else:
                                    raise
                        
                        # 检查页面标题和URL，判断页面是否正确加载
                        self.logger.info(f"当前页面标题: {self.driver.title}")
                        self.logger.info(f"当前页面URL: {self.driver.current_url}")
                        
                        # 检查用户是否存在
                        if "这个账号不存在" in self.driver.page_source or "This account doesn't exist" in self.driver.page_source:
                            self.logger.error(f"用户 {username} 不存在")
                            return []
                        
                        # 等待推文加载
                        try:
                            # 尝试多种可能的CSS选择器
                            selectors = [
                                "article[data-testid='tweet']", 
                                "div[data-testid='cellInnerDiv']", 
                                "div[data-testid='tweet']",
                                "div[role='article']"
                            ]
                            
                            tweet_found = False
                            for selector in selectors:
                                try:
                                    self.logger.info(f"尝试使用选择器: {selector}")
                                    WebDriverWait(self.driver, 15).until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                                    )
                                    tweet_found = True
                                    self.logger.info(f"找到推文元素，使用选择器: {selector}")
                                    break
                                except:
                                    self.logger.warning(f"选择器 {selector} 未找到元素")
                            
                            if not tweet_found:
                                self.logger.error("所有选择器都未找到推文")
                                # 记录页面源代码的前1000个字符以便调试
                                self.logger.debug(f"页面源代码前1000个字符: {self.driver.page_source[:1000]}")
                                return []
                                
                        except TimeoutException:
                            self.logger.warning(f"等待推文加载超时")
                            return []
                        
                        # 获取一天前的日期作为筛选条件
                        one_day_ago = datetime.now(datetime.now().astimezone().tzinfo) - timedelta(days=1)
                        self.logger.info(f"只获取 {one_day_ago.isoformat()} 之后的推文")
                        
                        # 滚动加载更多推文
                        last_height = self.driver.execute_script("return document.body.scrollHeight")
                        scrolls = 0
                        max_scrolls = 10  # 减少最大滚动次数，因为我们只需要前一天的推文
                        
                        no_new_tweets_count = 0  # 连续没有新推文的次数
                        
                        while len(tweets) < count and scrolls < max_scrolls:
                            # 滚动到底部
                            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            time.sleep(3)  # 给页面加载的时间
                            
                            # 获取推文元素 - 尝试多种选择器
                            tweet_elements = []
                            for selector in selectors:
                                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                if elements:
                                    tweet_elements = elements
                                    self.logger.info(f"使用选择器 {selector} 找到 {len(elements)} 条推文")
                                    break
                            
                            if not tweet_elements:
                                self.logger.warning("未找到任何推文元素")
                                break
                                
                            self.logger.info(f"本次找到 {len(tweet_elements)} 条推文")
                            
                            # 解析推文
                            new_tweets_count = 0
                            oldest_tweet_time = datetime.now(datetime.now().astimezone().tzinfo)
                            
                            for tweet_element in tweet_elements:
                                if len(tweets) >= count:
                                    break
                                    
                                try:
                                    # 获取创建时间
                                    created_on = datetime.now(datetime.now().astimezone().tzinfo)  # 默认为当前时间，带时区信息
                                    try:
                                        time_element = tweet_element.find_element(By.CSS_SELECTOR, "time")
                                        created_at = time_element.get_attribute("datetime")
                                        if created_at:
                                            created_on = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                    except:
                                        self.logger.debug("无法获取推文创建时间")
                                    
                                    # 更新最旧推文时间
                                    if created_on < oldest_tweet_time:
                                        oldest_tweet_time = created_on
                                    
                                    # 检查是否为前一天内的推文
                                    if created_on < one_day_ago:
                                        self.logger.debug(f"跳过旧推文，时间: {created_on.isoformat()}")
                                        continue
                                    
                                    # 获取推文ID
                                    tweet_id = None
                                    try:
                                        tweet_link = tweet_element.find_element(By.CSS_SELECTOR, "a[href*='/status/']").get_attribute("href")
                                        tweet_id = tweet_link.split("/status/")[1].split("?")[0] if "/status/" in tweet_link else None
                                    except:
                                        self.logger.debug("无法通过链接获取推文ID")
                                    
                                    # 如果无法获取ID，尝试从其他属性获取
                                    if not tweet_id:
                                        try:
                                            tweet_id = tweet_element.get_attribute("data-tweet-id") or tweet_element.get_attribute("id")
                                        except:
                                            # 生成一个随机ID
                                            tweet_id = f"temp_{random.randint(10000000, 99999999)}"
                                            self.logger.debug(f"使用临时ID: {tweet_id}")
                                    
                                    # 检查是否已经处理过这条推文
                                    if any(t.id == tweet_id for t in tweets):
                                        continue
                                    
                                    # 获取推文文本 - 尝试多种选择器
                                    text = ""
                                    text_selectors = [
                                        "div[data-testid='tweetText']",
                                        "div[lang]",
                                        "div[dir='auto']"
                                    ]
                                    
                                    for selector in text_selectors:
                                        try:
                                            text_elements = tweet_element.find_elements(By.CSS_SELECTOR, selector)
                                            if text_elements:
                                                text = text_elements[0].text
                                                if text:
                                                    break
                                        except:
                                            pass
                                    
                                    # 获取统计数据
                                    likes, retweets, replies = 0, 0, 0
                                    
                                    # 创建推文对象
                                    tweet = type('obj', (object,), {
                                        'id': tweet_id,
                                        'text': text,
                                        'created_on': created_on,
                                        'likes': likes,
                                        'retweets': retweets, 
                                        'replies': replies,
                                        'quotes': 0,
                                        'url': tweet_link if 'tweet_link' in locals() else f"https://x.com/{username}/status/{tweet_id}",
                                        'links': []
                                    })
                                    
                                    tweets.append(tweet)
                                    new_tweets_count += 1
                                    self.logger.debug(f"已解析推文ID: {tweet_id}, 时间: {created_on.isoformat()}")
                                    
                                except Exception as e:
                                    self.logger.debug(f"解析单条推文失败: {str(e)}")
                                    continue
                            
                            # 如果本次未找到新推文，增加计数
                            if new_tweets_count == 0:
                                no_new_tweets_count += 1
                            else:
                                no_new_tweets_count = 0
                            
                            # 如果连续两次未找到新推文或者最早的推文已经超过一天，提前退出
                            if no_new_tweets_count >= 2:
                                self.logger.debug("连续多次未获取到新推文，提前结束")
                                break
                                
                            # 如果已经滚动到的推文早于一天前，没必要继续滚动
                            if oldest_tweet_time < one_day_ago:
                                self.logger.info(f"已找到一天前的推文，不再继续滚动。最早推文时间: {oldest_tweet_time.isoformat()}")
                                break
                                
                            # 检查是否已滚动到底部
                            new_height = self.driver.execute_script("return document.body.scrollHeight")
                            if new_height == last_height:
                                self.logger.debug("已滚动到页面底部，没有更多推文")
                                break
                            last_height = new_height
                            scrolls += 1
                        
                        self.logger.info(f"共获取到 {len(tweets)} 条推文")
                        return tweets
                        
                    except Exception as e:
                        self.logger.error(f"获取用户 {username} 的推文失败: {str(e)}")
                        self.logger.error(traceback.format_exc())
                        return []
                
                def _load_cookies(self):
                    """从文件加载 Cookies"""
                    cookies_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'x_cookies.json')
                    if os.path.exists(cookies_file):
                        try:
                            self.logger.info(f"尝试从 {cookies_file} 加载 Cookies")
                            with open(cookies_file, 'r') as f:
                                cookies = json.load(f)
                                
                            # 先访问 Twitter 网站，然后才能添加 cookies
                            self.driver.get("https://x.com")
                            time.sleep(1)
                            
                            # 添加 cookies
                            for cookie in cookies:
                                try:
                                    # 有些 cookie 属性 Selenium 无法处理，需要删除
                                    if 'sameSite' in cookie:
                                        del cookie['sameSite']
                                    if 'expiry' in cookie and isinstance(cookie['expiry'], float):
                                        cookie['expiry'] = int(cookie['expiry'])
                                    
                                    self.driver.add_cookie(cookie)
                                except Exception as e:
                                    self.logger.debug(f"添加 cookie 失败: {str(e)}")
                                    
                            self.logger.info("Cookies 加载完成")
                            return True
                        except Exception as e:
                            self.logger.error(f"加载 Cookies 失败: {str(e)}")
                            return False
                    else:
                        self.logger.info(f"Cookies 文件不存在: {cookies_file}")
                        return False
                        
                def _save_cookies(self):
                    """保存 Cookies 到文件"""
                    if not self.driver:
                        return False
                        
                    try:
                        cookies = self.driver.get_cookies()
                        cookies_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
                        os.makedirs(cookies_dir, exist_ok=True)
                        cookies_file = os.path.join(cookies_dir, 'x_cookies.json')
                        
                        with open(cookies_file, 'w') as f:
                            json.dump(cookies, f)
                            
                        self.logger.info(f"已保存 Cookies 到 {cookies_file}")
                        return True
                    except Exception as e:
                        self.logger.error(f"保存 Cookies 失败: {str(e)}")
                        return False
                
                def close(self):
                    """关闭浏览器"""
                    if self.driver:
                        try:
                            # 保存 Cookies 再关闭
                            self._save_cookies()
                            self.driver.quit()
                            self.logger.info("Selenium浏览器已关闭")
                        except Exception as e:
                            self.logger.error(f"关闭浏览器失败: {str(e)}")
            
            # 创建客户端
            self.logger.info("初始化Selenium客户端...")
            
            # 检查是否需要有头模式（从api_config中获取headless配置）
            headless_mode = True  # 默认无头模式
            if self.api_config and 'headless' in self.api_config:
                headless_mode = self.api_config['headless']
                if not headless_mode:
                    self.logger.info("根据配置使用有头模式启动浏览器")
            
            # 如果存在验证码或需要手动操作，可以设置headless=False
            client = SeleniumClient(self.logger, headless=headless_mode, api_config=self.api_config)
            
            # 如果提供了登录信息，则登录
            if self.api_config and 'username' in self.api_config and 'password' in self.api_config:
                self.logger.info(f"尝试使用账号 {self.api_config['username']} 登录X")
                success = client.sign_in(
                    self.api_config['username'],
                    self.api_config['password']
                )
                if not success:
                    self.logger.warning("X账号登录失败，将使用未登录模式（获取的数据可能有限）")
            else:
                self.logger.info("未提供X账号信息，使用未登录模式")
            
            # 测试一下客户端是否可用
            self.logger.info("测试Selenium客户端...")
            test_tweets = client.get_tweets("AIDEN_LI_", count=1)
            return client
            # if test_tweets:
            #     self.logger.info("Selenium客户端测试成功")
            #     return client
            # else:
            #     self.logger.error("Selenium客户端测试失败")
            #     client.close()
            #     return None
            
        except Exception as e:
            self.logger.error(f"初始化Selenium客户端失败: {traceback.format_exc()}")
            return None
    
    def collect(self) -> List[Tweet]:
        """
        从X采集推文
        
        Returns:
            list: Tweet对象列表
        """
        if not self.client:
            self.logger.error("Selenium客户端未初始化，无法采集")
            return []
            
        all_tweets = []
        # 使用当前日期减一天作为开始日期，确保带有时区信息
        start_date = datetime.now(datetime.now().astimezone().tzinfo) - timedelta(days=1)
        self.logger.info(f"设置开始日期: {start_date.isoformat()}")
        
        for account in self.accounts:
            self.logger.info(f"正在采集用户 {account['username']} 的推文")
            
            try:
                username = account['username']
                
                # 获取用户推文
                user_tweets = self.client.get_tweets(username, count=self.max_items)
                
                # 过滤推文
                filtered_tweets = []
                for tweet in user_tweets:
                    # 检查日期 - tweet_date 和 start_date 应该都有时区信息
                    tweet_date = tweet.created_on
                    
                    # 确保两个日期时间对象有相同的时区格式
                    if tweet_date.tzinfo is not None and start_date.tzinfo is None:
                        # start_date 是 naive，将 tweet_date 转换为 naive
                        from datetime import timezone
                        tweet_date = tweet_date.replace(tzinfo=None)
                    elif tweet_date.tzinfo is None and start_date.tzinfo is not None:
                        # tweet_date 是 naive，将其转换为与 start_date 相同的时区
                        tweet_date = tweet_date.replace(tzinfo=start_date.tzinfo)
                    
                    # 现在可以安全比较
                    if tweet_date < start_date:
                        continue
                        
                    # 检查关键词,去掉关键词过滤
                    # if not self.is_relevant(tweet.text):
                    #     continue
                    
                    # 转换为内部Tweet模型
                    tweet_model = self._convert_to_model(tweet, account)
                    filtered_tweets.append(tweet_model)
                
                self.logger.info(f"成功采集 {account['username']} 的 {len(filtered_tweets)} 条相关推文")
                all_tweets.extend(filtered_tweets)
                
                # 避免频繁请求，简化为固定等待时间
                time.sleep(4)
                
            except Exception as e:
                self.logger.error(f"采集 {account['username']} 的推文时出错: {str(e)}")
                self.logger.error(traceback.format_exc())
                # 发生错误后短暂暂停
                time.sleep(3)
        
        # 使用完后关闭浏览器
        if hasattr(self.client, "close"):
            self.client.close()
        
        # 限制返回的最大数量
        return all_tweets[:self.max_items]
    
    def _convert_to_model(self, tweet, account: Dict[str, str]) -> Tweet:
        """
        将推文对象转换为内部模型
        
        Args:
            tweet: 推文对象
            account: 账号信息
            
        Returns:
            Tweet: 内部推文模型
        """
        # 提取基本信息
        tweet_id = tweet.id
        text = tweet.text
        created_at = tweet.created_on
        
        # 获取统计数据
        likes = getattr(tweet, 'likes', 0) or 0
        retweets = getattr(tweet, 'retweets', 0) or 0
        replies = getattr(tweet, 'replies', 0) or 0
        quotes = getattr(tweet, 'quotes', 0) or 0
        
        # 获取URL
        tweet_url = getattr(tweet, 'url', f"https://x.com/{account['username']}/status/{tweet_id}")
        
        # 获取引用链接
        urls = []
        if hasattr(tweet, 'links') and tweet.links:
            urls = [link for link in tweet.links if link]
        
        # 创建内部模型
        return Tweet(
            id=str(tweet_id),
            author=account['username'],
            author_fullname=account.get('full_name', account['username']),
            content=text,
            created_at=created_at,
            likes=likes,
            retweets=retweets,
            replies=replies,
            quotes=quotes,
            url=tweet_url,
            referenced_urls=urls,
            platform="X"
        )
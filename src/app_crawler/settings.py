# Scrapy settings for app_crawler project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import time
import logging
from pathlib import Path

from scrapy.extensions.telnet import TelnetConsole

from .pipelines import PrintItemsPipeline

BOT_NAME = "app_crawler"

SPIDER_MODULES = ["app_crawler.spiders"]
NEWSPIDER_MODULE = "app_crawler.spiders"

ADDONS = {}

current_file_path = Path(__file__).resolve()
LOG_DIR = current_file_path.parent.parent.parent / "log"
LOG_DIR.mkdir(exist_ok=True)

# 扩展类
class CustomLoggingExtension:
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)-15s: %(name)s: %(levelname)s: %(message)s"
    LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"

    def spider_opened(self, spider):
        logger = logging.getLogger(spider.name)
        spider.logger.info("spider opened")

        # 确保每个logger只配置一次
        if not logger.handlers:
            log_file = (
                LOG_DIR
                / f"{time.strftime(self.LOG_DATEFORMAT, time.localtime(time.time()))}_{spider.name}.log"
            )
            spider.logger.info("init log file %s", log_file)

            formatter = logging.Formatter(self.LOG_FORMAT, self.LOG_DATEFORMAT)

            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
            logger.setLevel(self.LOG_LEVEL)


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0(+appcrawler)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 16

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 0
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
    # AppcrawlerDevSpiderMiddleware: 543,
}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    # AppcrawlerDevDownloaderMiddleware: 546,  # todo: if you use mysql output recommend to comment this out
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {
    TelnetConsole: None,
    CustomLoggingExtension: 500,
}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    # 'appcrawler_dev.pipelines.MySQLPipeline': 500,  # todo: comment this out to change to mysql output
    PrintItemsPipeline: 500  # for test items
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"

RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [429, 500, 403]

# todo: change mysql settings for yourself
MYSQL_DB_NAME = ""
MYSQL_HOST = ""
MYSQL_USER = ""
MYSQL_PASSWORD = ""

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"

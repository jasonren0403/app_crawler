# -*- coding: utf-8 -*-
from .middlewares import *

BOT_NAME = 'appcrawler_dev'

SPIDER_MODULES = ['appcrawler_dev.spiders.a360', 'appcrawler_dev.spiders.appchina',
                  'appcrawler_dev.spiders.leshangdian']
NEWSPIDER_MODULE = 'appcrawler_dev.spiders'

COMMANDS_MODULE = 'appcrawler_dev.commands'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36(+appcrawler)'

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
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    # 'appcrawler_dev.pipelines.MySQLPipeline': 500,  # todo: comment this out to change to mysql output
    'appcrawler_dev.pipelines.PrintItemsPipeline': 500  # for test items
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

RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [429, 500, 403]

# todo: change mysql settings for yourself
MYSQL_DB_NAME = ''
MYSQL_HOST = ''
MYSQL_USER = ''
MYSQL_PASSWORD = ''

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"

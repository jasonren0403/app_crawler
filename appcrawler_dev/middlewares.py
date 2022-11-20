# -*- coding: utf-8 -*-

import time

from scrapy import signals
from scrapy.exceptions import NotConfigured


class AppcrawlerDevSpiderMiddleware(object):

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        pass

    def process_start_requests(self, start_requests, spider):
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
        from twisted.python import log
        observer = log.PythonLoggingObserver()
        observer.start()
        import logging
        fhlr = logging.FileHandler(f"log/"
                                   f"{time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime(time.time()))}-{spider.name}.log")
        console = logging.StreamHandler()
        logging.basicConfig(
            filename=f"log/"
                     f"{time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime(time.time()))}-{spider.name}.log",
            level=logging.INFO,
            format='%(asctime)-15s: %(name)s: %(levelname)s: %(message)s',
            handlers=[fhlr, console]
        )


class AppcrawlerDevDownloaderMiddleware(object):

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        import re, pymysql
        db = spider.settings.get('MYSQL_DB_NAME')
        host = spider.settings.get('MYSQL_HOST')
        port = spider.settings.get('MYSQL_PORT')
        user = spider.settings.get('MYSQL_USER')
        passwd = spider.settings.get('MYSQL_PASSWORD')
        if not db or not host or not port or not user or not passwd:
            raise NotConfigured("You should configure a mysql data source at settings.py")
        db_conn = pymysql.connect(host=host, port=port, db=db, user=user, passwd=passwd)
        db_cur = db_conn.cursor()
        if re.match(r"http://www\.appchina\.com/app/([\w\.]+)", request.url):
            pkg_name = re.match(r"http://www\.appchina\.com/app/([\w\.]+)", request.url)[0]
            sql = "select app_id from app_meta where app_id = %s and store=%s"
            db_cur.execute(sql, (pkg_name, spider.name))
            if db_cur.fetchone():
                spider.logger.critical(f"App[{pkg_name}] has already crawled. Will update data")
                # raise IgnoreRequest(f"App[{pkg_name}] already crawled")
        if re.match(r"http://zhushou\.360\.cn/detail/index/soft_id/\d+", request.url):
            import requests
            req = requests.get(url=request.url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36 (+appcrawler)"})
            html = req.text
            detail = re.findall(r"'pname':\s\"([\w\.]+)\"", html, re.M)
            if detail:
                pkg_name = detail[0]
                sql = "select app_id from app_meta where app_id=%s and store = %s and download_times!=-1 and review_times!=-1"
                db_cur.execute(sql, (pkg_name, spider.name))
                if db_cur.fetchone():
                    spider.logger.debug(f"{db_cur.fetchone()}")
                    spider.logger.critical(f"App[{pkg_name}] has already crawled. Will update data")
                    # raise IgnoreRequest(f"App[{pkg_name}] already crawled")
        return None

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

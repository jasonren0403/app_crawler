# -*- coding: utf-8 -*-

from scrapy import signals
from scrapy.exceptions import NotConfigured


class AppcrawlerDevDownloaderMiddleware(object):
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        import re
        import pymysql

        db = spider.settings.get("MYSQL_DB_NAME")
        host = spider.settings.get("MYSQL_HOST")
        port = spider.settings.get("MYSQL_PORT")
        user = spider.settings.get("MYSQL_USER")
        passwd = spider.settings.get("MYSQL_PASSWORD")
        if not db or not host or not port or not user or not passwd:
            raise NotConfigured(
                "You should configure a mysql data source at settings.py"
            )
        db_conn = pymysql.connect(host=host, port=port, db=db, user=user, passwd=passwd)
        db_cur = db_conn.cursor()
        if re.match(r"http://www\.appchina\.com/app/([\w\.]+)", request.url):
            pkg_name = re.match(
                r"http://www\.appchina\.com/app/([\w\.]+)", request.url
            )[0]
            sql = "select app_id from app_meta where app_id = %s and store=%s"
            db_cur.execute(sql, (pkg_name, spider.name))
            if db_cur.fetchone():
                spider.logger.info(
                    f"App[{pkg_name}] has already crawled. Will update data"
                )
                # raise IgnoreRequest(f"App[{pkg_name}] already crawled")
        if re.match(r"https://zhushou\.360\.cn/detail/index/soft_id/\d+", request.url):
            import requests

            req = requests.get(
                url=request.url,
                headers={
                    "User-Agent": spider.settings.get("USER_AGENT")
                },
            )
            html = req.text
            detail = re.findall(r"'pname':\s\"([\w\.]+)\"", html, re.M)
            if detail:
                pkg_name = detail[0]
                sql = "select app_id from app_meta where app_id=%s and store = %s and download_times!=-1 and review_times!=-1"
                db_cur.execute(sql, (pkg_name, spider.name))
                if db_cur.fetchone():
                    spider.logger.debug(f"{db_cur.fetchone()}")
                    spider.logger.info(
                        f"App[{pkg_name}] has already crawled. Will update data"
                    )
                    # raise IgnoreRequest(f"App[{pkg_name}] already crawled")
        return None

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

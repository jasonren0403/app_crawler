# -*- coding: utf-8 -*-

import pymysql
from scrapy.exceptions import CloseSpider


class MySQLPipeline(object):
    def __init__(self, db, host, port, user, passwd):
        self.db = db
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd

    @classmethod
    def from_crawler(cls, spider):
        return cls(
            db=spider.settings.get('MYSQL_DB_NAME', ''),
            host=spider.settings.get('MYSQL_HOST', ''),
            port=spider.settings.get('MYSQL_PORT', 3306),
            user=spider.settings.get('MYSQL_USER', ''),
            passwd=spider.settings.get('MYSQL_PASSWORD', '')
        )

    def open_spider(self, spider):
        try:
            self.db_conn = pymysql.connect(host=self.host,
                                           port=self.port,
                                           db=self.db,
                                           user=self.user,
                                           passwd=self.passwd)
            spider.logger.info('MySQL connection established!')
        except pymysql.err.OperationalError:
            spider.logger.warning("Cannot open database for mysql, closing the spider")
            raise CloseSpider("Cannot open database connection")

    def close_spider(self, spider):
        if hasattr(self.db_conn, 'commit'):
            self.db_conn.commit()
        if hasattr(self.db_conn, 'close'):
            self.db_conn.close()
            spider.logger.info("MySQL connection closed")

    def process_item(self, item, spider):
        # spider.logger.info(item.__repr__())
        try:
            db_cur = self.db_conn.cursor()
            if 'user' in item:
                # 查重处理
                db_cur.execute(
                    """select * from app_comment where app_id = %s and store=%s and user=%s and content=%s """,
                    (item['app_id'], item['store'], item['user'], item['content']))
                # 是否有重复数据
                repetition = db_cur.fetchone()
                goal = 'app_comment'
                # 重复
                if repetition:
                    spider.logger.warning(
                        f"source:{item['store']} appid:{item['app_id']} user:{item['user']} already in DB table:{goal}")
                    return item
                else:
                    values = (
                        item['app_id'],
                        item.get('review_id', ''),
                        item['store'],
                        item['user'],
                        item['score'],
                        item['time'],
                        item['content']
                    )
                    sql = "insert into app_comment values(0,%s,%s,%s,%s,%s,%s,%s)"
            else:
                # 查重处理
                db_cur.execute(
                    """select * from app_meta where app_id = %s and store = %s""",
                    (item['app_id'], item['store']))
                # 是否有重复数据
                repetition = db_cur.fetchone()
                goal = 'app_meta'
                # 重复
                if repetition:
                    spider.logger.debug(f"repetition:{repetition}")
                    dl_times = repetition[7]
                    rev_times = repetition[8]
                    if dl_times == -1:
                        spider.logger.warning(f"update bad dl_time value to {item['download_times']}")
                    if rev_times == -1:
                        spider.logger.warning(f"update bad rev_time value to {item['review_times']}")
                    values = (
                        item['name'],
                        item['store'],
                        item['score'],
                        item['description'],
                        item['update_time'],
                        item['category'],
                        item.get('developer', ''),
                        item['download_times'],
                        item.get('review_times', 0),
                        item['app_id'],
                        item['md5']
                    )
                    sql = 'REPLACE INTO app_meta VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
                else:
                    values = (
                        item['name'],
                        item['store'],
                        item['score'],
                        item['description'],
                        item['update_time'],
                        item['category'],
                        item.get('developer', ''),
                        item['download_times'],
                        item['review_times'],
                        item['app_id'],
                        item['md5']
                    )
                    spider.logger.debug(f"NEW REVIEW TIMES: {item['review_times']}")
                    sql = 'INSERT INTO app_meta VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'

            db_cur.execute(sql, values)
            spider.logger.info(f"source:{item['store']} appid:{item['app_id']} ->DB table:{goal}")
            self.db_conn.commit()
            db_cur.close()

        except Exception as error:
            spider.logger.error(error)
        return item


class PrintItemsPipeline(object):
    def process_item(self, item, spider):
        spider.logger.info(item)
        return item

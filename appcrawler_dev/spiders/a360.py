# -*- coding: utf-8 -*-
import time

import scrapy
from scrapy.exceptions import DropItem
from scrapy.linkextractors import LinkExtractor
from itemloaders.processors import Join, MapCompose
from scrapy.selector import Selector
from scrapy.spiders import CrawlSpider

from ..items import AppInfo, AppComment, AppInfoLoader, AppCommentLoader


class A360Spider(CrawlSpider):
    name = '360'
    allowed_domains = ['zhushou.360.cn']

    custom_settings = {
        'CONCURRENT_REQUESTS': 64,
        'DOWNLOAD_DELAY': 1,
        # "DOWNLOAD_TIMEOUT": 5,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 32,
        'LOG_LEVEL': 'INFO',
        'LOG_STDOUT': True,
        # 'LOG_FILE': f"""log/{time.strftime('%Y-%m-%d', time.localtime(time.time()))}-{name}.log"""
    }

    PAGE_OFFSET = 1  # where to start crawling default 1
    CRAWL_TO = 2
    MAX_PAGE_DEFAULT = 10  # 10
    MAX_COMMENT_OFFSET = 500  # 最多抓几条评论
    """
    Set to true to crawl app meta
    """
    CRAWL_META = True

    """
    Set to true to count available app counts
    """
    COUNT_APP_NUM = False
    bad_app_count = 0
    week_updates = 0
    app_count = 0

    """
    Set to true to crawl app comments
    """
    CRAWL_COMMENT = False

    def start_requests(self):
        yield scrapy.Request(url=f"http://zhushou.360.cn/list/index/cid/2",
                             meta={
                                 "source": "game"
                             }, callback=self.max_page, dont_filter=True)
        yield scrapy.Request(url=f"https://zhushou.360.cn/list/index/cid/1",
                             meta={
                                 "source": "software"
                             }, callback=self.max_page, dont_filter=True)

    def max_page(self, response):
        import js2py
        has_pg_js = response.css(".main script:not([src])::text").extract_first()
        ending_page = 0
        try:
            context = js2py.EvalJs()
            context.execute(f"{'function showPages(){};showPages.prototype.printHtml=function(){};'}{has_pg_js}")
            ending_page = min(int(context.pg.pageCount), self.CRAWL_TO)
        except Exception:
            ending_page = self.MAX_PAGE_DEFAULT
            self.logger.warning(f"cannot get max page for {response.meta['source']}, starting from page 1")
        finally:
            starting_page = self.PAGE_OFFSET if self.PAGE_OFFSET <= ending_page else 1
            self.logger.info(f'{response.meta["source"]}: from page {starting_page} to {ending_page}')
            for i in range(starting_page, ending_page + 1):
                match response.meta["source"]:
                    case "game":
                        # 游戏综合榜
                        url = f'http://zhushou.360.cn/list/index/cid/2/order/weekpure/?page={i}'
                    case "software":
                        # 软件综合榜
                        url = f"http://zhushou.360.cn/list/index/cid/1/order/weekdownload/?page={i}"
                    case _:
                        raise ValueError(f"Bad value {response.meta['source']}")
                yield scrapy.Request(url=url,
                                     meta={
                                         "source": response.meta["source"],
                                         "page": i,
                                         "download_timeout": 5
                                     }, callback=self.from_pages, dont_filter=True)

    def from_pages(self, response):
        link_ext = LinkExtractor(restrict_css='.icon_box>.iconList>li>h3',
                                 allow=r"/detail/index/soft_id/\d+")
        links = link_ext.extract_links(response)
        for link in links:
            try:
                yield scrapy.Request(url=link.url, meta={
                    "source": response.meta.get("source"),
                    "page": response.meta.get("page"),
                    "download_timeout": 5
                }, callback=self.parse_item_app)
            except Exception as e:
                self.logger.warning(f"{e} when trying to parse {link}")

    def parse_item_app(self, response):
        self.logger.info(
            f'[{response.meta.get("source")}-Page{response.meta.get("page")}]: Parsing appid[{response.url.split("/")[-1]}] meta contents')
        selector = Selector(response=response, type='html')
        itemLoader = AppInfoLoader(item=AppInfo(), selector=selector)
        import re, json, urllib.parse, time, requests
        scripts = response.css('script:not([src])').extract()
        detail = None
        for script in scripts:
            if '详情页的命名空间' in script:
                detail = re.findall(r'var\s+detail\s+=\s+\(function\s+\(\)\s+{\s+return\s+({[\w\W]*});\s+}\)', script,
                                    re.M)
                break
        if not detail:
            raise DropItem(f'Cannot find detail on page {response.url}!')
        detail = detail[0]
        detail = re.sub(r'[\t\r\n]', '', detail)
        detail = re.sub(r'\'', '"', detail)
        try:
            de = json.loads(detail)
            sid = de.get('sid') or response.url.split("/")[-1]
            type = de.get('type', '')  # soft/game
            sname = de.get('sname', '')  # 软件名称
            baike_name = de.get('baike_name', '')
            md5 = de.get('filemd5')
            pname = de.get('pname', '')  # 软件包名
            from w3lib.html import remove_tags
            if self.COUNT_APP_NUM:
                base_info = re.sub(r'[\t\r\n\s]+', ' ', remove_tags(response.css('.base-info').extract_first()))
                match_public_time = re.findall(r"更新时间：(\d{4}-(0\d|1[012])-([012]\d|3[01]))", base_info)
                import datetime
                from dateutil.parser import parse
                if match_public_time and (datetime.datetime.now() - parse(match_public_time[0][0])).days <= 7:
                    self.week_updates += 1
                self.app_count += 1
                self.logger.info(f'{self.app_count} apps total, {self.week_updates} week updates')
            if self.CRAWL_META:
                if not (type and sname and baike_name and pname):
                    raise DropItem('Corrupted app item!')
                # bug workaround: review_times may result in error if review_times is 0, add css selector for interface
                # fallback
                times = response.css("span.review-count-all::text").extract_first()
                itemLoader.add_value("review_times", times)
                itemLoader.add_value("store", "360")
                itemLoader.add_value("name", sname)
                itemLoader.add_value("app_id", pname)
                itemLoader.add_value("md5", md5)
                score = response.css('#app-info-panel span.s-1.js-votepanel::text').extract_first()
                # 360商店是10分制的，将其与其他商店统一为1分制
                itemLoader.add_value("score", round(float(score) / 10, 2))
                dl = response.css('#app-info-panel span.s-3::text').extract_first()
                # ['下载：467万次', '14.03M']
                assert re.match(r"下载：\d+[万|亿]?次", dl)
                itemLoader.add_value("download_times", dl.replace('下载：', ''))
                query = urllib.parse.urlencode({
                    "baike": baike_name,
                    "_": int(round(time.time() * 1000)),
                    "c": "message",
                    "a": "getmessagenum"
                })
                # self.logger.debug(f"baike: {baike_name}")
                c = requests.get(url=f"https://comment.mobilem.360.cn/comment/getLevelCount?{query}",
                                 headers={
                                     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36(+appcrawler)',
                                     'Referer': 'http://zhushou.360.cn/'
                                 })
                resp = c.json()
                review_times = resp.get('mesg')
                self.logger.info(f"review times from {response.url}:{resp}")
                if times == '0':
                    itemLoader.replace_value('review_times', review_times or times)

                itemLoader.add_css("description", '.breif::text', Join(''))
                if not response.css('.breif::text'):
                    # self.logger.warn(c.url)
                    self.logger.warn(f"no .breif::text content in {response.url}")
                    itemLoader.replace_css("description", '#html-brief>p:not([style="text-align:center"])', Join(''))
                    if not response.css('#html-brief>p:not([style="text-align:center"])'):
                        itemLoader.replace_css("description", '#html-brief p::text', MapCompose(str.strip), Join(''))

                base_info = re.sub(r'[\t\r\n\s]+', ' ', remove_tags(response.css('.base-info').extract_first()))
                match_developer = re.findall(
                    r"作者：([\u4e00-\u9fa5\u3002\uff1b\uff0c\uff1a\u201c\u201d\uff08\uff09\u3001\uff1f\u300a\u300b\S]+)",
                    base_info)
                match_public_time = re.findall(r"更新时间：(\d{4}-(0\d|1[012])-([012]\d|3[01]))", base_info)
                if not (match_developer and match_public_time):
                    raise DropItem(f"No developer or public_time, don't scrap this item {response.url}")
                itemLoader.add_value("developer", match_developer[0])
                itemLoader.add_css("category", '.app-tags>a::text', Join(','))
                itemLoader.add_value("category", '<NO CATEGORY SPECIFIED>')
                # [('2020-04-21', '04', '21')]
                itemLoader.add_value("update_time", match_public_time[0][0])
                item = itemLoader.load_item()
                yield item
            if self.CRAWL_COMMENT:
                yield scrapy.Request(url=f"https://comment.mobilem.360.cn/comment/getComments?"
                                         f"baike={urllib.parse.quote(baike_name)}&start=0&count=50&_={int(round(time.time() * 1000))}",
                                     callback=self.parse_comment_app, dont_filter=True,
                                     meta={
                                         'sid': sid,
                                         'type': type,
                                         'appname': sname,
                                         'appid': pname,
                                         'offset': 0,
                                         'baike_name': baike_name
                                     })
        except Exception:
            self.bad_app_count += 1
            raise DropItem(f'Corrupted app item! Bad app items total: {self.bad_app_count}')

    def parse_comment_app(self, response):
        appid = response.meta.get("appid")
        offset = response.meta.get("offset", 0)
        baike_name = response.meta.get("baike_name")
        self.logger.info(f'Parsing appid[{appid} offset:{offset}] comments')
        import time, urllib.parse
        resp_d = response.json()
        if resp_d and not resp_d["error"]:
            comment_data = resp_d["data"]
            total = comment_data['total']
            comment_list = comment_data["messages"]
            if comment_list:
                parsed = 0
                for comment in comment_list:
                    # self.logger.warn(comment)

                    if not comment.get('content', ''):
                        parsed += 1
                        continue
                    try:
                        selector = scrapy.Selector(response=response, type='html')
                        itemLoader = AppCommentLoader(item=AppComment(), selector=selector)
                        itemLoader.add_value("app_id", appid)
                        itemLoader.add_value("review_id", comment['msgid'])
                        itemLoader.add_value("store", "360")
                        itemLoader.add_value("user", comment['username'])
                        itemLoader.add_value("score", comment["score"])  # _type: best好评 | good中评 | bad差评
                        itemLoader.add_value("content", comment.get('content'))
                        itemLoader.add_value("time", comment["create_time"])  # or comment['update_time']
                        yield itemLoader.load_item()
                        parsed += 1
                    except Exception:
                        pass
                current = offset + parsed
                if current < total and current < self.MAX_COMMENT_OFFSET:
                    yield scrapy.Request(callback=self.parse_comment_app, meta={
                        'appid': appid,
                        'offset': current,
                        'baike_name': baike_name
                    }, url=f"https://comment.mobilem.360.cn/comment/getComments?"
                           f"baike={urllib.parse.quote(baike_name)}&start={offset + parsed}&count=50&_={int(round(time.time() * 1000))}",
                                         dont_filter=True)
        else:
            self.logger.warn(
                f"error code {resp_d['errno']} received from server when parsing {response.url}, msg:{resp_d['error']}")

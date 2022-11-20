# -*- coding: utf-8 -*-
import scrapy
from scrapy.exceptions import DropItem, DontCloseSpider
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider

from ..items import AppInfo, AppInfoLoader, AppComment, AppCommentLoader
import time


class LeshangdianSpider(CrawlSpider):
    name = 'leshangdian'
    allowed_domains = ['lenovomm.com']

    custom_settings = {
        'CONCURRENT_REQUESTS': 96,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 32,
        'LOG_LEVEL': 'INFO',
        # 'LOG_STDOUT': True,
        'LOG_FILE': f"""log/{time.strftime('%Y-%m-%d', time.localtime(time.time()))}-{name}.log"""
    }

    PAGE_OFFSET = 1  # where to start crawling default 1
    MAX_PAGE = 2  # 5
    MAX_COMMENT_OFFSET = 500  # 最多抓几条评论

    start_urls = [
        # Apps
        # f'https://www.lenovomm.com/apps/1038/0?p={PAGE_OFFSET or 1}&type=1',  # 影视 视频
        f'https://www.lenovomm.com/apps/1028/0?p={PAGE_OFFSET or 1}&type=1',  # 聊天 社交
        # f'https://www.lenovomm.com/apps/1030/0?p={PAGE_OFFSET or 1}&type=1',  # 系统 优化
        # f'https://www.lenovomm.com/apps/1034/0?p={PAGE_OFFSET or 1}&type=1',  # 实用 工具
        # f'https://www.lenovomm.com/apps/1052/0?p={PAGE_OFFSET or 1}&type=1',  # 新闻 阅读
        # f'https://www.lenovomm.com/apps/1048/0?p={PAGE_OFFSET or 1}&type=1',  # 拍摄 美图
        # f'https://www.lenovomm.com/apps/1040/0?p={PAGE_OFFSET or 1}&type=1',  # 音乐 铃声
        # f'https://www.lenovomm.com/apps/2351/0?p={PAGE_OFFSET or 1}&type=1',  # 购物 优惠
        # f'https://www.lenovomm.com/apps/1042/0?p={PAGE_OFFSET or 1}&type=1',  # 生活服务
        # f'https://www.lenovomm.com/apps/1060/0?p={PAGE_OFFSET or 1}&type=1',  # 母婴 儿童
        # f'https://www.lenovomm.com/apps/1046/0?p={PAGE_OFFSET or 1}&type=1',  # 地图 出行
        # f'https://www.lenovomm.com/apps/1058/0?p={PAGE_OFFSET or 1}&type=1',  # 考试 学习
        # f'https://www.lenovomm.com/apps/1062/0?p={PAGE_OFFSET or 1}&type=1',  # 桌面 美化
        # f'https://www.lenovomm.com/apps/1032/0?p={PAGE_OFFSET or 1}&type=1',  # 办公 效率
        # f'https://www.lenovomm.com/apps/1054/0?p={PAGE_OFFSET or 1}&type=1',  # 理财 金融
        # f'https://www.lenovomm.com/apps/2441/0?p={PAGE_OFFSET or 1}&type=1',  # 智能硬件
        # f'https://www.lenovomm.com/apps/2461/0?p={PAGE_OFFSET or 1}&type=1',  # 运动 健身
        # f'https://www.lenovomm.com/apps/2463/0?p={PAGE_OFFSET or 1}&type=1',  # 医疗 健康
        # Games
        # f'https://www.lenovomm.com/apps/2397/0?p={PAGE_OFFSET or 1}&type=2',  # 休闲益智
        # f'https://www.lenovomm.com/apps/2383/0?p={PAGE_OFFSET or 1}&type=2',  # 棋牌游戏
        # f'https://www.lenovomm.com/apps/2373/0?p={PAGE_OFFSET or 1}&type=2',  # 角色扮演
        # f'https://www.lenovomm.com/apps/2367/0?p={PAGE_OFFSET or 1}&type=2',  # 动作冒险
        # f'https://www.lenovomm.com/apps/2395/0?p={PAGE_OFFSET or 1}&type=2',  # 音乐舞蹈
        # f'https://www.lenovomm.com/apps/2389/0?p={PAGE_OFFSET or 1}&type=2',  # 体育竞技
        # f'https://www.lenovomm.com/apps/2481/0?p={PAGE_OFFSET or 1}&type=2',  # 飞行射击
        # f'https://www.lenovomm.com/apps/2501/0?p={PAGE_OFFSET or 1}&type=2',  # 特色分类
        # f'https://www.lenovomm.com/apps/2521/0?p={PAGE_OFFSET or 1}&type=2',  # 经营策略
    ]

    """
    Set true to crawl app meta
    """
    CRAWL_META = True

    """
    Set true to count available app counts
    """
    COUNT_APP_NUM = True
    app_num = 0
    bad_app_count = 0
    week_updates = 0

    """
    Set true to crawl app comments
    """
    CRAWL_COMMENT = False

    """
    Use client id to get app comments from API
    """
    client_id = "21552078-1a2-2-9999-1-3-1_240_i100000000000012t19700101000000001_c25434d1p4"

    def parse_start_url(self, response, **kwargs):
        self.logger.debug(f'parse_start_url:{response.url}')
        import json
        current_page = response.meta.get('page', self.PAGE_OFFSET)

        link_ext = LinkExtractor(restrict_css='.cate-list>li')
        links = link_ext.extract_links(response)

        s = response.css('body>script:not([async])::text').extract_first()
        c = json.loads(s.replace(';__NEXT_LOADED_PAGES__=[];__NEXT_REGISTER_PAGE=function(r,'
                                 'f){__NEXT_LOADED_PAGES__.push([r, f])}', '').replace('__NEXT_DATA__ = ', ''))

        for link in links:
            yield scrapy.Request(url=link.url, callback=self.extract_app_link, meta={
                "category": link.text,
                "frompage": current_page,
                "tagDict": c["props"]["pageProps"]["categoryList"]
            })

    def extract_app_link(self, response):
        page_max = min(int(response.css('.page-num > .num:not(.active)::text').extract_first()), self.MAX_PAGE)
        self.logger.info(f'Page [{response.meta.get("frompage")}/{page_max}]'
                         f'(MAX:{page_max})'
                         f'Request from start link. Category:{response.meta.get("category")}')
        current_page = int(response.meta.get("frompage"))
        self.logger.debug(f"extracting link from {response.url}")
        link_ext = LinkExtractor(restrict_css='.list>.item-wrapper', attrs='href')
        links = link_ext.extract_links(response)
        length = len(links)
        self.logger.debug(
            f"{response.meta.get('category')}-Page {response.meta.get('frompage')} : "
            f"{[f'{link.url}:{link.text}' for link in links]}")
        for link in links:
            self.logger.info(
                f'Category[{response.meta.get("category")}: Page {response.meta.get("frompage")} '
                f'{links.index(link) + 1}/{length}] Requesting app meta...')
            yield scrapy.Request(url=link.url, callback=self.parse_app_meta, meta={
                "category": response.meta.get("category"),
                "tagDict": response.meta.get("tagDict")
            })

        page_ele = response.css('.page-wrapper>a::attr(href)').extract()
        if current_page == 1:
            next_url = response.urljoin(page_ele[0])
        else:
            if len(page_ele) == 2:
                next_url = response.urljoin(page_ele[1])
            else:
                next_url = ''
                # self.logger.warning(page_ele)
        if current_page <= page_max and next_url and '下一页' in response.css('.page-wrapper>a::text').extract():
            if self.COUNT_APP_NUM:
                yield scrapy.Request(url=next_url, callback=self.extract_app_link, meta={
                    "frompage": current_page + 1,
                    "category": response.meta.get("category")
                })
            elif current_page <= self.MAX_PAGE:
                yield scrapy.Request(url=next_url, callback=self.extract_app_link, meta={
                    'frompage': current_page + 1,
                    "category": response.meta.get("category")
                })

    def parse_app_meta(self, response):
        import json
        try:
            s = response.css('body>script:not([async])::text').extract_first()
            c = json.loads(s.replace(';__NEXT_LOADED_PAGES__=[];__NEXT_REGISTER_PAGE=function(r,'
                                     'f){__NEXT_LOADED_PAGES__.push([r, f])}', '').replace('__NEXT_DATA__ = ', ''))

            q = c["props"]["pageProps"]
            name = q["pkgName"] or q["appInfo"]["name"]
            app_id = c["query"]["pkg"] or q["appInfo"]["packageName"]
            category = c["query"]["cateName"]
            md5 = q["appInfo"]["apkmd5"]
            # leshangdian give public time in millis(13 digits)
            public_time = int(q["appInfo"]["publishDate"] / 1000)
            download_times = q["appInfo"]["realDownCount"]
            review_times = q["appInfo"].get("commentsNum", 0)
            description = q["appInfo"]["description"]
            store = "leshangdian"
            developer = q["appInfo"]["developerName"]
            score = round(q["appInfo"]["averageStar"] / 5, 2)
            if self.COUNT_APP_NUM:
                import time
                if int(time.time()) - public_time <= 60 * 60 * 24 * 7:
                    self.week_updates += 1
                self.app_num += 1
                self.logger.info(f'{self.app_num} apps total, {self.week_updates} week updates total')

            if self.CRAWL_META:
                self.logger.info(f'Parsing app meta [{app_id}]')
                selector = scrapy.Selector(response=response, type='html')
                itemLoader = AppInfoLoader(item=AppInfo(), selector=selector)
                itemLoader.add_value("name", name)
                itemLoader.add_value("store", store)
                itemLoader.add_value("score", str(score))
                itemLoader.add_value("description", description)
                itemLoader.add_value("update_time", str(public_time))
                itemLoader.add_value("category", category)
                itemLoader.add_value("developer", developer)
                itemLoader.add_value("download_times", download_times)
                itemLoader.add_value("review_times", review_times)
                itemLoader.add_value("app_id", app_id)
                itemLoader.add_value("md5", md5)
                yield itemLoader.load_item()
            if self.CRAWL_COMMENT:
                self.logger.info(f'Parsing app [{app_id}] comment: start from offset 1')
                yield scrapy.Request(
                    url=f'https://www.lenovomm.com/api/comment?bizCode=APP&bizIdentity={app_id}&si=1&c=40'
                        f'&clientid={self.client_id}',
                    callback=self.parse_comments, meta={
                        "app_id": app_id,
                        "offset": 1,
                        "client_id": self.client_id,
                        "store": store
                    })
        except Exception:
            self.bad_app_count += 1
            raise DropItem(
                f"Can't find NEXT_DATA on page or Item corrupted! Incomplete meta app num {self.bad_app_count}")

    def parse_comments(self, response):
        # https://www.lenovomm.com/api/comment?bizCode=APP&bizIdentity={APPID}&si={START_INDEX}&c=40
        # &clientid={} if clientid is not set error 308 will be raised by server
        self.logger.info(
            f'Parsing app [{response.meta.get("app_id")}] comment. Offset:{response.meta.get("offset", 1)}')
        c = response.json()
        parsed = 0
        try:
            if not c['success']:
                self.logger.warning(
                    f'Received error from server. Error code:{c.get("errorCode", "unknown code")} '
                    f'ErrorMessage:{c.get("message", "unknown message")}')
                raise DontCloseSpider()
            if not response.meta.get("client_id"):
                self.logger.warning(f'Cannot get comment without client id!')
                raise DontCloseSpider()
            dt = c["data"]["datalist"]
            total_num = c["data"]["totalCount"]
            if self.CRAWL_COMMENT and dt:
                for e in dt:
                    selector = scrapy.Selector(response=response, type='html')
                    itemLoader = AppCommentLoader(item=AppComment(), selector=selector)
                    comment_info = e["comment"]
                    review_id = comment_info["id"]
                    app_id = response.meta.get("app_id")
                    store = response.meta.get("store")
                    user = comment_info["userName"]  # may use comment_info["userId"]
                    score = comment_info["grade"]
                    review_time = comment_info["createDate"]
                    content = comment_info["content"]

                    itemLoader.add_value("app_id", app_id)
                    itemLoader.add_value("review_id", review_id)
                    itemLoader.add_value("store", store)
                    itemLoader.add_value("user", user)
                    itemLoader.add_value("score", score)
                    itemLoader.add_value("time", review_time)
                    itemLoader.add_value("content", content)
                    parsed += 1
                    yield itemLoader.load_item()
                current_num = response.meta.get("offset", 1) + parsed
                if current_num <= total_num and current_num <= self.MAX_COMMENT_OFFSET:
                    yield scrapy.Request(
                        url=f'https://www.lenovomm.com/api/comment?bizCode=APP&bizIdentity={response.meta.get("app_id")}&si={current_num}&c=40'
                            f'&clientid={response.meta.get("client_id")}', callback=self.parse_comments,
                        meta={
                            "app_id": response.meta.get("app_id"),
                            "offset": current_num,
                            "client_id": self.client_id,
                            "store": response.meta.get("store")
                        })
        except Exception:
            self.logger.warning(f"Error in parsing comments when trying to access url: {response.url}")
            # self.logger.warning(f"Received contents: {c}")

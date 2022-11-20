# -*- coding: utf-8 -*-
import time

import scrapy
from scrapy.exceptions import DropItem
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from ..items import AppInfo, AppComment, AppInfoLoader, AppCommentLoader


class AppchinaSpider(CrawlSpider):
    name = 'appchina'  # 应用汇
    allowed_domains = ['appchina.com']
    custom_settings = {
        'CONCURRENT_REQUESTS': 48,
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 16,
        'LOG_LEVEL': 'INFO',
        # 'LOG_STDOUT':True
        'LOG_FILE': f"""log/{time.strftime('%Y-%m-%d', time.localtime(time.time()))}-{name}.log"""
    }
    PAGE_OFFSET = 1  # where to start crawling default 1
    start_urls = [f'http://www.appchina.com/category/40/1_1_{PAGE_OFFSET or 1}_1_0_0_0.html',
                  f'http://www.appchina.com/category/30/1_1_{PAGE_OFFSET or 1}_1_0_0_0.html']
    # 1_1_{page}_1_xxx sort by dl
    MAX_PAGE = 5
    MAX_COMMENT_PAGE = 50
    """
    Set true to crawl app meta
    """
    CRAWL_META = True

    """
    Set true to count available app counts
    """
    COUNT_APP_NUM = False
    bad_app_count = 0
    week_updates = 0

    """
    Set true to crawl app comments
    """
    CRAWL_COMMENT = False

    rules = (
        Rule(LinkExtractor(restrict_css=".app-list>.app",
                           deny=(r"com\.appchina\.anpai\.\d+", r"com\.appchina\.yugao\.\d+")),
             callback='parse_item_app', follow=False),
    )

    def parse_start_url(self, response, **kwargs):
        current_page = int(response.meta.get('page', self.PAGE_OFFSET))
        # print(response.meta)
        source = response.meta.get('source', 'soft' if response.url.split('/')[-2] == '30' else 'game')
        self.logger.info(f'Source:{source} Current page:{current_page}')
        next_link = response.css('.next::attr(href)').extract()[0]
        dates = response.css('.update-date::text').extract()
        date_list = [i.strip(' 更新') for i in dates]
        import datetime
        from dateutil.parser import parse
        updates = len([parse(i) for i in date_list if (datetime.datetime.now() - parse(i)).days <= 7])
        if next_link and self.COUNT_APP_NUM:
            app_count = int(response.meta.get("appcount", 0))
            self.week_updates = int(response.meta.get("week_updates", 0))
            link_ext = LinkExtractor(restrict_css='.app-list>.app',
                                     deny=(r"com\.appchina\.anpai\.\d+", r"com\.appchina\.yugao\.\d+"))
            links = link_ext.extract_links(response)
            app_count += len(links)
            self.week_updates += updates
            # self.logger.info(f'{response.urljoin(next_link)}')
            self.logger.info(f'{source}-{app_count} apps total, {self.week_updates} week updates (+{updates})')
            yield scrapy.Request(url=response.urljoin(next_link), callback=self.parse_start_url, meta={
                "page": int(next_link.split('/')[-1].split('_')[2]),
                "source": 'game' if next_link.split('/')[2] == '40' else 'soft',  # 30
                "appcount": app_count,
                "week_updates": self.week_updates
            })
        elif next_link and current_page <= self.MAX_PAGE:
            yield scrapy.Request(url=response.urljoin(next_link), callback=self.parse_start_url, meta={
                "page": next_link.split('/')[-1].split('_')[0],
                "source": 'game' if next_link.split('/')[2] == '40' else 'soft'  # 30
            })

    def parse_item_app(self, response):
        if not self.COUNT_APP_NUM:
            self.logger.info(f'Parsing app[{response.url.split("/")[-1]}] meta contents')
        import re
        name = response.css('.app-detail .app-name::text').extract_first()
        if self.CRAWL_META:
            selector = scrapy.Selector(response=response, type='html')
            itemLoader = AppInfoLoader(item=AppInfo(), selector=selector)

            itemLoader.add_css("name", '.app-detail .app-name::text')
            itemLoader.add_value("store", 'appchina')
            itemLoader.add_css("score", '.app-detail .app-statistic::text')
            itemLoader.add_css("description", '.main-info>.art-content')
            app_meta = response.css('.app-other-info-intro> .art-content::text').extract()
            itemLoader.add_css("review_times", '.app-detail .app-statistic::text')
            try:
                app_meta = {val.split("：")[0]: val.split("：")[1] for val in app_meta if
                            re.match(r"([\u4e00-\u9fa5\w]+)：(.+)", val)}
                self.logger.info(f'App-meta:{app_meta}')
                itemLoader.add_value("update_time", app_meta.get('更新', '') or app_meta.get('update', ''))
                itemLoader.add_value("category", app_meta.get('分类', '') or app_meta.get('category', ''))
                if '开发者' in app_meta or 'developer' in app_meta:
                    developer = app_meta.get('开发者', '') or app_meta.get('developer', '')
                    itemLoader.add_value("developer", developer)
                else:
                    text = response.css('.app-other-info-intro>div>p::text').extract_first()
                    if text and text.strip() == '开发者：':
                        developer = response.css('.app-other-info-intro>div>a::text').extract_first()
                        itemLoader.add_value("developer", developer)
                        # download times not available in appchina
                        itemLoader.add_value("download_times", -1)

                        item_script = response.xpath('/html/body/script').extract_first()
                        # var md5 = xxxxxx
                        # var packagename = 'xxxxx'
                        package_name = re.findall(r"var\s+packagename\s+=\s+'([\w\.]+)'", item_script, re.M)
                        itemLoader.add_value("app_id", package_name[0] or response.url.split("/")[-1])
                        # if needed
                        app_md5 = re.findall(r"var\s+md5\s+=\s+'(\w+)'", item_script, re.M)
                        if not app_md5:
                            raise DropItem('No md5 info! ')
                        else:
                            md5 = app_md5[0]
                            itemLoader.add_value("md5", md5)
                            yield itemLoader.load_item()
            except Exception as e:
                self.logger.error(e)
                raise DropItem(f'error in parsing app_meta when parsing {response.url}')

        remark_link = response.css('.check-all-remark::attr(href)').extract_first()
        if self.CRAWL_COMMENT and remark_link:
            yield scrapy.Request(url=response.urljoin(remark_link), callback=self.parse_comments, meta={
                "appid": response.url.split("/")[-1],
                "appname": name,
                "store": 'appchina'
            })

    def parse_comments(self, response):
        from lxml.html import soupparser
        current_page = response.meta.get('page', 1)
        self.logger.info(f'Parsing app[{response.url.split("/")[-2]}] comments. Page [{current_page}]')
        for comment in response.css('.comments-list>li').extract():
            selector = scrapy.Selector(response=response, type='html')
            itemLoader = AppCommentLoader(item=AppComment(), selector=selector)
            demo = soupparser.fromstring(comment)
            comment_item = demo.xpath('//p[@class="comment-content"]/text()')
            user = demo.xpath('//div/h2[@class="comment-nickname"]/text()')
            date = demo.xpath('//div/span[@class="date"]/text()')
            if not comment_item or not user or not date:
                self.logger.warn('Skipped an corrupted comment content')
                continue
            itemLoader.add_value("content", comment_item[0])
            itemLoader.add_value("user", user[0])
            itemLoader.add_value("time", date[0])
            itemLoader.add_value("store", response.meta.get('store', 'appchina'))
            itemLoader.add_value("app_id", response.meta.get('appid', response.url.split("/")[-2]))
            itemLoader.add_value("score", -1)
            itemLoader.add_value("review_id", '')
            yield itemLoader.load_item()
        next_page = response.css('.next::attr(href)').extract_first()
        if next_page and current_page <= self.MAX_COMMENT_PAGE:
            import re
            page_nextnum = re.findall(r"comments_(\d+)\.html", next_page.split('/')[-1])
            # comments_1.html
            num = page_nextnum[0]
            yield scrapy.Request(url=response.urljoin(next_page), callback=self.parse_comments, meta={
                'page': int(num)
            })

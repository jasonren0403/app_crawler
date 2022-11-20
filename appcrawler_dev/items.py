# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.exceptions import DropItem
import itemloaders
from itemloaders import ItemLoader
from w3lib.html import remove_tags, remove_comments


class AppInfoLoader(ItemLoader):
    default_output_processor = itemloaders.processors.TakeFirst()


class AppCommentLoader(ItemLoader):
    default_output_processor = itemloaders.processors.TakeFirst()


class ItemCleaner:
    @classmethod
    def datestrTotimestamp(cls, value) -> int:
        # timestamp:10 s

        import re, time, datetime, calendar
        if not value: return int(time.mktime((1970, 1, 1, 8, 0, 0, 3, 1, 0)))
        if re.match(r"\d{10,14}", value): return int(value)
        try:
            timeArray = time.strptime(value, "%Y-%m-%d %H:%M:%S")
            return int(time.mktime(timeArray))
        except Exception:
            pass
        if not re.match(r"\d{4}-(0\d|1[012])-([012]\d|3[01])", value):
            # x 个月前/ x 天前 / x 小时前 / x 分钟前
            now = datetime.datetime.now()
            match_month = re.findall(r"(\d+)个月前", value)
            match_day = re.findall(r"(\d+)天前", value) or re.findall(r"(\d+)日前", value)
            match_hour = re.findall(r"(\d+)小时前", value)
            match_minute = re.findall(r"(\d+)分钟前", value)
            match_second = re.findall(r"(\d+)秒前", value)
            if not (match_month or match_day or match_hour or match_minute or match_second):
                raise DropItem(f"Invalid time format, ignored. current value {value}")
            elif match_month:
                monthdelta = int(match_month[0])
                month = now.month - 1 - monthdelta
                year = now.year + int(month / 12)
                month = month % 12 + 1
                day = min(now.day, calendar.monthrange(year, month)[1])
                modified_date = now.replace(year=year, month=month, day=day)
            elif match_day:
                modified_date = now - datetime.timedelta(days=int(match_day[0]))
            elif match_hour:
                modified_date = now - datetime.timedelta(hours=int(match_hour[0]))
            elif match_minute:
                modified_date = now - datetime.timedelta(minutes=int(match_minute[0]))
            else:
                # second
                modified_date = now - datetime.timedelta(seconds=int(match_second[0]))
            ts = int(time.mktime(modified_date.timetuple()))
        else:
            timeArray = time.strptime(value, "%Y-%m-%d")
            ts = int(time.mktime(timeArray))
        return ts

    @classmethod
    def cleanhtmlentites(cls, value: str) -> str:
        import re
        content = remove_tags(value)
        content = remove_comments(content)
        # 移除空格 换行
        return re.sub(r'[\t\r\n\s]', '', content)

    @classmethod
    def cleanScore(cls, value) -> float:
        try:
            return float(value)
        except ValueError:
            pass
        import re
        # appchina
        match = re.findall(r"(\d+)%好评\(\d+人\)", value, re.M)
        if match:
            # 0 好评 is also filtered because it doesn't match
            return int(match[0]) / 100
        # 360
        match2 = re.match(r"(\d+)\.(\d+)", value)
        if match2:
            return float(match2[0])
        return -1.0

    @classmethod
    def cleanReviewTime(cls, value) -> int:
        try:
            return int(value)
        except ValueError:
            pass
        import re
        # appchina
        match = re.findall(r"\d+%好评\((\d+)人\)", value, re.M)
        if match:
            return int(match[0])
        return -1

    @classmethod
    def dlTimestrtoInt(cls, value) -> int:
        if isinstance(value, int):
            return value
        import re
        match = re.findall(r"(\d+[万|亿]?)次", value)
        if match:
            if '万' in match[0]:
                s = match[0].replace('万', '')
                return int(s) * 10000
            elif '亿' in match[0]:
                s = match[0].replace('亿', '')
                return int(s) * 1_0000_0000
            else:
                return int(match[0])
        return -1

    @classmethod
    def cleanscore(cls, value) -> int:
        try:
            return int(value)
        except Exception:
            return -1


class AppInfo(scrapy.Item):
    name = scrapy.Field()
    store = scrapy.Field()
    score = scrapy.Field(serializer=float, input_processor=itemloaders.processors.Compose(itemloaders.processors.TakeFirst(),
                                                                                          ItemCleaner.cleanScore))
    description = scrapy.Field(serializer=str, input_processor=itemloaders.processors.MapCompose(ItemCleaner.cleanhtmlentites))
    update_time = scrapy.Field(serializer=int, input_processor=itemloaders.processors.Compose(itemloaders.processors.TakeFirst(),
                                                                                              ItemCleaner.datestrTotimestamp))
    category = scrapy.Field()
    developer = scrapy.Field(serializer=str)
    download_times = scrapy.Field(serializer=int, input_processor=itemloaders.processors.MapCompose(ItemCleaner.dlTimestrtoInt))
    review_times = scrapy.Field(serializer=int, input_processor=itemloaders.processors.Compose(itemloaders.processors.TakeFirst(),
                                                                                               ItemCleaner.cleanReviewTime))
    app_id = scrapy.Field()
    md5 = scrapy.Field()


class AppComment(scrapy.Item):
    content = scrapy.Field(serializer=str, input_processor=itemloaders.processors.MapCompose(ItemCleaner.cleanhtmlentites))
    time = scrapy.Field(serializer=int, input_processor=itemloaders.processors.Compose(itemloaders.processors.TakeFirst(),
                                                                                       ItemCleaner.datestrTotimestamp))
    user = scrapy.Field()
    score = scrapy.Field(serializer=int)
    app_id = scrapy.Field()
    store = scrapy.Field()
    review_id = scrapy.Field()

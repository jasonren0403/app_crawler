# 应用程序爬虫-scrapy
## 如何开始爬取
入口文件是 `run.py`，根据提示交互即可

支持多种日志输出方式：文件(`LOG_FILE`)或标准输出(`LOG_STDOUT`)，但暂不支持同时做这两个输出
## 支持以下应用软件商店
* [360手机助手](http://zhushou.360.cn/) - `spiders/a360.py`
* [应用汇](http://www.appchina.com/) - `spiders/appchina.py`
* [联想应用商店](https://www.lenovomm.com/) - `spiders/leshangdian.py`
## 爬取内容
> 数据库定义在 database_def 文件夹下
### App信息
```python
class AppInfo(scrapy.Item):
    # 应用名称
    name = scrapy.Field()
    # 商店名称
    store = scrapy.Field()
    # 评分/1分满分
    score = scrapy.Field()
    # 应用简介
    description = scrapy.Field()
    # 更新时间
    update_time = scrapy.Field()
    # 分类
    category = scrapy.Field()
    # 开发者
    developer = scrapy.Field()
    # 下载次数
    download_times = scrapy.Field()
    # 评论次数
    review_times = scrapy.Field()
    # 应用ID
    app_id = scrapy.Field()
    # 安装包MD5校验码
    md5 = scrapy.Field()
```
### App评论
```python
class AppComment(scrapy.Item):
    # 评论内容
    content = scrapy.Field()
    # 评论时间
    time = scrapy.Field()
    # 用户名
    user = scrapy.Field()
    # 评分
    score = scrapy.Field()
    # 应用ID
    app_id = scrapy.Field()
    # 来源商店
    store = scrapy.Field()
    # 评论ID
    review_id = scrapy.Field()
```
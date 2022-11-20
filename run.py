from scrapy import cmdline

import sys

sys.path.append("")

CRAWL_NAME = ""

if __name__ == '__main__':
    while CRAWL_NAME not in ('360', 'appchina', 'leshangdian'):
        CRAWL_NAME = input("Input name you want to crawl['360','appchina','leshangdian']>> ")
    cmdline.execute(f"scrapy crawl {CRAWL_NAME}".split())

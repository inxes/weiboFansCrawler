# -*- coding: utf-8 -*-
import scrapy
import re

class ExampleSpider(scrapy.Spider):
    name = 'laoziliao'
    allowed_domains = ['laoziliao.net']


    def start_requests(self):
        start_urls = []
        y = 1946
        while y < 2000:
            m = 1
            while m < 13:
                d = 1
                while d < 32:
                    url = 'http://www.laoziliao.net/rmrb/' + str(y) + '-' + str(m) + '-' + str(d)
                    print('爬取地址：' + url)
                    start_urls.append(url)
                    d = d + 1
                m = m + 1
            y = y + 1

        for url in start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        next_pages = response.css('.box a::attr(href)').extract()

        for next_page in next_pages:
            if next_page is not None:
                next_page = response.urljoin(next_page)
                yield scrapy.Request(next_page, callback=self.parse)
        page = response.url.split("/")[-1]
        filename = '/Users/cindy/Documents/cindy/crawler/laoziliao/ziliao-%s.txt' % page
        article = '\n'.join(response.css('.article').extract())
        if article:
            dealartical = re.sub('<[^<]+?>', '', article).strip()
            with open(filename, 'wb') as f:
                f.write(dealartical.encode())

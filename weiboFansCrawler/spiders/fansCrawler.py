# -*- coding: utf-8 -*-
from scrapy_splash import SplashRequest
import scrapy
import re
import json

class FanscrawlerSpider(scrapy.Spider):
    name = 'fansCrawler'
    allowed_domains = ['weibo.com']

    def start_requests(self):
        # 浏览器用户代理
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'
        }
        # 指定cookies
        cookies = {
            'ALF': '1608343202',
            'Apache': '6695636289983.198.1576641109715',
            'SCF': 'AhYAERVc4btt_ZIfxmIJj-vc2EV8AB2r4pBrS3eneyFe-WbISf5WV6llujr_yCUTctU2BLRukkHYHe4wQ1SYgpE.',
            'SINAGLOBAL': '2164635642128.6316.1553319913398',
            'SUB': '_2A25w-FtzDeRhGeRG6lcU9C3IzziIHXVTjMu7rDV8PUNbmtANLRPTkW9NUig-Z1JsuhcqfxFu6OnT34sV4udwB0Ag',
            'SUBP': '0033WrSXqPxfM725Ws9jqgMF55529P9D9WhrAymGvNJKyKwEjTGQLc8b5JpX5KMhUgL.FozReK-fSheXShB2dJLoI0qLxK-L1-zLB.BLxKqL1-eL12BLxKMLB-eLB-eLxKBLBonL1h5LxKnL1hzLBK-LxKqL1-qLBoBt',
            'SUHB':'0S7DcQkjZzeJ-Z',
            'TC-Page-G0': '51e9db4bd1cd84f5fb5f9b32772c2750|1576727748|1576727741',
            'TC-V5-G0': 'eb26629f4af10d42f0485dca5a8e5e20',
            'ULV': '1576641109740:24:2:1:6695636289983.198.1576641109715:1575386199515',
            'UOR': ',,login.sina.com.cn',
            'Ugrow-G0': '9ec894e3c5cc0435786b4ee8ec8a55cc',
            'YF-V5-G0': '2583080cfb7221db1341f7a137b6762e',
            '_s_tentry': '-',
            'appkey': '',
            'cross_origin_proto': 'SSL',
            'login_sid_t': 'd895db1c11bc26b719d10da9988b99e7',
            'wvr': '6',
            'YF-Page-G0': '8438e5756d0e577d90f6ef4db5cfc490|1576663483|1576663316',
            # '': '',
            # '': '',
            'SSOLoginState': '1576641078',
            'sso_info': 'v02m6alo5qztKWRk5SlkKSQpZCjhKWRk6SljpOUpZCkmKWRk5ilkKOIpZCjjKadlqWkj5OIuIyTlLWNg4y0jYOQwA==',
            'un': '690852990@qq.com'
        }

        urls = [
            'https://weibo.com/p/1005055448635862/follow?relate=fans&page=1#Pl_Official_HisRelation__59'
        ]

        splash_args = {
            'html': 1,
            'png': 1,
            'width': 600,
            'render_all': 1,
        }

        for url in urls:
            yield scrapy.Request(url=url, headers=headers, cookies=cookies, callback=self.parse)

    def parse(self, response):
        if not response.body:
            return
        body = re.findall('<script>FM.view\((.+)\)</script>', response.body.decode())[8]
        json_body = json.loads(body)['html']
        virtual_response = scrapy.http.TextResponse(url='', body=json_body.encode())
        # if virtual_response is None:
            # TODO 重试
        next_pages = virtual_response.css('.page.next.S_txt1.S_line1::attr(href)').extract_first()
        fansids = virtual_response.css("img::attr(usercard)").extract()
        page = response.url.split("/")[-2]
        filetxt = '/Users/cindy/Documents/allstar/weibo-crawler/quotes-%s.txt' % page
        filename = 'quotes-%s.html' % page
        # fansids = response.css(".S_txt1 a::attr(href)").extract()
        print('爬取的好友id列表：', fansids)
        configpath = '/Users/cindy/Documents/allstar/weibo-crawler/config.json'

        print('下一页：' , next_pages)
        if next_pages is not None:
            next_page = response.urljoin(next_pages)
            yield scrapy.Request(next_page, callback=self.parse)
        for fansid in fansids:
            print('爬取的好友id：', fansid.split("&")[0][3:])
            with open(filetxt, 'a+') as ft:
                ft.write(fansid.split("&")[0][3:]+' ')
            self.log('Saved file %s' % filetxt)


# -*- coding: utf-8 -*-
import scrapy
import re
import json
import time

class FanscrawlerSpider(scrapy.Spider):
    name = 'fansCrawler'
    allowed_domains = ['weibo.com']

    handle_httpstatus_list = [414]

    cus_retry_times = 10

    count = 0

    custom_settings = {
        "RANDOM_DELAY": 3,
    }

    def start_requests(self):
        # 浏览器用户代理
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'
        }
        # 指定cookies
        cookies = {
            'ALF': '1608372361',
            'Apache': '6695636289983.198.1576641109715',
            'SCF': 'AhYAERVc4btt_ZIfxmIJj-vc2EV8AB2r4pBrS3eneyFeL9Qjmy__hmYX91V7LiU2sQVKtSlS-fDGCvFqY7-ISE0.',
            'SINAGLOBAL': '2164635642128.6316.1553319913398',
            'SUB': '_2A25w-O1ADeRhGeRG6lcU9C3IzziIHXVTjFmIrDV8PUNbmtAKLU7fkW9NUig-ZwxMtOTvcuWMNPhm4TuXhJlZsmOg',
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
            'SSOLoginState': '1576807202',
            'sso_info': 'v02m6alo5qztKWRk5SlkKSQpZCjhKWRk6SljpOUpZCkmKWRk5ilkKOIpZCjjKadlqWkj5OIuIyTlLWNg4y0jYOQwA==',
            'un': '690852990@qq.com',
            's_tentry':'login.sina.com.cn',
            'wb_view_log_2815543444':'1440*9002',
            'WBStorage':'42212210b087ca50|undefined',
            'webim_unReadCount':'%7B%22time%22%3A1576836434093%2C%22dm_pub_total%22%3A0%2C%22chat_group_client%22%3A0%2C%22allcountNum%22%3A0%2C%22msgbox%22%3A0%7D'
        }

        urls = [
            'https://weibo.com/p/1005055448635862/follow?relate=fans&from=100505&wvr=6&mod=headfans&current=fans#place'
        ]

        for url in urls:
            yield scrapy.Request(url=url, headers=headers, cookies=cookies, callback=self.parse)

    def parse(self, response):
        if not response.body:
            return
        script = re.findall('<script>FM.view\((.+)\)</script>', response.body.decode())
        print("长度", len(script))
        if len(script) == 0:
            print("重试")
            retries = response.meta.get('cus_retry_times', 0) + 1
            print("重试次数：", retries)
            # 打印问题html
            filename = 'quotes-error.html'
            if retries <= self.cus_retry_times:
                r = response.request.copy()
                r.meta['cus_retry_times'] = retries
                r.dont_filter = True
                yield r
            else:
                with open(filename, 'wb') as ft:
                    ft.write(response.body)
                self.log('Saved file %s' % filename)
                self.logger.debug("Gave up retrying {}, failed {} times".format(
                    response.url, retries
                ))

        # body = script[8]
        for body in script:
            if json.loads(body).get('html') is None:
                continue
            json_body = json.loads(body)['html']
            if json_body is None:
                continue
            virtual_response = scrapy.http.TextResponse(url='', body=json_body.encode())

            next_pages = virtual_response.css('.page.next.S_txt1.S_line1::attr(href)').extract_first()
            # 写入文件
            fansids = virtual_response.css("img::attr(usercard)").extract()
            page = response.url.split("/")[-2]
            filetxt = '/Users/cindy/Documents/allstar/weibo-crawler/quotes-%s.txt' % page
            # fansids = response.css(".S_txt1 a::attr(href)").extract()
            print('爬取的好友id列表：', fansids)
            configpath = '/Users/cindy/Documents/allstar/weibo-crawler/config.json'

            if next_pages is not None:
                next_page = response.urljoin(next_pages)
                print('捕获到下一页：', next_page)
                yield scrapy.Request(next_page, callback=self.parse)
            for fansid in fansids:
                print('爬取的好友id：', fansid.split("&")[0][3:])
                with open(filetxt, 'a+') as ft:
                    ft.write(fansid.split("&")[0][3:]+' ')
                self.count = self.count + 1
                self.log('Saved file %s' % filetxt)
            time.sleep(1)
        print('粉丝总数：', self.count)
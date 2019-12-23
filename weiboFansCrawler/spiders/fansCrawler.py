# -*- coding: utf-8 -*-
# from scrapy_splash import SplashRequest
import os

import scrapy
import re
import json
import time


class FanscrawlerSpider(scrapy.Spider):
    name = 'fansCrawler'
    # 爬网的域的字符串的可选列表
    allowed_domains = ['weibo.com']

    handle_httpstatus_list = [414]

    cus_retry_times = 10

    count = 0

    time = time.time()

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
            'ALF': '1577672083',
            'Apache': '6268048979834.457.1577067237128',
            'SCF': 'ApujhM8uDdqNvzdLTqI849Z5w7PGPP8Cse1Ti5EtzTJiM3Qk4qSRPWtU1_UKbbPeH-4IZ75KEydqbO3FIeQRI0E.',
            'SINAGLOBAL': '6268048979834.457.1577067237128',
            'SSOLoginState': '1577067234',
            'SUB': '_2A25zBFNFDeRhGeNN6VAT8CfJzT6IHXVQcMONrDV8PUNbmtAKLUbYkW9NSd-4-wxdg9wEXMJMk8r9xJdpNyZ5JlpJ',
            'SUBP': '0033WrSXqPxfM725Ws9jqgMF55529P9D9WhEE0KKnuqJiTM-1Qw8R3q_5JpX5K2hUgL.Fo-0eozEeh.fSoz2dJLoIEXLxKBLBonL12zLxK-LBo2LBo2LxK-LB.BL1KeLxK-L1KzL12eLxK-LBo5L1-2t',
            'SUHB': '0xnClA7lVuxlH4',
            'ULV': '1577067237134:1:1:1:6268048979834.457.1577067237128:',
            'UOR': ',,www.baidu.com',
            'Ugrow-G0': '7e0e6b57abe2c2f76f677abd9a9ed65d',
            'YF-Page-G0': '753ea17f0c76317e0e3d9670fa168584|1576995465|1576995464',
            'YF-V5-G0': 'b588ba2d01e18f0a91ee89335e0afaeb',
            '_s_tentry': '-',
            'cross_origin_proto': 'SSL',
            'login_sid_t': 'e85dd926c0edc739aa417b91fef1877f',
            'un': '17621142248',
            'wb_view_log': '1680*10502',
            'wb_view_log_5322209562': '1680*10502',
            'webim_unReadCount': '%7B%22time%22%3A1577067588477%2C%22dm_pub_total%22%3A0%2C%22chat_group_client%22%3A0%2C%22allcountNum%22%3A3%2C%22msgbox%22%3A0%7D',
            # 'TC-Page-G0': '753ea17f0c76317e0e3d9670fa168584|1576995465|1576995464',
            # 'TC-V5-G0': 'eb26629f4af10d42f0485dca5a8e5e20',
            #
            #
            #
            #
            #
            # 'appkey': '',
            #
            #
            # 'wvr': '6',

            # '': '',
            # '': '',

            # 'sso_info': 'v02m6alo5qztKWRk5SlkKSQpZCjhKWRk6SljpOUpZCkmKWRk5ilkKOIpZCjjKadlqWkj5OIuIyTlLWNg4y0jYOQwA==',
            #
            # 's_tentry': 'login.sina.com.cn',
            #
            # 'WBStorage': '42212210b087ca50|undefined',
            # 'webim_unReadCount': '%7B%22time%22%3A1576836434093%2C%22dm_pub_total%22%3A0%2C%22chat_group_client%22%3A0%2C%22allcountNum%22%3A0%2C%22msgbox%22%3A0%7D'
        }

        urls = [
            # 'https://weibo.com/5448635862/fans?from=100505&wvr=6&mod=headfans&current=fans#place', # weibo.com/user_id
            'https://weibo.com/2815543444/fans?from=100505&wvr=6&mod=headfans&current=fans#place'
        ]

        for url in urls:
            yield scrapy.Request(url=url, headers=headers, cookies=cookies, callback=self.parse)

    def parse(self, response):
        if not response.body:
            return
        scripts = re.findall('<script>FM.view\((.+)\)</script>', response.body.decode())

        print("script正则匹配的标签个数长度", len(scripts))

        print("response.URL的值:", response.url)

        if len(scripts) == 0:
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
                # 先截断文件 然后以二进制形式写入文件 默认是t
                with open(filename, 'wb') as ft:
                    ft.write(response.body)
                self.log('Saved file %s' % filename)
                self.logger.debug("Gave up retrying {}, failed {} times".format(
                    response.url, retries
                ))

        page = response.url.split("/")[-2]
        # isotimeformat = '%Y%m%d%X'
        #
        # date = time.strftime(isotimeformat, time.localtime(time.time()))
        filetxt = 'quotes-%s-%s.txt' % (page, self.time)
        # body = script[8]
        for script in scripts:
            if json.loads(script).get('html') is None:
                continue
            json_body = json.loads(script)['html']
            if json_body is None:
                continue
            virtual_response = scrapy.http.TextResponse(url='', body=json_body.encode())
            # 获取下一页的链接
            next_pages = virtual_response.css('.page.next.S_txt1.S_line1::attr(href)').extract_first()
            # 写入文件
            fansids = virtual_response.css("img::attr(usercard)").extract()
            # fansids = response.css(".S_txt1 a::attr(href)").extract()
            print('爬取的好友id列表：', fansids)

            if next_pages is not None:
                recursivePageInfo(response, next_pages, self)
            # 粉丝信息写入文件
            for fansid in fansids:
                dealFansId(fansid, filetxt, self)
            # 把文件名写入config.json 的user_id_list
            configpath = 'config.json'

            # 如果文件存在
            if os.path.exists(configpath):
                existDunpFile(configpath, fansids, filetxt)
            else:
                notExistDumpFile(configpath, fansids, filetxt)
        time.sleep(1)
        print('粉丝总数：', self.count)


def dealFansId(fansid, filetxt, self):
    print('爬取的好友id：', fansid.split("&")[0][3:])
    with open(filetxt, 'a+') as ft:
        ft.write(fansid.split("&")[0][3:] + ' ')
    self.count = self.count + 1
    self.log('Saved file %s' % filetxt)


def recursivePageInfo(response, next_pages, self):
    # urlJoin 处理相对路径
    next_page = response.urljoin(next_pages)
    print('捕获到下一页：', next_page)
    yield scrapy.Request(next_page, callback=self.parse)


# 写入已经存在的文件
def existDunpFile(configpath, fansids, filetxt):
    # 读取文件 读取时候文件指针放在文件头部
    with open(configpath, 'r+') as load_f:
        load_dict = json.load(load_f)
        print("读取到的json内容:", load_dict)
        # 判断好友id是否存在
        if fansids is not None and len(fansids) >= 0:
            user_id_list = load_dict['user_id_list']
            print("user_id_list的集合内容:", user_id_list)
            # 写入的是之前的文件名
            if filetxt not in user_id_list:
                user_id_list.append(filetxt)
                print("user_id_list的集合内容:", user_id_list)
                print("拼接的config内容:", load_dict)
                print("当前文件指针位置", load_f.tell())
                load_f.seek(0, 0)
                print("重置后文件指针位置", load_f.tell())
                json.dump(load_dict, load_f)


# 写入不存在的文件
def notExistDumpFile(configpath, fansids, filetxt):
    # 文件不存在直接写一个config
    with open(configpath, 'w') as cf:
        # 创建赋值
        if fansids is not None and len(fansids) >= 0:
            dict = {'user_id_list': [],
                    'filter': 1,
                    'since_date': time.strftime('%Y-%m-%d', time.localtime(time.time())),
                    'write_mode': ["csv"], 'mysql_config': {
                    'host': 'localhost', 'port': 3306, 'user': 'root', 'password': '123456',
                    'charset': 'utf8mb4'
                }}

            print("新创建的config对象", json.dumps(dict))
            print("文件名字", filetxt)
            user_id_list = dict['user_id_list']
            user_id_list.append(filetxt)
            json.dump(dict, cf)
            print("user_id_list的集合内容:", dict)

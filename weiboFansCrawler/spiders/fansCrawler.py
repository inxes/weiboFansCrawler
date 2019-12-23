# -*- coding: utf-8 -*-
# from scrapy_splash import SplashRequest
import os

import scrapy
import re
import json
import time
import urllib
import base64
import requests
import binascii
import rsa


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

    cookies_tosave = 'weibo.cookies'

    USER_AGENT = [
        'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/9.0.601.0 Safari/534.14',
        'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.874.120 Safari/535.2',
        'Mozilla/5.0 (Windows; U; Windows NT 6.0 x64; en-US; rv:1.9pre) Gecko/2008072421 Minefield/3.0.2pre',
        'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.0.11) Gecko/2009060215 Firefox/3.0.11 (.NET CLR 3.5.30729)',
        'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 GTB5',
        'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/527 (KHTML, like Gecko, Safari/419.3) Arora/0.6 (Change: )',
        'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/533.1 (KHTML, like Gecko) Maxthon/3.0.8.2 Safari/533.1 '
    ]

    user_agent = (
        'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.11 (KHTML, like Gecko) '
        'Chrome/20.0.1132.57 Safari/536.11'
    )

    weibo_user = '690852990@qq.com'
    weibo_password = 'a8887880A'
    session = requests.session()
    session.headers['User-Agent'] = user_agent

    def start_requests(self):
        self.login()
        urls = [
            # 'https://weibo.com/5448635862/fans?from=100505&wvr=6&mod=headfans&current=fans#place', # weibo.com/user_id
            'https://weibo.com/2815543444/fans?from=100505&wvr=6&mod=headfans&current=fans#place'
        ]

        # 浏览器用户代理
        headers = {
            'User-Agent': self.USER_AGENT
        }
        print("Cookies：", self.session.cookies.__dict__['_cookies'])
        for url in urls:
            yield scrapy.http.Request(url=url, callback=self.parse)

    def start_requests_login(self):
        # 自动登录
        username = self.weibo_user
        url = 'http://login.sina.com.cn/sso/prelogin.php?entry=miniblog&callback=sinaSSOController.preloginCallBack&user=%s&client=ssologin.js(v1.3.14)&_=%s' % (username, str(time.time()).replace('.', ''))
        return [scrapy.Request(url=url, method='get', callback=self.parse_item)]

    def post_message(self, response):
        serverdata = re.findall('{"retcode":0,"servertime":(.*?),"nonce":"(.*?)"}', response.body, re.I)[0]

        print(serverdata)
        servertime = serverdata[0]


        print(servertime)
        nonce = serverdata[1]
        print(nonce)
        formdata = {"entry": 'miniblog',
                    "gateway": '1',
                    "from": "",
                    "savestate": '7',
                    "useticket": '1',
                    "ssosimplelogin": '1',
                    "username": self.weibo_user,
                    "service": 'miniblog',
                    "servertime": servertime,
                    "nonce": nonce,
                    "pwencode": 'wsse',
                    "password": self.weibo_password,
                    "encoding": 'utf-8',
                    "url": 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
                    "returntype": 'META'}

        return [scrapy.FormRequest(url='http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.3.14)', formdata=formdata, callback=self.check_page)]

    def check_page(self, response):
        url = 'http://weibo.com/'
        request = response.request.replace(url=url, method='get', callback=self.parse_item)

        return request

    def parse_item(self, response):
        print(response.body)
        with open('%s%s%s' % (os.getcwd(), os.sep, 'logged.html'), 'wb') as f:
            f.write(response.body)

    def get_prelt(self, pre_login):
        prelt = int(time.time() * 1000) - pre_login['preloginTimeStart'] - pre_login['exectime']
        return prelt

    def prelogin(self):
        preloginTimeStart = int(time.time() * 1000)
        url = ('https://login.sina.com.cn/sso/prelogin.php?'
               'entry=weibo&callback=sinaSSOController.preloginCallBack&'
               'su=&rsakt=mod&client=ssologin.js(v1.4.19)&'
               '_=%s') % preloginTimeStart
        resp = self.session.get(url)
        pre_login_str = re.match(r'[^{]+({.+?})', resp.text).group(1)
        pre_login = json.loads(pre_login_str)
        pre_login['preloginTimeStart'] = preloginTimeStart
        print('pre_login 1:', pre_login)
        return pre_login

    def encrypt_user(self, username):
        user = urllib.parse.quote(username)
        su = base64.b64encode(user.encode())
        return su

    def encrypt_passwd(self, passwd, pubkey, servertime, nonce):
        key = rsa.PublicKey(int(pubkey, 16), int('10001', 16))
        message = str(servertime) + '\t' + str(nonce) + '\n' + str(passwd)
        passwd = rsa.encrypt(message.encode('utf-8'), key)
        return binascii.b2a_hex(passwd)

    def login(self):
        # step-1\. prelogin
        pre_login = self.prelogin()
        su = self.encrypt_user(self.weibo_user)
        sp = self.encrypt_passwd(
            self.weibo_password,
            pre_login['pubkey'],
            pre_login['servertime'],
            pre_login['nonce']
        )
        print("登录预加载数据：", pre_login)
        prelt = self.get_prelt(pre_login)
        data = {
            'entry': 'weibo',
            'gateway': 1,
            'from': '',
            'savestate': 7,
            'qrcode_flag': 'false',
            'userticket': 1,
            'pagerefer': '',
            'vsnf': 1,
            'su': su,
            'service': 'miniblog',
            'servertime': pre_login['servertime'],
            'nonce': pre_login['nonce'],
            'pwencode': 'rsa2',
            'sp': sp,
            'rsakv' : pre_login['rsakv'],
            'encoding': 'UTF-8',
            'prelt': prelt,
            'sr': "1280*800",
            'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.'
                   'sinaSSOController.feedBackUrlCallBack',
            'returntype': 'META'
        }
        # step-2 login POST
        login_url = 'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.19)'
        resp = self.session.post(login_url, data=data)
        print(resp.headers)
        print(resp.content)
        print('Step-2 response:', resp.text)
        # step-3 follow redirect
        redirect_url = re.findall(r'location\.replace\("(.*?)"', resp.text)[0]
        print('Step-3 to redirect:', redirect_url)
        resp = self.session.get(redirect_url)
        print('Step-3 response:', resp.text)
        # step-4 process step-3's response
        arrURL = re.findall(r'"arrURL":(.*?)\}', resp.text)[0]
        arrURL = json.loads(arrURL)
        print('CrossDomainUrl:', arrURL)
        for url in arrURL:
            print('set CrossDomainUrl:', url)
            resp_cross = self.session.get(url)
            print(resp_cross.text)
        redirect_url = re.findall(r'location\.replace\(\'(.*?)\'', resp.text)[0]
        print('Step-4 redirect_url:', redirect_url)
        resp = self.session.get(redirect_url)
        print('输出模拟登录数据：', resp.text)
        # with open(self.cookies_tosave, 'wb') as f:
        #     json.dump(self.session.cookies.__dict__, f)
        return True

        # # 指定cookies
        # cookies = {
        #     'ALF': '1608603281',
        #     'Apache': '6268048979834.457.1577067237128',
        #     'SCF': 'AhYAERVc4btt_ZIfxmIJj-vc2EV8AB2r4pBrS3eneyFe9kuBz1gSyiauUgsJ82oybuBMPl4WcF69-8XjDMlbC0I.',
        #     'SINAGLOBAL': '2164635642128.6316.1553319913398',
        #     'SSOLoginState': '1576807202',
        #     'SUB': '_2A25zBFNDDeRhGeRG6lcU9C3IzziIHXVQcMOLrDV8PUNbmtANLW-nkW9NUig-Zz1K38ZwXfQT8OSJ1foInJal73j7',
        #     'SUBP': '0033WrSXqPxfM725Ws9jqgMF55529P9D9WhrAymGvNJKyKwEjTGQLc8b5JpX5KMhUgL.FozReK-fSheXShB2dJLoI0qLxK-L1-zLB.BLxKqL1-eL12BLxKMLB-eLB-eLxKBLBonL1h5LxKnL1hzLBK-LxKqL1-qLBoBt',
        #     'SUHB': '0xnClA7lVuxlH4',
        #     'ULV': '1577067237134:1:1:1:6268048979834.457.1577067237128:',
        #     'UOR': ',,www.baidu.com',
        #     'Ugrow-G0': '7e0e6b57abe2c2f76f677abd9a9ed65d',
        #     'YF-Page-G0': '753ea17f0c76317e0e3d9670fa168584|1576995465|1576995464',
        #     'YF-V5-G0': 'b588ba2d01e18f0a91ee89335e0afaeb',
        #     '_s_tentry': '-',
        #     'cross_origin_proto': 'SSL',
        #     'login_sid_t': 'e85dd926c0edc739aa417b91fef1877f',
        #     'un': '17621142248',
        #     'wb_view_log': '1680*10502',
        #     'wb_view_log_5322209562': '1680*10502',
        #     'webim_unReadCount': '%7B%22time%22%3A1577067588477%2C%22dm_pub_total%22%3A0%2C%22chat_group_client%22%3A0%2C%22allcountNum%22%3A3%2C%22msgbox%22%3A0%7D',
        #     # 'TC-Page-G0': '753ea17f0c76317e0e3d9670fa168584|1576995465|1576995464',
        #     # 'TC-V5-G0': 'eb26629f4af10d42f0485dca5a8e5e20',
        #     #
        #     #
        #     #
        #     #
        #     #
        #     # 'appkey': '',
        #     #
        #     #
        #     # 'wvr': '6',
        #
        #     # '': '',
        #     # '': '',
        #
        #     # 'sso_info': 'v02m6alo5qztKWRk5SlkKSQpZCjhKWRk6SljpOUpZCkmKWRk5ilkKOIpZCjjKadlqWkj5OIuIyTlLWNg4y0jYOQwA==',
        #     #
        #     # 's_tentry': 'login.sina.com.cn',
        #     #
        #     # 'WBStorage': '42212210b087ca50|undefined',
        #     # 'webim_unReadCount': '%7B%22time%22%3A1576836434093%2C%22dm_pub_total%22%3A0%2C%22chat_group_client%22%3A0%2C%22allcountNum%22%3A0%2C%22msgbox%22%3A0%7D'
        # }

    def parse(self, response):
        if not response.body:
            return
        filename = 'quotes-error.html'
        with open(filename, 'wb') as ft:
            ft.write(response.body)
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
                # urlJoin 处理相对路径
                next_page = response.urljoin(next_pages)
                print('捕获到下一页：', next_page)
                yield scrapy.Request(next_page, callback=self.parse)
            # 粉丝信息写入文件
            for fansid in fansids:
                self.dealFansId(fansid, filetxt)
            # 把文件名写入config.json 的user_id_list
            configpath = './config.json'

            # 把文件名写入config.json 的user_id_list
            configpath = 'config.json'

            # 如果文件存在
            if os.path.exists(configpath):
                # 读取文件 读取时候文件指针放在文件头部
                with open(configpath, 'r+') as load_f:
                    load_dict = json.load(load_f)
                    print("读取到的json内容:", load_dict)
                    # 判断好友id是否存在
                    if fansids is not None and len(fansids) >= 0:
                        user_id_list = load_dict['user_id_list']
                        print("user_id_list的集合内容:", user_id_list)
                        print("var1的类型===", isinstance(user_id_list, list))
                        # 写入的是之前的文件名
                        if filetxt not in user_id_list:
                            user_id_list.append(filetxt)
                            print("user_id_list的集合内容:", user_id_list)
                            print("拼接的config内容:", load_dict)
                            json.dump(load_dict, load_f)
            else:
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
        time.sleep(1)
        print('粉丝总数：', self.count)
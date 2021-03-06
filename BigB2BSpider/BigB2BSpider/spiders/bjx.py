# -*- coding: utf-8 -*-
import re
import requests
import scrapy
from hashlib import md5
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from BigB2BSpider.data_tools.clean_worlds import CleanWords
# from BigB2BSpider.data_tools.orc_img import recognition_image
from BigB2BSpider.items import BeiJiXingShangWuWangItem
# from scrapy_redis.spiders import RedisCrawlSpider
from scrapy.cmdline import execute



class BeiJiXingShangWuWangSpider(CrawlSpider):
    name = "bjx"
    allowed_domains = ['b2b.bjx.com.cn',]
    start_urls = ['http://b2b.bjx.com.cn/company/']
    cw = CleanWords()
    # redis_key = "ksb:start_urls"

    custom_settings = {
        'DOWNLOAD_DELAY': 0.5,
        'ITEM_PIPELINES': {'BigB2BSpider.pipelines.MysqlTwistedPiplines_v1': 302},
        'DEFAULT_REQUEST_HEADERS': {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Cookie": "UM_distinctid=16d192f7272f6-07eabfff6ab5fb-5a13331d-1fa400-16d192f7274907; Hm_lvt_797e95e42c7a8bdc8814749cbcddd277=1568085603; Hm_lpvt_797e95e42c7a8bdc8814749cbcddd277=1568085603; CNZZDATA30036372=cnzz_eid%3D1111716948-1568081417-http%253A%252F%252Fwww.bjx.com.cn%252F%26ntime%3D1568081417",
            "Host": "b2b.bjx.com.cn",
            "Referer": "http://www.bjx.com.cn/",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.87 Safari/537.36",
        },
        'DOWNLOADER_MIDDLEWARES': {
            'BigB2BSpider.middlewares.Bigb2BspiderDownloaderMiddleware': 544,
            # 'BigB2BSpider.middlewares.RandomMyProxyMiddleware': 420,
        },
    }
    # /c3847/p2/
    rules = (
        Rule(LinkExtractor(
            allow=r".*",restrict_xpaths=("//div[@class='xhqy_list']//li//a[contains(text(),'联系我们')]")), callback='parse_items', follow=True),

        Rule(LinkExtractor(
            allow=r".*", restrict_xpaths=("//div[@class='page']//a[contains(text(),'下一页')]")), follow=True),
    )

    def parse_items(self, response):
        item = BeiJiXingShangWuWangItem()
        if "contact_list.html" in response.url:
            pattern = re.compile(r'<meta name="keywords" content=".*?,(.*?)"/>',re.S)
            item["company_Name"] = response.xpath("//span[contains(text(),'公司名称：')]/../strong/text()").extract_first()
            item["company_address"] = response.xpath("//span[contains(text(),'联系地址：')]/../text()").extract_first()
            item["linkman"] = response.xpath("//span[contains(text(),'联')]/../text()").extract()
            item["telephone"] = response.xpath("//span[contains(text(),'固定电话：')]/../text()").extract_first()
            item["phone"] = response.xpath("//span[contains(text(),'移动电话：')]/text()").extract_first()
            item["contact_Fax"] = response.xpath("//span[contains(text(),'传真号码：')]/../text()").extract_first()
            item["contact_QQ"] = response.xpath("//span[contains(text(),'Q')]/../text()").extract_first()
            item["E_Mail"] = response.xpath("//span[contains(text(),'企业邮箱：')]/../text()").extract_first()
            item["Source"] = response.url
            item["kind"] = ",".join(response.xpath("//td[contains(text(),'主营产品：')]/following-sibling::td/p/text()").getall())
            city_infos = response.xpath("//span[contains(text(),'所在地区：')]/../text()").get()


            if item["company_Name"] and item["company_Name"] != '':
                if "（" in item["company_Name"]:
                    item["company_Name"] = item["company_Name"].split('（')[0]
                elif "(" in item["company_Name"]:
                    item["company_Name"] = item["company_Name"].split('(')[0]
                elif "_" in item["company_Name"]:
                    item["company_Name"] = item["company_Name"].split('_')[0]
                elif "-" in item["company_Name"]:
                    item["company_Name"] = item["company_Name"].split('-')[0]
                else:
                    item["company_Name"] = re.sub(r'\n|\s|\r|\t|公司名称：', '', item["company_Name"]).replace(' ', '').strip()
            else:
                return
            item["company_id"] = self.get_md5(item["company_Name"])

            if item["kind"]:
                item["kind"] = item["kind"].replace(" ", '|')
                item["kind"] = re.sub(r'\n|\s|\r|\t|主营业务：|主营|主营项目：|暂无商品', '', item["kind"]).replace('-', '|')\
                    .replace('、', '|').replace(',', '|').replace('，', '|').replace(';','|').replace('.', '').strip()
            else:
                item["kind"] = ''

            item["kind"] = self.cw.rinse_keywords(self.cw.replace_ss(item["kind"]))

            if item["linkman"]:
                try:
                    item["linkman"] = item["linkman"][1].replace('未填写','')
                except:
                    item["linkman"] = ''
            else:
                item["linkman"] = ''
            item["linkman"] = self.cw.search_linkman(item["linkman"])

            if item["phone"]:
                item["phone"] = item["phone"]
            else:
                item["phone"] = ''
            item["phone"] = self.cw.search_phone_num(item["phone"])

            if item["telephone"]:
                item["telephone"] = self.cw.search_telephone_num(item["telephone"])
            else:
                item["telephone"] = ''

            if item["contact_Fax"]:
                item["contact_Fax"] = self.cw.search_contact_Fax(item["contact_Fax"])
            else:
                item["contact_Fax"] = ''

            if item["E_Mail"]:
                item["E_Mail"] = self.cw.search_email(item["E_Mail"])
            else:
                item["E_Mail"] = ''

            if item["contact_QQ"]:
                item["contact_QQ"] = self.cw.search_QQ(item["contact_QQ"])
            else:
                item["contact_QQ"] = ''

            if item["company_address"]:
                item["company_address"] = self.cw.search_address(item["company_address"])
            else:
                item["company_address"] = ''

            if city_infos:
                if '/' in city_infos:
                    try:
                        item["province"] = city_infos.split('/')[0]
                        item["city_name"] = city_infos.split('/')[1]
                    except:
                        item["province"] = ''
                        item["city_name"] = ''
                else:
                    item["province"] = ''
                    item["city_name"] = ''
            else:
                item["province"] = ''
                item["city_name"] = ''

            yield item
        elif "index.html" in response.url:
            pattern_c = re.compile(r'<title>(.*?)-北极星电力商务通</title>',re.S)
            pattern_k = re.compile(r'<meta name="keywords" content="(.*?),.*?,北极星电力商务通" />',re.S)
            pattern_add = re.compile(r'>地址：(.*?)<',re.S)
            item["company_Name"] = response.xpath("//h1/text()").extract_first()
            item["company_address"] = response.xpath("//span[contains(text(),'联系地址：')]/../text()").extract_first()
            item["linkman"] = response.xpath("//span[contains(text(),'联系人：')]/../text()").extract_first()
            item["telephone"] = response.xpath("//span[contains(text(),'电话：')]/../text()").extract_first()
            item["phone"] = response.xpath("//span[contains(text(),'手机：')]/text()").extract_first()
            item["contact_Fax"] = response.xpath("//span[contains(text(),'传真：')]/../text()").extract_first()
            item["contact_QQ"] = response.xpath("//span[contains(text(),'QQ号码：')]/../text()").extract_first()
            item["E_Mail"] = response.xpath("//span[contains(text(),'邮箱：')]/../text()").extract_first()
            item["Source"] = response.url
            item["kind"] = ",".join(re.findall(pattern_k,response.text)) if re.findall(pattern_k,response.text) else ''
            city_infos = response.xpath("//span[contains(text(),'地区：')]/../text()").get()

            if item["company_Name"] and item["company_Name"] != '':
                if "（" in item["company_Name"]:
                    item["company_Name"] = item["company_Name"].split('（')[0]
                elif "(" in item["company_Name"]:
                    item["company_Name"] = item["company_Name"].split('(')[0]
                elif "_" in item["company_Name"]:
                    item["company_Name"] = item["company_Name"].split('_')[0]
                elif "-" in item["company_Name"]:
                    item["company_Name"] = item["company_Name"].split('-')[0]
                elif " " in item["company_Name"]:
                    item["company_Name"] = item["company_Name"].replace(" ","")
            else:
                return
            item["company_Name"] = re.sub(r'\n|\s|\r|\t|\\n|\\r|公司名称：', '', item["company_Name"]) \
                .replace('\r\n', '').strip()
            item["company_id"] = self.get_md5(item["company_Name"])

            if item["kind"]:
                item["kind"] = item["kind"].replace(" ", '|')
                item["kind"] = re.sub(r'\n|\s|\r|\t|主营业务：|主营|主营项目：|暂无商品', '', item["kind"]).replace('-', '|') \
                    .replace('、', '|').replace(',', '|').replace('，', '|').replace(';', '|').replace('.', '').strip()
            else:
                item["kind"] = ''

            item["kind"] = self.cw.rinse_keywords(self.cw.replace_ss(item["kind"]))

            if item["linkman"]:
                try:
                    item["linkman"] = item["linkman"].replace('未填写', '')
                except:
                    item["linkman"] = ''
            else:
                item["linkman"] = ''
            item["linkman"] = self.cw.search_linkman(item["linkman"])

            if item["phone"]:
                item["phone"] = item["phone"]
            else:
                item["phone"] = ''
            item["phone"] = self.cw.search_phone_num(item["phone"])

            if item["telephone"]:
                item["telephone"] = self.cw.search_telephone_num(item["telephone"])
            else:
                item["telephone"] = ''

            if item["contact_Fax"]:
                item["contact_Fax"] = self.cw.search_contact_Fax(item["contact_Fax"])
            else:
                item["contact_Fax"] = ''

            if item["E_Mail"]:
                item["E_Mail"] = self.cw.search_email(item["E_Mail"])
            else:
                item["E_Mail"] = ''

            if item["contact_QQ"]:
                item["contact_QQ"] = self.cw.search_QQ(item["contact_QQ"])
            else:
                item["contact_QQ"] = ''

            if item["company_address"]:
                item["company_address"] = self.cw.search_address(item["company_address"])
            else:
                try:
                    item["company_address"] = "".join(re.findall(pattern_add,response.text)) if re.findall(pattern_add,response.text) else ''
                except:
                    item["company_address"] = ''
            item["company_address"] = self.cw.search_address(item["company_address"])

            if city_infos:
                if '/' in city_infos:
                    try:
                        item["province"] = city_infos.split('/')[0]
                        item["city_name"] = city_infos.split('/')[1]
                    except:
                        item["province"] = ''
                        item["city_name"] = ''
                else:
                    item["province"] = ''
                    item["city_name"] = ''
            else:
                item["province"] = ''
                item["city_name"] = ''

            yield item


    def get_md5(self, value):
        if value:
            return md5(value.encode()).hexdigest()
        return ''

    # def requests_href(self, url, headers):
    #     res = requests.get(url=url, headers=headers, timeout=10, verify=False)
    #     res.encoding = "utf-8"
    #     if res.status_code == requests.codes.ok:
    #         img = res.content
    #         something_img_file_path = r"F:\PythonProjects\venv\pythonProjects\BigB2BSpider\BigB2BSpider\img_src\something_img3\image.png"
    #         with open(something_img_file_path, "wb") as fp:
    #             fp.write(img)
    #         fp.close()
    #         if img:
    #             try:
    #                 something = recognition_image(something_img_file_path)
    #                 if something:
    #                     return something
    #                 else:
    #                     return ''
    #             except:
    #                 return ''
    #         else:
    #             return ''
    #     else:
    #         return ''




if __name__ == '__main__':
    execute(["scrapy", "crawl", "bjx"])
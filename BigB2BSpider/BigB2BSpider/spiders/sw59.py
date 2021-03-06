# -*- coding: utf-8 -*-
import re
import requests
import scrapy
from hashlib import md5
from scrapy.spiders import CrawlSpider, Rule
from BigB2BSpider.data_tools.clean_worlds import CleanWords
from BigB2BSpider.data_tools.orc_img import recognition_image
from BigB2BSpider.items import WuJiuShangWuWangspiderItem
from scrapy.cmdline import execute



class WuJiuShangWuWangSpider(CrawlSpider):
    name = 'sw59'
    allowed_domains = ['www.59b2b.com']
    start_urls = ['http://www.59b2b.com/company/']
    cw = CleanWords()

    custom_settings = {
        'DOWNLOAD_DELAY': 0.3,
        'DEFAULT_REQUEST_HEADERS': {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            # "Cookie": "Hm_lvt_a8ba6329e67dda68e5d5dadf2df13e01=1564989677; Hm_lpvt_a8ba6329e67dda68e5d5dadf2df13e01=1564989683; security_session_verify=804231afb453a0f6d1f322329f5bfb57",
            # "Host": "www.yiwangtui.com",
            # "Referer": "http://www.yiwangtui.com/",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.87 Safari/537.36",
        },
        'DOWNLOADER_MIDDLEWARES': {
            'BigB2BSpider.middlewares.Bigb2BspiderDownloaderMiddleware': 543,
            # 'BigB2BSpider.middlewares.RandomMyProxyMiddleware': 543,
        }
    }

    def parse(self, response):
        a_list = response.xpath("//div[@class='left_box']//tr//a")
        for a in a_list:
            kind_name = a.xpath("./text()").extract_first()
            kind_href = a.xpath("./@href").extract_first()
            if kind_href:
                print(kind_name,kind_href)
                yield scrapy.Request(
                    url=kind_href,
                    callback=self.parse_company_list,
                    dont_filter=True
                )

    def parse_company_list(self, response):
        tr_list = response.xpath("//div[@class='left_box']//div[@class='list']//table//tr")
        for tr in tr_list:
            item = WuJiuShangWuWangspiderItem()
            pattern = re.compile(r'\[(.*?)/(.*?)\]', re.S)
            item["company_Name"] = tr.xpath(".//li//a/strong/text()").extract_first()
            company_href = tr.xpath(".//li/a/@href").extract_first()
            item["kind"] = tr.xpath(".//li[contains(text(),'主营：')]/text()").extract_first()
            city_infos = tr.xpath(".//td[@class='f_orange']/text()").extract_first()
            if city_infos:
                # 广东/潮州市
                try:
                    item["province"] = re.findall(pattern, city_infos)[0][0]
                    item["city_name"] = re.findall(pattern, city_infos)[0][1]
                except:
                    item["province"] = ''
                    item["city_name"] = ''
            else:
                item["province"] = ''
                item["city_name"] = ''

            if item["company_Name"]:
                item["company_Name"] = re.sub(r'\n|\s|\r|\t|公司名称：', '', item["company_Name"]).replace(' ', '').strip()
                item["company_id"] = self.get_md5(item["company_Name"])

            if item["kind"]:
                item["kind"] = re.sub(r'\n|\s|\r|\t|主营业务：|主营', '', item["kind"]).replace('-', '|')\
                    .replace('、', '|').replace('，', '|').replace('，', '|').replace('.', '').strip()
            else:
                item["kind"] = ''

            item["kind"] = self.cw.rinse_keywords(self.cw.replace_ss(item["kind"]))

            item["linkman"] = ''
            item["phone"] = ''
            item["telephone"] = ''
            item["contact_Fax"] = ''
            item["contact_QQ"] = ''
            item["E_Mail"] = ''
            item["company_address"] = ''
            item["Source"] = response.url
            yield item

        next_page_url = response.xpath("//div[@class='pages']//a[contains(text(),'下一页»')]/@href").extract_first()
        if next_page_url:
            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse_company_list
            )

    def get_md5(self, value):
        if value:
            return md5(value.encode()).hexdigest()
        return ''

    # def parse_company_contact(self, response):
    #     if " 对不起，您查找的页面不存在，以下信息有没有您需要的？" in response.text:
    #         return
    #     item = response.meta["item"]
    #     item["company_Name"] = response.xpath("//td[contains(text(),'公司名称：')]/following-sibling::td/text()").extract_first()
    #     # item["company_id"] = md5(item["company_Name"].encode()).hexdigest()
    #     # item["kind"] = response.xpath("//div[@class='head']/h4/text()").extract_first()
    #     item["company_address"] = "".join(response.xpath("//td[contains(text(),'公司地址：')]/following-sibling::td/text()").extract())
    #     item["linkman"] = "".join(response.xpath("//td[contains(text(),'联 系 人：')]/following-sibling::td/text()").extract())
    #     item["telephone"] = "".join(response.xpath("//td[contains(text(),'公司电话：')]/following-sibling::td/text()").extract())
    #     item["phone"] = "".join(response.xpath("//td[contains(text(),'手机号码：')]/following-sibling::td/text()").extract())
    #     item["contact_Fax"] = "".join(response.xpath("//td[contains(text(),'公司传真：')]/following-sibling::td/text()").extract())
    #     item["contact_QQ"] = "".join(response.xpath("//img[@title='点击QQ交谈/留言']/../@href").extract())
    #     item["E_Mail"] = "".join(response.xpath("//td[contains(text(),'电子邮件：')]/following-sibling::td/text()").extract())
    #     item["Source"] = response.url
    #
    #     if item["company_Name"]:
    #         item["company_Name"] = re.sub(r'\n|\s|\r|\t|公司名称：', '', item["company_Name"]).replace(' ', '').strip()
    #     item["company_id"] = self.get_md5(item["company_Name"])
    #
    #     if item["kind"]:
    #         item["kind"] = re.sub(r'\n|\s|\r|\t|主营业务：|主营', '', item["kind"]).replace('-', '|').replace('、', '|') \
    #             .replace('，', '|').replace('，', '|').replace('.', '').strip()
    #     else:
    #         item["kind"] = ''
    #
    #     item["kind"] = self.cw.rinse_keywords(self.cw.replace_ss(item["kind"]))
    #
    #     if item["linkman"]:
    #         item["linkman"] = item["linkman"]
    #     else:
    #         item["linkman"] = ''
    #     item["linkman"] = self.cw.search_linkman(item["linkman"])
    #
    #     if item["phone"]:
    #         item["phone"] = item["phone"]
    #     else:
    #         item["phone"] = ''
    #     item["phone"] = self.cw.search_phone_num(item["phone"])
    #
    #     if item["telephone"]:
    #         item["telephone"] = item["telephone"]
    #     else:
    #         item["telephone"] = ''
    #     item["telephone"] = self.cw.search_telephone_num(item["telephone"])
    #
    #     if item["contact_Fax"]:
    #         item["contact_Fax"] = item["contact_Fax"]
    #     else:
    #         item["contact_Fax"] = ''
    #     item["contact_Fax"] = self.cw.search_contact_Fax(item["contact_Fax"])
    #
    #     if item["E_Mail"]:
    #         item["E_Mail"] = self.cw.search_email(item["E_Mail"])
    #     else:
    #         item["E_Mail"] = ''
    #
    #     if item["contact_QQ"]:
    #         item["contact_QQ"] = self.cw.search_QQ(item["contact_QQ"])
    #     else:
    #         item["contact_QQ"] = ''
    #
    #     if item["company_address"]:
    #         item["company_address"] = item["company_address"]
    #     else:
    #         item["company_address"] = ''
    #     item["company_address"] = self.cw.search_address(item["company_address"])
    #
    #     yield item



    # def requests_href(self, url, headers):
    #     res = requests.get(url=url, headers=headers, timeout=20, verify=False)
    #     res.encoding = "utf-8"
    #     if res.status_code == requests.codes.ok:
    #         img = res.content
    #         something_img_file_path = r"F:\PythonProjects\venv\pythonProjects\BigB2BSpider\BigB2BSpider\img_src\something_img\image.png"
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
    execute(["scrapy", "crawl", "sw59"])
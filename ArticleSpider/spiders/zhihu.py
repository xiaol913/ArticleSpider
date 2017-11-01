# -*- coding: utf-8 -*-
import re
import json
import time
import datetime

try:
    import urlparse as parse
except:
    from urllib import parse

import scrapy
from  scrapy.loader import ItemLoader
from ArticleSpider.items import ZhihuAnswerItem, ZhihuQuestionItem


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    # question的第一页answer的请求url
    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?include=data[" \
                       "*].content,id,excerpt,created_time,updated_time,question,voteup_count," \
                       "comment_count;data[*].author.topics&offset={2}&limit={1}"

    agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) " \
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"
    header = {
        "HOST": "www.zhihu.com",
        "Referer": "https://www.zhihu.com",
        "User-Agent": agent
    }

    def parse(self, response):
        """
        提取出页面中所有url 并跟中url进一步爬取
        如何提取url中的格式为/question/xxx就下载之后直接进入解析函数
        """
        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        for url in all_urls:
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", url)
            if match_obj:
                # 如果提取到question相关的页面则下载后交由提取函数进行提取
                request_url = match_obj.group(1)
                question_id = int(match_obj.group(2))

                yield scrapy.Request(request_url, meta={"question_id": question_id},
                                     headers=self.header, callback=self.parse_question)
            else:
                # pass
                # 如果不是question页面则直接进一步跟随
                yield scrapy.Request(url, headers=self.header)

    def parse_question(self, response):
        # 处理question页面，从页面中取出具体question item
        question_id = response.meta.get("question_id", {})
        item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
        item_loader.add_css("title", "h1.QuestionHeader-title::text")
        item_loader.add_css("content", ".QuestionHeader-detail")
        item_loader.add_value("url", response.url)
        item_loader.add_value("zhihu_id", question_id)
        item_loader.add_css("answer_num", ".List-headerText span::text")
        item_loader.add_css("comments_num", ".QuestionHeader-Comment button::text")
        item_loader.add_css("watch_user_num", ".NumberBoard-value::text")
        item_loader.add_css("topics", ".QuestionHeader-topics .Popover div::text")

        question_item = item_loader.load_item()
        # 如果是Request则下载 如果是 item则进入到pipeline
        yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0),
                             callback=self.parse_answer, headers=self.header)
        yield question_item

    def parse_answer(self, response):
        # 处理question的anser
        ans_json = json.loads(response.text)
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]

        # 提取answer的具体字段
        for answer in ans_json["data"]:
            annswer_item = ZhihuAnswerItem()
            annswer_item["zhihu_id"] = answer["id"]
            annswer_item["url"] = answer["url"]
            annswer_item["question_id"] = answer["question"]["id"]
            annswer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            annswer_item["content"] = answer["content"] if "content" in answer else None
            annswer_item["praise_num"] = answer["voteup_count"]
            annswer_item["comments_num"] = answer["comment_count"]
            annswer_item["create_time"] = answer["created_time"]
            annswer_item["update_time"] = answer["updated_time"]
            annswer_item["crawl_time"] = datetime.datetime.now()

            yield annswer_item

        if not is_end:
            yield scrapy.Request(self.start_answer_url.format(next_url, 20, 0),
                                 callback=self.parse_answer, headers=self.header)

    # 以下为登录函数
    def start_requests(self):
        return [scrapy.Request('https://www.zhihu.com/#signin', callback=self.login, headers=self.header)]

    def login(self, response):
        match_obj = re.match('.*name="_xsrf" value="(.*?)"', response.text, re.DOTALL)
        xsrf = ''
        if match_obj:
            xsrf = match_obj.group(1)
            post_data = {
                "_xsrf": xsrf,
                "phone_num": "18615705738",
                "password": "651134",
                "captcha": ""
            }

            t = str(int(time.time() * 1000))
            captcha_url = "https://www.zhihu.com/captcha.gif?r={0}&type=login".format(t)
            yield scrapy.Request(captcha_url, headers=self.header, meta={"post_data": post_data},
                                 callback=self.login_after_captcha)

    def login_after_captcha(self, response):
        with open("captcha.jpg", "wb") as f:
            f.write(response.body)
            f.close()
        from PIL import Image
        try:
            im = Image.open("captcha.jpg")
            im.show()
            im.close()
        except:
            pass

        captcha = input("输入验证码\n>")
        post_data = response.meta.get("post_data", {})
        post_data["captcha"] = captcha
        post_url = "https://www.zhihu.com/login/phone_num"
        return [scrapy.FormRequest(
            url=post_url,
            formdata=post_data,
            headers=self.header,
            callback=self.check_login,
        )]

    def check_login(self, response):
        # 验证服务器返回数据判断是否成功
        text_json = json.loads(response.text)
        if "msg" in text_json and text_json["msg"] == "登录成功":
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True, headers=self.header)

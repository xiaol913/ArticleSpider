# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html
import datetime

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join

from w3lib.html import remove_tags

from ArticleSpider.utils.common import get_md5, date_convert, match_nums, remove_comment_tags, return_value, \
    remove_splash, handle_jobaddr
from ArticleSpider.settings import SQL_DATE_FORMAT, SQL_DATETIME_FORMAT


class ArticlespiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class ArticleItemLoader(ItemLoader):
    # 自定义itemloader
    default_output_processor = TakeFirst()


class JobBoleArticleItem(scrapy.Item):
    title = scrapy.Field()
    create_date = scrapy.Field(
        input_processor=MapCompose(date_convert),
    )
    url = scrapy.Field()
    url_object_id = scrapy.Field(
        input_processor=MapCompose(get_md5),
    )
    front_image_url = scrapy.Field(
        output_processor=MapCompose(return_value),
    )
    front_image_path = scrapy.Field()
    praise_nums = scrapy.Field(
        input_processor=MapCompose(match_nums),
    )
    comment_nums = scrapy.Field(
        input_processor=MapCompose(match_nums),
    )
    fav_nums = scrapy.Field(
        input_processor=MapCompose(match_nums),
    )
    tags = scrapy.Field(
        input_processor=MapCompose(remove_comment_tags),
        output_processor=Join(","),
    )
    content = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
                    insert into jobbole_article(title, url, url_object_id, comment_nums, fav_nums, praise_nums) 
                    VALUES (%s, %s, %s, %s, %s, %s)        
                """
        params = (
            self["title"],
            self["url"],
            self["url_object_id"],
            self["comment_nums"],
            self["fav_nums"],
            self["praise_nums"],
        )
        return insert_sql, params


class ZhihuQuestionItem(scrapy.Item):
    # 知乎的问题item
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answer_num = scrapy.Field()
    comments_num = scrapy.Field()
    watch_user_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
                    insert into zhihu_question(zhihu_id, topics, url, title, content, 
                    answer_num, comments_num, watch_user_num, click_num, crawl_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)    
                    ON DUPLICATE KEY UPDATE title=VALUES(title), content=VALUES(content),
                     answer_num=VALUES(answer_num), comments_num=VALUES(comments_num),
                     watch_user_num=VALUES(watch_user_num), click_num=VALUES(click_num)
                """
        zhihu_id = self["zhihu_id"][0]
        topics = ",".join(self["topics"])
        url = self["url"][0]
        title = "".join(self["title"])
        content = "".join(self["content"])
        answer_num = match_nums("".join(self["answer_num"]))
        comments_num = match_nums("".join(self["comments_num"]))

        if len(self["watch_user_num"]) == 2:
            watch_user_num = int(self["watch_user_num"][0])
            click_num = int(self["watch_user_num"][1])
        else:
            watch_user_num = int(self["watch_user_num"][0])
            click_num = 0
        crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)
        params = (
            zhihu_id,
            topics,
            url,
            title,
            content,
            answer_num,
            comments_num,
            watch_user_num,
            click_num,
            crawl_time,
        )
        return insert_sql, params


class ZhihuAnswerItem(scrapy.Item):
    # 知乎的问题回话item
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    praise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
                    insert into zhihu_answer(zhihu_id, url, question_id, author_id, 
                    content, praise_num, comments_num, create_time, update_time, crawl_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE content=VALUES(content), comments_num=VALUES(comments_num),
                     praise_num=VALUES(praise_num), update_time=VALUES(update_time) 
                """
        create_time = datetime.datetime.fromtimestamp(self["create_time"]).strftime(SQL_DATE_FORMAT)
        update_time = datetime.datetime.fromtimestamp(self["update_time"]).strftime(SQL_DATE_FORMAT)
        params = (
            self["zhihu_id"],
            self["url"],
            self["question_id"],
            self["author_id"],
            self["content"],
            self["praise_num"],
            self["comments_num"],
            create_time,
            update_time,
            self["crawl_time"].strftime(SQL_DATETIME_FORMAT),
        )
        return insert_sql, params


class LagouJobItem(scrapy.Item):
    # 拉勾网职位信息
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    title = scrapy.Field()
    salary = scrapy.Field()
    job_city = scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    work_years = scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    degree_need = scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    job_type = scrapy.Field()
    publish_time = scrapy.Field()
    tags = scrapy.Field(
        input_processor=Join(",")
    )
    job_advantage = scrapy.Field()
    job_desc = scrapy.Field(
        input_processor=MapCompose(remove_tags),
    )
    job_addr = scrapy.Field(
        input_processor=MapCompose(remove_tags, handle_jobaddr),
    )
    company_url = scrapy.Field()
    company_name = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
                    insert into lagou_job(url, url_object_id, title, salary, 
                    job_city, work_years, degree_need, job_type, publish_time, tags,
                    job_advantage, job_desc, job_addr, company_url, company_name, crawl_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE salary=VALUES(salary), job_desc=VALUES(job_desc),
                     job_advantage=VALUES(job_advantage)
                """
        params = (
            self["url"],
            self["url_object_id"],
            self["title"],
            self["salary"],
            self["job_city"],
            self["work_years"],
            self["degree_need"],
            self["job_type"],
            self["publish_time"],
            self["tags"],
            self["job_advantage"],
            self["job_desc"],
            self["job_addr"],
            self["company_url"],
            self["company_name"],
            self["crawl_time"].strftime(SQL_DATETIME_FORMAT),
        )
        return insert_sql, params


class LagouJobItemLoader(ItemLoader):
    # 自定义itemloader
    default_output_processor = TakeFirst()

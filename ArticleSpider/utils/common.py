# -*- coding: utf-8 -*-
import hashlib
import re
import datetime

def get_md5(url):
    if isinstance(url, str):
        url = url.encode("utf-8")
    m = hashlib.md5()
    m.update(url)
    return m.hexdigest()


def match_nums(nums):
    match_re = re.match(".*(\d+).*", nums)
    if match_re:
        nums = match_re.group(1)
    else:
        nums = 0
    return nums


def date_convert(value):
    try:
        value = datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except Exception as e:
        value = datetime.datetime.now().date()
    return value


def remove_comment_tags(value):
    # 去掉tag中的评论
    if "评论" in value:
        return ""
    else:
        return value


def return_value(v):
    return v


def remove_splash(v):
    # 去掉工作城市的斜线
    return v.replace("/", "")


def handle_jobaddr(v):
    addr_list = v.split("\n")
    addr_list = [item.strip() for item in addr_list if item.strip() != "查看地图"]
    return "".join(addr_list)

# -*- coding: utf-8 -*-
import requests
from scrapy.selector import Selector
import MySQLdb

conn = MySQLdb.connect('127.0.0.1', 'root', 'root', 'article_spider', charset="utf8", use_unicode=True)
cursor = conn.cursor()


def crawl_ips():
    # 爬取西刺免费IP代理
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 ("
                      "KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36"}
    for i in range(2488):
        re = requests.get("http://www.xicidaili.com/nn/{0}".format(i), headers=headers)

    selector = Selector(text=re.text)
    all_trs = selector.css("#ip_list tr")

    ip_list = []
    for tr in all_trs[1:]:
        speed_str = tr.css(".bar::attr(title)").extract()[0]
        if speed_str:
            speed = float(speed_str.split("秒")[0])
        else:
            speed = 0
        all_texts = tr.css("td::text").extract()
        ip = all_texts[0]
        port = all_texts[1]
        proxy_type = all_texts[5]

        ip_list.append((ip, port, proxy_type, speed))

    for ip_info in ip_list:
        cursor.execute(
            "insert proxy_id(ip, port, proxy_type, speed) VALUES('{0}', '{1}', '{2}', {3})".format(
                ip_info[0], ip_info[1], ip_info[2], ip_info[3]
            )
        )
        conn.commit()


class GetIp(object):
    def delete_ip(self, ip):
        sql = """
            DELETE FROM proxy_ip WHERE ip='{0}'
            """.format(ip)
        cursor.execute(sql)
        conn.commit()
        return True

    def judge_ip(self, ip, port):
        # 判断ip是否可用
        http_url = "http://www.baidu.com"
        proxy_url = "http://{0}:{1}".format(ip, port)
        try:
            proxy_dict = {
                "http": proxy_url
            }
            response = requests.get(http_url, proxies=proxy_dict)
            return True
        except Exception as e:
            print("invalid ip and port")
            self.delete_ip(ip)
            return False
        else:
            code = response.status_code
            if code >= 200 and code < 300:
                print("effective ip")
                return True
            else:
                print("invalid ip and port")
                self.delete_ip(ip)
                return False

    def get_random_ip(self):
        sql = """
            SELECT ip, port FROM proxy_ip
            ORDER BY RAND()
            LIMIT 1
        """
        result = cursor.execute(sql)
        for ip_info in cursor.fetchall():
            ip = ip_info[0]
            port = ip_info[1]

            resutl = self.judge_ip(ip, port)
            if result:
                return "http://{0}:{1}".format(ip, port)
            else:
                return self.get_random_ip()

# if __name__ == "__main__":

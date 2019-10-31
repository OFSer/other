#!/usr/bin/env python3
import os
import re
import sys
import pymysql
import requests
import threading
from http import HTTPStatus

class Collectstaticfile:
    RE_DICT = {
        're_js' : '<\s*script[^>].*\ssrc=\"(.*)\">[^<]*<\s*/\s*script\s*>',
        're_css' : 'href=[\'"]?([^\'" >]+\.css)',
        're_png' : 'src=[\'"]?([^\'" >]+\.png)',
        're_jpg' : 'src=[\'"]?([^\'" >]+\.jpg)',
        're_asp' : 'href=[\'"]?([^\'" >]+\.asp)',
        're_aspx' : 'href=[\'"]?([^\'" >]+\.aspx)',
        're_php' : 'href=[\'"]?([^\'" >]+\.php)',
        're_html' : 'href=[\'"]?([^\'" >]+\.html)',
        're_dir' : 'href=[\'"]?([^\'" >]+\/)\"\>'
    }
    RE_LIST = [ 're_js', 're_css', 're_png', 
                're_jpg', 're_asp', 're_aspx', 
                're_php', 're_html', 're_dir' 
               ]

    def __init__(self, re_dict=RE_DICT, re_list=RE_LIST):
        self.re_dict = re_dict
        self.re_list = re_list
        self.web = requests.session()

    def get_url_text(self, url):
        r = self.web.get("{}".format(url))
        assert r.status_code == HTTPStatus.OK
        res = r.text
        return res

    def connect_mysql(self):
        db_config = {
            'host' : '10.0.100.71',
            'port' : 3307,
            'user' : 'root',
            'passwd' : 'hc2345678',
            'db' : 'dirsearch',
            'charset' : 'utf8'
        }
        cnx = pymysql.connect(**db_config)
        return cnx

    def add_data_to_mysql(self, re_policy, data):
        cnx = self.connect_mysql()
        if 'js' in re_policy:
            sql = """insert INTO js_path(path) VALUES ('{}');""".format(data)
            print (sql)
        elif 'css' in re_policy:
            sql = """insert INTO css_path(path) VALUES ('{}');""".format(data)
            print (sql)
        elif 'dir' in re_policy:
            sql = """insert INTO dir_path(path) VALUES ('{}');""".format(data) 
            print (sql)
        elif 'html' in re_policy:
            sql = """insert INTO html_path(path) VALUES ('{}');""".format(data)
            print (sql)
        elif 'php' in re_policy:
            sql = """insert INTO php_path(path) VALUES ('{}');""".format(data)
            print (sql)
        elif 'png' in re_policy or 'jpg' in re_policy:
            sql = """insert INTO img_path(path) VALUES ('{}');""".format(data)
            print (sql)
        elif 'asp' in re_policy or 'aspx' in re_policy:
            sql = """insert INTO asp_path(path) VALUES ('{}');""".format(data)
            print (sql)

        try:
            cus = cnx.cursor()
            cus.execute(sql)
            cus.close()
        except Exception as e:
            cnx.rollback()
            print ("Data addition error!")
            raise e
        finally:
            cnx.commit()
            cnx.close()
        return 

    def post_data_path(self, url, re_policy):
        res = self.get_url_text(url)
        re_data = re.compile(self.re_dict[re_policy], re.I)
        data_path_list = re_data.findall(res)
        data_path_list = list(set(data_path_list))
        for path_data in data_path_list:
            if 'http' not in path_data:
                self.add_data_to_mysql(re_policy, path_data)
        return

    def run(self):
        while 1:
            url = input("请输入要搜集的域名(多域名以逗号分隔)：")
            if url:
                if ',' in url:
                    url_list = url.split(',')
                    print (url_list)
                    for url in url_list:
                        for re_policy in self.re_list:
                            t = threading.Thread(target=self.post_data_path, args=(url, re_policy))
                            t.start()
                else:
                    for re_policy in self.re_list:
                        t = threading.Thread(target=self.post_data_path, args=(url, re_policy))
                        t.start()
                break
            else:
                print ("输入有误，请再次尝试！")
                continue

if __name__ == "__main__":
    Csf = Collectstaticfile()
    Csf.run()


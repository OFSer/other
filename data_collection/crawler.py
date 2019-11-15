#!/usr/bin/env python3
import re
import math
import sys
import time
import pymysql
import requests
import threading
from lxml import html
from urllib import parse
from bs4 import BeautifulSoup
from dataCollection import Collectstaticfile

class Browsersearch:
    HEADERS = { 
                "Accept":"text/html,application/xhtml+xml,application/xml;",
                "Accept-Encoding":"gzip",
                "Accept-Language":"zh-CN,zh;q=0.9",
                "Referer":"https://www.baidu.com/",
                "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36"
                }

    def __init__(self, headers=HEADERS):
        self.headers = headers
        self.web = requests.session()

    def connect_mysql(self):
        db_config = {
            'host' : '10.0.10.xx',
            'port' : 3307,
            'user' : 'root',
            'passwd' : 'sdsdsdsddd',
            'db' : 'dirsearch',
            'charset' : 'utf8'
        }
        cnx = pymysql.connect(**db_config)
        return cnx

    def get_pagenum(self, url):
        try:
            while 1:
                req = self.web.get(url, headers=self.headers)
                text = req.text
                r = re.search(r"找到相关结果约(.*?)个", text)
                if r:
                    num = r.group(1)
                    break
                else:
                    continue
            num = int(num.replace(",",""))
            return num
        except Exception as e:
            print(e)
            return  

    def set_keyword(self, keyword):
        http = "http://www.baidu.com/s?wd={}&gpc=0&ie=utf-8".format(parse.quote(keyword))
        print(http)
        return http

    def search(self, keyword, ctype):
        """gpc为搜索时间参数"""
        n = 0
        urls=[]
        url = self.set_keyword(keyword)
        num = self.get_pagenum(url)
        num_max = math.ceil(num/10)
        print("发现{}页".format(num_max))
        for i in range(num_max):
            print("开始爬第{}页".format(int(i+1)))
            http = url + "&pn={}".format(int(i*10))
            req = self.web.get(http, headers=self.headers)
            text = req.text
            soup = BeautifulSoup(text, "html.parser")
            b_list = soup.find_all("a", class_="c-showurl") 
            for b in b_list:
                try:
                    req = self.web.get(b["href"], headers=self.headers, allow_redirects=False)
                    text = req.headers["Location"]
                    urls.append(text)
                except KeyError as e:
                    #print (e)
                    continue
            for urldata in urls:
                cnx = self.connect_mysql() 
                urldata = re.split(r'(http://|https://|/)\s*', urldata)
                sqlExit = """SELECT url_data FROM tmp_urldata WHERE url_data='{}';""".format(urldata[2])
                result = cnx.cursor().execute(sqlExit)
                if result:
                    #print ("'{}' database alread exists, Skip!!".format(urldata[2]))
                    continue
                urldata_sql = """INSERT INTO tmp_urldata(url_data) VALUES ('{}');""".format(urldata[2])
                try:
                    cus = cnx.cursor()
                    cus.execute(urldata_sql)
                    cus.close()
                except Exception as e:
                    cnx.rollback()
                    print ("Data addition error!")
                    raise e
                finally:
                    cnx.commit()
                    cnx.close()
            n += 1
            if n % 20 == 0:
                Csf = Collectstaticfile()
                csf = threading.Thread(target=Csf.run, args=(ctype,))
                csf.start()
                csf.join()

        #所有执行完毕，清空域名数据表
        cnx = self.connect_mysql()
        clear_table_sql = """DELETE FROM tmp_urldata;"""
        cus = cnx.cursor()
        cus.execute(clear_table_sql)
        cus.close()
        cnx.commit()
        cnx.close()
        if cus:
            print ("URL数据表已经清空!")
        return urls

    def run(self):
        while 1:
            keyword = input("请输入要搜索的关键字:")
            if keyword:
                while 1:
                    ctype = input("请输入要采集的类型,逗号分隔(js|css|html|png|jpg|asp|aspx|php|dir|all):\n")
                    tag = ['js','css', 'html','png','jpg','asp','aspx','php','dir','all']
                    if ctype:
                        if ',' in ctype:
                            ctype = ctype.split(',')
                            for x in ctype:
                                if x in tag:
                                    continue
                                else:
                                    print ("你输入的采集类型{}不合法，退出程序！".format(x))
                                    sys.exit(1)
                        elif ctype not in tag:
                            print ("你的输入不合法，请重新输入！")
                            continue
                        else:
                            break
                    else:
                        print ("你的输入为空，请重新输入！")
                        continue
                    break
            else:
                print("你的输入为空，请重新输入！")
                continue
            isstart = input("是否开始采集(y/n)")
            if isstart.lower() == "y" or isstart.lower() == "yes" or isstart.lower() == "":
                pages= self.search(keyword, ctype)
                print ("此次搜索页面:", pages)
            elif isstart.lower() == "n" or isstart.lower() == "no":
                print ("不进行此次采集,退出程序.")
                sys.exit(0)
            else:
                print ("无法识别你的输入，请重新填写信息！")
                continue
              
if __name__ == '__main__':
    Bs = Browsersearch() 
    Bs.run()


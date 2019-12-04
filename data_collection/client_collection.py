#!/usr/bin/env python3
import re
import sys
import time
import math
import json
import socket
import asyncio
import random
import pymysql
import requests
import threading
from lxml import html
from urllib import parse
from bs4 import BeautifulSoup
from xmlrpc.client import ServerProxy
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

    def https_proxies(self):
        https_proxies_list = []
        req_proxy = self.web.get("http://lab.crossincode.com/proxy/get/?num=20&head=https")
        req_proxy = req_proxy.json()
        for n in range(20):
            https_proxies_list.append(req_proxy["proxies"][n]["https"])
        return https_proxies_list

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

    def rpc_collection_client(self, server_ip, ctype):
        time.sleep(20)
        print ("开始写入数据库！")
        e = ServerProxy("http://{}:9901".format(server_ip))  #同server_run.sh输入的ip地址
        e.collection_script(ctype)
        return

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
    
    def domain_obtain_ip(self):
        ip_pool = []
        urldata_sql = """SELECT url_data FROM tmp_urldata;"""
        cnx = self.connect_mysql()
        cus = cnx.cursor()
        cus.execute(urldata_sql)
        url_list = cus.fetchall()
        for url in url_list:
            ip_list = self.get_ip_list(url[0])
            for ip in ip_list: 
                ip_pool.append(ip)
        return ip_pool

    def get_ip_list(self, url):
        ip_list = []
        try:
            addrs = socket.getaddrinfo(url, None)
            for item in addrs:
                if item[4][0] not in ip_list:
                    if self.verifyisIPV4(item[4][0]) is True:
                        ip_list.append(item[4][0])
        except Exception as e:
            print (e)
        ip_list = list(set(ip_list))
        return ip_list

    def verifyisIPV4(self, ipaddr):
        compile_ip=re.compile('^(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[1-9])\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)$')
        if compile_ip.match(ipaddr):
            return True 
        else:  
            return False

    async def ip_obtain_domain(self, tmp_ip, num):
        domain_list = []
        ip = ("{0}{1}".format(tmp_ip,str(num)))
        api = "https://site.ip138.com/{}/".format(ip)
        try:
            req = self.web.get(api)
            text = req.text
        except Exception as e:
            text = ''
            pass
        if text:
            re_domains = re.findall(r"</span><a href=\"/(.*?)/\"", text)
            for domains in re_domains:
                domain_list.append(domains)
            domainlist = list(set(domain_list))
            for d in domainlist:
                cnx = self.connect_mysql()
                sqlex = """select domain from recheck_domain where domain='{}';""".format(d)
                result = cnx.cursor().execute(sqlex)
                if result:
                    cnx.close()
                    continue
                insert_sql = """insert into recheck_domain(domain) values ('{}');""".format(d)
                try:
                    cnx = self.connect_mysql()
                    cus = cnx.cursor()
                    cus.execute(insert_sql)
                    cus.close()
                except Exception as e:
                    cnx.rollback()
                    raise e
                finally:
                    cnx.commit()
                    cnx.close()
        return

    def set_keyword(self, keyword):
        http = "http://www.baidu.com/s?wd={}&gpc=0&ie=utf-8".format(parse.quote(keyword))
        print(http)
        return http

    def search(self, keyword, ctype, server_ip, https_proxies_list=[]):
        """gpc为搜索时间参数"""
        n = 0
        urls=[]
        url = self.set_keyword(keyword)
        num = self.get_pagenum(url)
        num_max = math.ceil(num/10)
        #print("发现{}页".format(num_max))
        threading.Thread(target=self.rpc_collection_client, args=(server_ip,ctype)).start()
        for i in range(num_max):
            #print("开始爬第{}页".format(int(i+1)))
            http = url + "&pn={}".format(int(i*10))
            if https_proxies_list:
                https_proxy = random.choice(https_proxies_list)
                proxies = {
                    "https":"https://{}".format(https_proxy)
                }
                req = self.web.get(http, headers=self.headers, proxies=proxies)
            else:
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
            ip_pool = self.domain_obtain_ip()
            for tmp_ip in ip_pool:
                tmp_ip = re.search(r"\b(\d{1,3}\.){2}\d{1,3}\.\b", tmp_ip)
                tmp_ip = tmp_ip.group()
                # 异步协程
                loop = asyncio.get_event_loop()
                func_list = (self.ip_obtain_domain(tmp_ip, num) for num in range(1, 255))
                loop.run_until_complete(asyncio.gather(*func_list))
                loop.close()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            n += 1
            if n % 20 == 0:
                https_proxies_list = self.https_proxies()

        #所有执行完毕，清空域名数据表
        cnx = self.connect_mysql()
        clear_table_sql1 = """TRUNCATE TABLE tmp_urldata;"""
        clear_table_sql2 = """TRUNCATE TABLE recheck_domain;"""
        cus = cnx.cursor()
        cus.execute(clear_table_sql1)
        cus.execute(clear_table_sql2)
        cus.close()
        cnx.commit()
        cnx.close()
        if cus:
            print ("域名数据表已经清空!")
        return 

    def run(self):
        while 1:
            keyword = input("请输入要搜索的关键字:")
            if keyword:
                while 1:
                    ctype = input("请输入要采集的类型,逗号分隔(js|css|html|png|jpg|gif|jpeg|asp|aspx|jsp|jspx|php|dir|all):\n")
                    tag = ['js','css', 'html',
                           'png','jpg','gif',
                           'jpeg','asp','aspx',
                           'jsp','jspx','php',
                           'dir','all']
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
            server_ip = input("请输入服务端的IP地址：")
            isstart = input("是否开始采集(y/n)")
            if isstart.lower() == "y" or isstart.lower() == "yes" or isstart.lower() == "":
                pages= self.search(keyword, ctype, server_ip)
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


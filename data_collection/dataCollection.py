#!/usr/bin/env python3
import os
import re
import sys
import time
import socket
import pymysql
import requests
import argparse
import threading
import subprocess
from http import HTTPStatus

class Collectstaticfile:
    RE_DICT = {
        'js_path' : 'src=[\'"]?([^\'" >]+\.js)',
        'css_path' : 'href=[\'"]?([^\'" >]+\.css)',
        'png_path' : 'src=[\'"]?([^\'" >]+\.png)',
        'jpg_path' : 'src=[\'"]?([^\'" >]+\.jpg)',
        'asp_path' : 'href=[\'"]?([^\'" >]+\.asp)',
        'aspx_path' : 'href=[\'"]?([^\'" >]+\.aspx)',
        'php_path' : 'href=[\'"]?([^\'" >]+\.php)',
        'html_path' : 'href=[\'"]?([^\'" >]+\.html)',
        'dir_path' : 'href=[\'"]?([^\'" >]+\/)\"\>'
    }
    RE_LIST = [ 'js_path', 'css_path', 'png_path', 
                'jpg_path', 'asp_path', 'aspx_path', 
                'php_path', 'html_path', 'dir_path' 
               ]

    def __init__(self, re_dict=RE_DICT, re_list=RE_LIST):
        self.re_dict = re_dict
        self.re_list = re_list
        self.web = requests.session()

    def http_get(self, url):
        try:
            r = self.web.get("http://{}".format(url))
            res = r.text
        except:
            pass
            return False
        return res

    def https_get(self, url):
        try:
            r = self.web.get("https://{}".format(url))
            res = r.text
        except:
            pass
            return False
        return res

    def get_url_text(self, url):
        try:
            resq = self.https_get(url)
            if resq:
                return resq
            else:
                resq2 = self.http_get(url)
                if resq2:
                    return resq2
        except:
            pass

    def connect_mysql(self):
        db_config = {
            'host' : '10.0.10.xx',
            'port' : 3307,
            'user' : 'root',
            'passwd' : 'sdsdsdsdsd',
            'db' : 'dirsearch',
            'charset' : 'utf8'
        }
        try:
            cnx = pymysql.connect(**db_config)
        except Exception as e:
            print (e)
            print ("Connect database failed!")
            sys.exit(1)
        return cnx

    def add_data_to_mysql(self, re_policy, data):
        cnx = self.connect_mysql()
        sqlExit = """SELECT path FROM {} WHERE path='{}';""".format(re_policy, data)
        result = cnx.cursor().execute(sqlExit)
        if result:
            #print ("'{}' database already exists, Skip!".format(data))
            return 
        sql = """insert INTO {}(path) VALUES ('{}');""".format(re_policy, data)
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
        data_path_list = re_data.findall(str(res))
        data_path_list = list(set(data_path_list))
        for path_data in data_path_list:
            if 'http' not in path_data:
                self.add_data_to_mysql(re_policy, path_data)
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
            addrs = socket.getaddrinfo(url,None)
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

    def ip_obtain_domain(self, tmp_ip):
        domain_list = []
        for num in range(1, 256):
            ip = ("{0}{1}".format(tmp_ip,str(num)))
            api = "https://site.ip138.com/{}/".format(ip)
            try:
                req = self.web.get(api, timeout=10)
                text = req.text
            except Exception as e:
                text = ''
                continue
            re_domains = re.findall(r"</span><a href=\"/(.*?)/\"", text)
            for domains in re_domains:
                domain_list.append(domains)
            domainlist = list(set(domain_list))
        return domainlist

    def run(self, ctype):
        ip_pool = self.domain_obtain_ip()
        for tmp_ip in ip_pool:
            tmp_ip = re.search(r"\b(\d{1,3}\.){2}\d{1,3}\.\b", tmp_ip)
            tmp_ip = tmp_ip.group()
            url_list = self.ip_obtain_domain(tmp_ip)
            for url in url_list:
                for re_policy in self.re_list:
                    if type(ctype) == list:
                        for k in ctype:
                            if k in re_policy:
                                t = threading.Thread(target=self.post_data_path, args=(url, re_policy))
                                t.start()
                                #t.join(timeout=10)
                    else:
                        if ctype in re_policy:
                            t = threading.Thread(target=self.post_data_path, args=(url, re_policy))
                            t.start()
                            #t.join(timeout=10)
                        elif ctype == 'all':
                            t = threading.Thread(target=self.post_data_path, args=(url, re_policy))
                            t.start()
                            #t.join(timeout=10)


if __name__ == "__main__":
    Csf = Collectstaticfile()
    Csf.run('js')

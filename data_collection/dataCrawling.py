#!/usr/bin/env python3
import os
import re
import sys
import time
import random
import pymysql
import requests
import threading
from http import HTTPStatus

requests.adapters.DEFAULT_RETRIES = 3

class Yujian:
    HEADERS = { 
            "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36"
            }

    def __init__(self, headers=HEADERS):
        self.web = requests.session()
        self.headers = headers

    
    def http_get(self, req_url, proxies):
        try:
            self.web.keep_alive = False
            r = self.web.get("http://{}".format(req_url), headers=self.headers, \
                             proxies=proxies, timeout=5, allow_redirects=False)
        except:
            pass
            return False
        return r

    def https_get(self, req_url, proxies):
        try:
            self.web.keep_alive = False
            r = self.web.get("https://{}".format(req_url), headers=self.headers, \
                             proxies=proxies, timeout=5, allow_redirects=False)
        except:
            pass
            return False
        return r
    
    def get_url(self, req_url, proxies):
        try:
            resq = self.https_get(req_url, proxies)
            if resq:
                return resq
            else:
                resq2 = self.http_get(req_url, proxies)
                if resq2:
                    return resq2
        except:
            pass

    def connect_mysql(self):
        db_config = {
            'host' : '10.0.100.71',
            'port' : 3307,
            'user' : 'root',
            'passwd' : 'hc2345678',
            'db' : 'dirsearch',
            'charset' : 'utf8'
        }
        try:
            cnx = pymysql.connect(**db_config)
            cus = cnx.cursor()
            cus.execute("set session net_write_timeout = 800")
            cus.close()
        except Exception as e:
            print (e)
            print ("Connect database failed!")
            sys.exit(1)
        return cnx

    def https_proxies(self):
        https_proxies_list = []
        req_proxy = self.web.get("https://proxy.horocn.com/api/v2/proxies?order_id=NLDP1651250202807991&num=20&format=json&line_separator=unix&can_repeat=yes")
        req_proxy = req_proxy.json()
        for n in req_proxy["data"]:
            req_proxy = "{}:{}".format(n["host"], n["port"])
            https_proxies_list.append(req_proxy)
        return https_proxies_list

    def call_data_table(self, call_table):
        path_list = []
        cnx = self.connect_mysql()
        cus = cnx.cursor(pymysql.cursors.SSCursor)
        tmp = cus.execute("SELECT path from {}_path".format(call_table))
        for path in cus:
            path_list.append(path[0])
        return path_list

    def splice_domain(self, domain_name, req_path, table_name, call_table, proxies_list):
        try:
            if req_path[0] != '/':
                req_url = "{}/{}".format(domain_name, req_path)
            else:
                req_url = "{}{}".format(domain_name, req_path)
            t = threading.Thread(target=self.verify_url_state, args=(req_url,table_name, call_table, proxies_list))        
            t.start()
        except IndexError as e:
            pass
        return 

    def mysql_execute(self, sql):
        cnx = self.connect_mysql()
        try:
            cus = cnx.cursor()
            cus.execute(sql)
            cus.close()
        except Exception as e:
            cnx.rollback()
            print("Data addition error!")
            raise e
        finally:
            cnx.commit()
            cnx.close()

    def write_file(self, req_url, table_name):
        db_dir = "db_file"
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        with open("{}/{}.txt".format(db_dir,table_name), 'at') as f:
            f.write("{}\n".format(req_url))

    def create_table(self, domain_name):
        if "http://" in domain_name or "https://" in domain_name:
            table_name = re.split(r"[//]", domain_name)[2]
        else:
            table_name = re.split(r"[//]", domain_name)[0]
        sqlExit = """
                    SELECT
                    	TABLE_NAME
                    FROM
                    	INFORMATION_SCHEMA. TABLES
                    WHERE
                    	TABLE_SCHEMA = 'dirsearch'
                    AND TABLE_NAME = '{}';
                """.format(table_name)
        cnx = self.connect_mysql()
        result = cnx.cursor().execute(sqlExit)
        if result:
            cnx.close()
            return table_name
        else:
            sql = """
                    CREATE TABLE IF NOT EXISTS `{}` (
                    `id` int(11) NOT NULL AUTO_INCREMENT,
                    `url` varchar(255) DEFAULT NULL,
                    `state` varchar(255) DEFAULT NULL,
                    PRIMARY KEY (`id`)
                    ) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8;
                """.format(table_name)
            self.mysql_execute(sql)
            return table_name 

    def verify_url_state(self, req_url, table_name, call_table, proxies_list):
        proxy = random.choice(proxies_list)
        proxies = {
                    "http":"http://{}".format(proxy),
                    "https":"http://{}".format(proxy)
                }
        if "http://" in req_url or "https://" in req_url:
            try:
                self.web.keep_alive = False
                #req_url = re.split(r"(http://|https://)", req_url)
                r = self.web.get("{}".format(req_url),headers=self.headers,proxies=proxies,allow_redirects=False, timeout=5)
            except:
                pass
                return 
        else:
            r = self.get_url(req_url, proxies)
        if r:
            sql_exit = """select url from `{}` where url="{}";""".format(table_name, req_url)
            cnx = self.connect_mysql()
            resu = cnx.cursor().execute(sql_exit)
            if resu:
                cnx.close()
                return
            if r.status_code == HTTPStatus.OK:
                sql_200 = """INSERT INTO `{}`(url,state) VALUES ('{}','{}');""".format(table_name, req_url, r.status_code)
                self.mysql_execute(sql_200)
                self.write_file(req_url, table_name) 

            if r.status_code == HTTPStatus.MOVED_PERMANENTLY:
                sql_301 = """INSERT INTO `{}`(url,state) VALUES ('{}','{}');""".format(table_name, req_url, r.status_code)
                self.mysql_execute(sql_301) 
                self.write_file(req_url, table_name) 

            if r.status_code == HTTPStatus.FOUND:
                sql_302 = """INSERT INTO `{}`(url,state) VALUES ('{}','{}');""".format(table_name, req_url, r.status_code)
                self.mysql_execute(sql_302)
                self.write_file(req_url, table_name) 

            if r.status_code == HTTPStatus.FORBIDDEN:
                sql_403 = """INSERT INTO `{}`(url,state) VALUES ('{}','{}');""".format(table_name, req_url, r.status_code)
                self.mysql_execute(sql_403)
                self.write_file(req_url, table_name) 
                tmp_list = re.split(r'[^/]+(?!.*/)', req_url)
                d_name = "{}".format(tmp_list[0])
                self.crawle(d_name, call_table, proxies_list)
            
    def crawle(self, domain_name, call_table, proxies_list):
        table_name = self.create_table(domain_name)
        path_list = self.call_data_table(call_table)
        for req_path in path_list:
            p = threading.Thread(target=self.splice_domain, args=(domain_name, req_path, table_name, call_table, proxies_list))
            p.start()

    def run(self):
        domain_names = input("输入要扫描的网站(逗号分隔)：")
        if domain_names:
            if ',' in domain_names:
                domain_names = domain_names.split(',')
            call_tables = input("请输入要调用的表类型(dir/img/asp/jsp/php/all)：")
            proxies_list = self.https_proxies()
            print ("获取高匿代理IP:{}".format(proxies_list))
            if call_tables:
                if ',' in call_tables:
                    call_tables = call_tables.split(',')
                if type(domain_names) == list:
                    for domain_name in domain_names:
                        if type(call_tables) == list:
                            for call_table in call_tables:
                                self.crawle(domain_name, call_table, proxies_list)
                        else:
                            self.crawle(domain_name, call_tables, proxies_list)
                else:
                    if type(call_tables) == list:
                        for call_table in call_tables:
                            self.crawle(domain_names, call_table, proxies_list)
                    else:
                        self.crawle(domain_names, call_tables, proxies_list)

if __name__ == "__main__":
    yj = Yujian()
    yj.run()

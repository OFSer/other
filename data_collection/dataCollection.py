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

requests.adapters.DEFAULT_RETRIES = 3

class Collectstaticfile:
    RE_DICT = {
        'js_path' : 'src=[\'"]?([^\'" >]+\.js)',
        'css_path' : 'href=[\'"]?([^\'" >]+\.css)',
        'html_path' : 'href=[\'"]?([^\'" >]+\.html)',
        'png_path' : 'src=[\'"]?([^\'" >]+\.png)',
        'jpg_path' : 'src=[\'"]?([^\'" >]+\.jpg)',
        'gif_path' : 'src=[\'"]?([^\'" >]+\.gif)',
        'jpeg_path' : 'src=[\'"]?([^\'" >]+\.jpeg)',
        'asp_path' : 'href=[\'"]?([^\'" >]+\.asp)',
        'aspx_path' : 'href=[\'"]?([^\'" >]+\.aspx)',
        'php_path' : 'href=[\'"]?([^\'" >]+\.php)',
        'dir_path' : 'href=[\'"]?([^\'" >]+\/)\"\>',
        'jsp_path' : 'href=[\'"]?([^\'" >]+\.jsp)',
        'jspx_path' : 'href=[\'"]?([^\'" >]+\.jspx)'
    }
    RE_LIST = [ 'js_path', 'css_path', 'html_path',
                'png_path', 'jpg_path', 'gif_path',
                'jpeg_path','asp_path', 'aspx_path', 
                'php_path', 'dir_path', 'jsp_path',
                'jspx_path']

    def __init__(self, re_dict=RE_DICT, re_list=RE_LIST):
        self.re_dict = re_dict
        self.re_list = re_list
        self.web = requests.session()

    def http_get(self, url):
        try:
            self.web.keep_alive = False
            r = self.web.get("http://{}".format(url))
            res = r.text
        except:
            pass
            return False
        return res

    def https_get(self, url):
        try:
            self.web.keep_alive = False
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
            'host' : '10.0.100.71',
            'port' : 3307,
            'user' : 'root',
            'passwd' : 'hc2345678',
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

    def db_remove_repeat(self):
        table_list = ['dir_path', 'img_path', 'asp_path', 'jsp_path', 'php_path']
        for table in table_list:
            sqlRecheckRemoveRepeat = """
                DELETE FROM `{0}` WHERE (path)
                IN
                (SELECT path FROM (SELECT path FROM `{0}` GROUP BY path HAVING COUNT(*)>1) s1)
                AND
                id NOT in (SELECT id FROM (SELECT id FROM `{0}` GROUP BY path HAVING COUNT(*)>1) s2);""".format(table)
            cnx = self.connect_mysql()
            recheck_data = cnx.cursor()
            recheck_data.execute(sqlRecheckRemoveRepeat)
            cnx.commit()
            cnx.close()
        return 

    def add_data_to_mysql(self, re_policy, data):
        cnx = self.connect_mysql()
        if 'js' in re_policy or 'css' in re_policy or 'html' in re_policy:
            sqlExit = """SELECT path FROM dir_path WHERE path='{}';""".format(data)
            sql = """insert INTO dir_path(path) VALUES ('{}');""".format(data)
        elif 'png' in re_policy or 'jpg' in re_policy or 'gif' in re_policy or 'jpeg' in re_policy:
            sqlExit = """SELECT path FROM img_path WHERE path='{}';""".format(data)
            sql = """insert INTO img_path(path) VALUES ('{}');""".format(data)
        elif 'asp' in re_policy or 'aspx' in re_policy:
            sqlExit = """SELECT path FROM asp_path WHERE path='{}';""".format(data)
            sql = """insert INTO asp_path(path) VALUES ('{}');""".format(data)
        elif 'jsp' in re_policy or 'jspx' in re_policy:
            sqlExit = """SELECT path FROM jsp_path WHERE path='{}';""".format(data)
            sql = """insert INTO jsp_path(path) VALUES ('{}');""".format(data)
        else:
            sqlExit = """SELECT path FROM {} WHERE path='{}';""".format(re_policy, data)
            sql = """insert INTO {}(path) VALUES ('{}');""".format(re_policy, data)
        result = cnx.cursor().execute(sqlExit)
        if result:
            print ("'{}' database already exists, Skip!".format(data))
            return 
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
        threading.Thread(target=self.db_remove_repeat).start()
        return 

    def post_data_path(self, url, re_policy):
        res = self.get_url_text(url)
        re_data = re.compile(self.re_dict[re_policy], re.I)
        data_path_list = re_data.findall(str(res))
        data_path_list = list(set(data_path_list))
        for path_data in data_path_list:
            if 'http' not in path_data:
                if '.js' in path_data or '.css' in path_data or '.html' in path_data:
                    tmp_list = re.split(r'[^/]+(?!.*/)', path_data)
                    path_data = tmp_list[0]
                    self.add_data_to_mysql(re_policy, path_data)
                else:
                    self.add_data_to_mysql(re_policy, path_data)
        return

    def run(self, ctype):
        self.db_remove_repeat()
        n1 = 0
        x = 0
        while 1:
            time.sleep(3)
            print ("n1的当前值是：{}".format(n1))
            cnx = self.connect_mysql()
            sql = """select domain from recheck_domain;"""
            n2 = cnx.cursor().execute(sql)
            cnx.close()
            if n2 == n1:
                time.sleep(30)
                x += 1
                if x % 20 == 0:
                    time.sleep(1800)
                continue
            if n1 == 0:
                sql1 = """select domain from recheck_domain limit 0, {};""".format(n2)
                cnx = self.connect_mysql()
                cus = cnx.cursor()
                nn = cus.execute(sql1)
                url_list = cus.fetchall()
                n1 = n2
                cnx.close()
            else:
                sql2 = """select domain from recheck_domain limit {}, {}; """.format(n1, n2-n1)
                cnx = self.connect_mysql()
                cus = cnx.cursor()
                nn = cus.execute(sql2)
                url_list = cus.fetchall()
                n1 = n2
                cnx.close

            for url in url_list:
                for re_policy in self.re_list:
                    if type(ctype) == list:
                        for k in ctype:
                            if k in re_policy:
                                t = threading.Thread(target=self.post_data_path, args=(url[0], re_policy))
                                t.start()
                                #t.join()
                    else:
                        if ctype in re_policy:
                            t = threading.Thread(target=self.post_data_path, args=(url[0], re_policy))
                            t.start()
                            #t.join()
                        elif ctype == 'all':
                            t = threading.Thread(target=self.post_data_path, args=(url[0], re_policy))
                            t.start()
                            #t.join()
             

if __name__ == "__main__":
    Csf = Collectstaticfile()
    Csf.run(sys.argv[1])

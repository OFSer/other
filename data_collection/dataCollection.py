#!/usr/bin/env python3
import os
import re
import sys
import pymysql
import requests
import argparse
import threading
from http import HTTPStatus

class Collectstaticfile:
    RE_DICT = {
        'js_path' : '<\s*script[^>].*\ssrc=\"(.*)\">[^<]*<\s*/\s*script\s*>',
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

    def get_url_text(self, url):
        try:
            r = self.web.get("https://{}".format(url))
        except Exception as e:
            r = self.web.get("http://{}".format(url))
        #assert r.status_code == HTTPStatus.OK
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
        sqlExit = """SELECT path FROM {} WHERE path='{}';""".format(re_policy, data)
        result = cnx.cursor().execute(sqlExit)
        if result:
            print ("'{}' database already exists, Skip!".format(data))
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
        data_path_list = re_data.findall(res)
        data_path_list = list(set(data_path_list))
        for path_data in data_path_list:
            if 'http' not in path_data:
                self.add_data_to_mysql(re_policy, path_data)
        return

    def call_script_get_subdomain(self, first_level_domain_name, scan_threads="", scan_process=""):
        url_list = []
        if scan_threads:
            os.system('./subDomainsBrute.py {} -t {}'.format(first_level_domain_name, scan_threads))
        elif scan_process:
            os.system('./subDomainsBrute.py {} -p {}'.format(first_level_domain_name, scan_process))
        elif scan_threads and scan_process:
            os.system('./subDomainsBrute.py {} -t {} -p {}'.format(first_level_domain_name, scan_threads, scan_process))
        else:
            os.system('./subDomainsBrute.py {}'.format(first_level_domain_name))
        with open('./{}.txt'.format(first_level_domain_name), 'r') as fi:
            for line in fi:
                url_list.append(line.split()[0])
        return url_list

    def run(self):
        parser = argparse.ArgumentParser(prog='dataCollection.py')
        parser.add_argument('-d', required=True, help='First-level domain name')
        parser.add_argument('-t', help='Num of scan threads, 200 by default')
        parser.add_argument('-p', help='Num of scan Process, 6 by default')
        parser.add_argument('--full', action='store_true', help='Full scan, NAMES FILE subnames_full.txt will be used to brute')
        parser.add_argument('--ignore-intranet', action='store_true', help='Ignore domains pointed to private IPs')
        args = parser.parse_args()
        first_level_domain_name = args.d
        scan_threads = args.t
        scan_process = args.p
        url_list = self.call_script_get_subdomain(first_level_domain_name, scan_threads, scan_process)
        for url in url_list:
            for re_policy in self.re_list:
                t = threading.Thread(target=self.post_data_path, args=(url, re_policy))
                t.start()
                t.join(timeout=10)

if __name__ == "__main__":
    Csf = Collectstaticfile()
    Csf.run()


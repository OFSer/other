import re
import os
import csv
import sys
import time
import random
import requests
import threading
from lxml import html
from http import HTTPStatus

def https_proxies():
    https_proxies_list = []
    req_proxy = requests.get("http://lab.crossincode.com/proxy/get/?num=20&head=https")
    req_proxy = req_proxy.json()
    for n in range(20):
        https_proxies_list.append(req_proxy["proxies"][n]["https"])
    return https_proxies_list

def get_vip_url_list(page, headers, proxies):
    url = "http://www.ssp28.pw/e/member/list/index.php"
    web = requests.session()
    r = web.get("{}?page={}&sear=1&hh[]=&keyboard[]=&totalnum=360108".format(url, page),headers=headers,proxies=proxies)
    #assert r.status_code == HTTPStatus.OK
    tree = html.fromstring(r.text)
    #从会员空间采集
    #vip_url_list = tree.xpath("//td/div/a[2]/@href")
    #从会员资料采集
    vip_url_list = tree.xpath("//td/div/a[1]/@href")
    return vip_url_list

def get_vip_info(para, headers, proxies):
    try:
        url = "http://www.ssp28.pw"
        vip_r = requests.get("{}{}".format(url,para), headers=headers, proxies=proxies)
        #assert vip_r.status_code == HTTPStatus.OK
    except:
        pass
        return
    try:
        tree = html.fromstring(vip_r.text)
        #从会员空间采集
        #email = tree.xpath("//td/a/@href")[7]
        email = tree.xpath("//td/a/@href")[3]
        email = re.split("[:]", email)
        #从会员资料采集
        #tel = tree.xpath("//td/text()")[31]
        tel = tree.xpath("//td/text()")[19]
        if tel == "QQ号码:":
            tel = "该用户没输入手机号"
        info_tuple = (email[1], tel)
        print (info_tuple)
    except:
        time.sleep(5)
        pass
        return
    return info_tuple

def save_csv(tuple_rows):
    #Windows
    #os.makedirs("D:\\", exist_ok=True)
    #with open("D:\\email_tel.csv","a", encoding="gbk") as f:
    #    f_csv = csv.writer(f)
    #    f_csv.writerows(tuple_rows)

    #Linux
    os.makedirs("./info/", exist_ok=True)
    with open("./info/email_tel.csv","a", encoding="utf-8") as f:
        f_csv = csv.writer(f)
        f_csv.writerows(tuple_rows)

def execute_threads(headers, para_list, https_proxies_list):
    tuple_rows = []
    for para in para_list:
        https_proxy2 = random.choice(https_proxies_list)
        proxies2 = {"https":"https://{}".format(https_proxy2)}
        print ("two choice:",proxies2)
        info_tuple = get_vip_info(para, headers, proxies2)
        if info_tuple:
            tuple_rows.append(info_tuple)
        else:
            time.sleep(5)
            continue
        save_csv(tuple_rows)

def main():
    tuple_rows = []
    https_proxies_list = https_proxies()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36'}
    for page in range(18006):
#        if page % 100 == 0:
#            https_proxies_list = https_proxies()
        https_proxy = random.choice(https_proxies_list)
        proxies = {"https":"https://{}".format(https_proxy)}
        print("one choice:",proxies)
        para_list = get_vip_url_list(page, headers, proxies)
        t = threading.Thread(target=execute_threads, args=(headers,para_list,https_proxies_list))
        t.start()

if __name__ == "__main__":
    main()

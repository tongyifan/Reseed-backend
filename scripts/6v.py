#! /usr/bin/python3
# -*- coding: utf-8 -*-
import os
import re
from http.cookies import SimpleCookie

import requests
from bs4 import BeautifulSoup

COOKIES = ""  # fixme: 修改这里的Cookies，格式为"k1=v1; k2=v2;"
DOWNLOAD_DIR = "./"  # fixme: 种子下载至

HEADERS = {
    'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/78.0.3904.108 Safari/537.36"
}
BASE_URL = "http://bt.neu6.edu.cn/"


def parse_cookies(cookies_raw: str) -> dict:
    """
    格式化cookies
    :param cookies_raw: k=v;形式的cookies
    :return: {k:v}形式的cookies
    """
    return {key: morsel.value for key, morsel in SimpleCookie(cookies_raw).items()}


def download_torrent(sid):
    if os.path.exists(DOWNLOAD_DIR + '/{}.torrent'.format(sid)):
        return "存在种子文件，跳过：{}".format(sid)

    try:
        torrent_page = requests.get(BASE_URL + 'thread-{}-1-1.html'.format(sid),
                                    cookies=parse_cookies(COOKIES), headers=HEADERS, timeout=30)
    except requests.RequestException:
        return "获取详情页错误，种子ID：{}".format(sid)
    if 'member.php' in torrent_page.url:
        return "Cookies过期，请手动更换Cookies", -1

    torrent_page.encoding = "gbk"  # 修改编码
    torrent_page_bs = BeautifulSoup(torrent_page.text, "lxml")  # 解析页面

    title = torrent_page_bs.title.get_text()

    if not re.search("(提示信息|我关注的)", title):
        if torrent_page_bs.find("img", src="static/image/filetype/torrent.gif"):
            # 正常种子
            download_link = ""
            for attnm in torrent_page_bs.find_all('p', {"class": "attnm"}):
                if '.torrent' in attnm.find('a').text:
                    download_link = BASE_URL + attnm.find('a').get('href')
            if not download_link:
                for attachment in torrent_page_bs.find_all(
                        'a', {'href': re.compile('^forum.php\\?mod=attachment.*')}):
                    if '.torrent' in attachment.text:
                        download_link = BASE_URL + attachment.get('href')
            resp = requests.get(download_link, cookies=parse_cookies(COOKIES), timeout=60, headers=HEADERS)
            if resp.headers.get('Content-Type') != 'application/x-bittorrent':
                _bs = BeautifulSoup(resp.text, 'lxml')
                dl_redirect_link = _bs.find("p", {"class": "alert_btnleft"}).find('a').get('href')
                resp = requests.get(BASE_URL + dl_redirect_link, cookies=parse_cookies(COOKIES),
                                    timeout=60, headers=HEADERS)

            with open(DOWNLOAD_DIR + '/{}.torrent'.format(sid), 'wb') as fp:
                fp.write(resp.content)
            return "下载成功：{}".format(sid)

        else:
            return "非种子/试种区/无权限：{}".format(sid)
    else:
        return "种子不存在：{}".format(sid)


if __name__ == '__main__':
    if not os.path.exists(DOWNLOAD_DIR):
        try:
            os.mkdir(DOWNLOAD_DIR)
        except FileNotFoundError:
            print("请填写正确的DOWNLOAD_DIR")
            exit()

    with open("./6v.txt", 'r') as fp:
        torrents = re.findall("thread-(\\d*)-1-1.html", fp.read())
    for sid in torrents:
        result = download_torrent(sid)
        if type(result) == tuple:
            print(result[0])
            exit()
        else:
            print(result)

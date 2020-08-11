#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName   :main.py
# @Author     :Shuranima
# @Time       :2020/8/11 19:00


import sys
import os

path = os.path.abspath(os.path.join(os.getcwd(), "../..")) + '\\' + 'spider'
sys.path.append(path)

from spider.pornhub import Pornhub
from multiprocessing import Pool
from spider.download import download
import re


def download_pool(lt):
    # 如果因前面解析失败 出现None则利用异常跳过
    try:
        file_url = lt['mp4_url']
        filepath = './XO/Mini Diva'
        filename = re.sub('[\/:*?"<>|]', '-', lt['title']) + '.mp4'  # 去掉非法字符
        download(file_url, filepath, filename)
    except Exception as ep:
        print(ep)
        return None


def run_pool(pool_count, func, iterable):
    pool = Pool(pool_count)
    ret = pool.map(func, iterable)
    pool.close()
    pool.join()
    return ret


def main():
    por = Pornhub()
    details_page = por.author('Mini Diva', 1, 1)
    if not len(details_page):
        return None
    print('开始获取视频下载地址：')
    mp4_list = run_pool(5, por.get_video_list, details_page)
    run_pool(5, download_pool, mp4_list)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print(e)
        exit()

#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName   :download.py
# @Author     :Shuranima
# @Time       :2020/8/11 19:00

import os
import requests
from tqdm import tqdm
import time
from spider.ua import HEADERS
import random


def down_from_url(url, dst):
    headers = random.choice(HEADERS)

    with requests.get(url, headers=headers, stream=True) as req:  # (1)
        if 200 != req.status_code and 206 != req.status_code:
            return -1
        file_size = int(req.headers['content-length'])  # (2)
        if os.path.exists(dst):
            first_byte = os.path.getsize(dst)  # (3)
        else:
            first_byte = 0
        if first_byte >= file_size:  # (4)
            return file_size

    headers['Range'] = f"bytes={first_byte}-{file_size}"

    pbar = tqdm(total=file_size, initial=first_byte, unit='B', unit_scale=True, desc=dst)
    with requests.get(url, headers=headers, stream=True) as req:  # (5)
        if 200 != req.status_code and 206 != req.status_code:
            return -1
        with open(dst, 'ab') as f:
            for chunk in req.iter_content(chunk_size=1024):  # (6)
                if chunk:
                    f.write(chunk)
                    pbar.update(1024)
        pbar.close()
    return file_size


def download(url, path, filename):
    if not os.path.exists(path):
        os.makedirs(path)
    print('地址：' + url)
    print('开始下载,' + filename)
    start_time = time.time()
    if os.path.exists(path + '/' + filename):
        start_file_size = os.path.getsize(path + '/' + filename)  # (3)
    else:
        start_file_size = 0

    mp4_size = down_from_url(url, path + '/' + filename)

    if os.path.exists(path + '/' + filename):
        end_file_size = os.path.getsize(path + '/' + filename)  # (3)
    else:
        end_file_size = 0
    end_time = time.time()
    if -1 == mp4_size:
        print(
            f"下载失败--文件初始大小：{start_file_size}/byte，下载大小：{end_file_size - start_file_size}/byte，视频大小：{mp4_size}，花费时间：{end_time - start_time}/s")
    elif end_file_size < mp4_size:
        print(
            f"下载未完成--文件初始大小：{start_file_size}/byte，下载大小：{end_file_size - start_file_size}/byte，视频大小：{mp4_size}，花费时间：{end_time - start_time}/s")
    else:
        print(
            f"下载已完成--文件初始大小：{start_file_size}/byte，下载大小：{end_file_size - start_file_size}/byte，视频大小：{mp4_size}，花费时间：{end_time - start_time}/s")

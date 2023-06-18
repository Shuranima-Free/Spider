#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName   :pornhub.py
# @Author     :Shuranima
# @Time       :2023/6/18 15:52

import requests
import random
from lxml import etree
import js2py

from spider.ua import HEADERS


class Pornhub:
    """
        Pornhub Spider
    """

    def __init__(self):
        self.home_url = 'https://cn.pornhub.com'
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/83.0.4103.106 Safari/537.36'}
        self.ses = requests.session()
        self.ses.get(url='https://cn.pornhub.com/', headers=self.headers)
        self.__judge_the_wall()

    def __judge_the_wall(self):
        """
            验证是否能连接外网
        :return: yes:status_code no:网速不佳或它未在墙外，请它出去后再使用~
        """
        try:
            response = requests.get('https://cn.pornhub.com/', self.headers, timeout=5)
            return response.status_code
        except Exception:
            raise Exception('网速不佳或它未在墙外，请它出去后再使用~')

    def __get_response(self, url):
        """
            获取url响应
        :param url: url
        :return: response
        """
        self.headers = random.choice(HEADERS)
        try:

            with self.ses.get(url=url, headers=self.headers, timeout=180) as response:
                return response
        except Exception as e:
            print(e)
            return None

    def get_details_page_list(self, url):
        """
            从视频页面获取详情页url列表
        :param url: 视频页url
        :return: 详情页列表--格式：[{'data_id': data_id, 'url':url, 'title': title}, ]
        """
        response = self.__get_response(url)
        if response is None:
            return None
        data = response.content.decode('utf-8')
        tree = etree.HTML(data)
        # 无搜索结果  #没发现页面
        page_title = tree.xpath('/html/head/title[1]/text()')[0]
        print(page_title)
        if '无搜索结果' in page_title or '没发现页面' in page_title:
            return None
        li_list = tree.xpath('//*[@id="mostRecentVideosSection"]/li')
        if not len(li_list):
            li_list = tree.xpath('//*[@id="videoSearchResult"]/li')
            li_list = li_list[2:]
        details_page_list = []
        # 获取所有详情页
        for li in li_list:
            data_id = li.xpath('./@data-id')[0]
            url = li.xpath('./div/div[3]/span/a/@href')[0]
            title = li.xpath('./div/div[3]/span/a/@title')[0]
            details_page_dic = {
                'data_id': data_id,
                'url': self.home_url + url,
                'title': title
            }
            details_page_list.append(details_page_dic)
        return details_page_list

    def get_video(self, url, data_id):
        """
            解析mp4下载地址
        :param url: 详情页url
        :param data_id: 详情页ID
        :return: MP4下载地址
        """
        #print(url)
        response = self.__get_response(url)
        if response is None:
            return None
        #print(response)
        data = response.content.decode('utf-8')
        tree = etree.HTML(data)
        # 解析出js代码
        player = tree.xpath('//*[@id="player"]/script[1]/text()')[0]
        # 去除无用代码
        script = player[:player.find('playerObjList')]
        # 执行js函数返回 flashvars
        # js = execjs.compile(r'function flashvars(){' + script + ' return flashvars_' + data_id + ';}')
        # flashvars = js.call('flashvars')
        # print(flashvars)
        context = js2py.EvalJs()
        js_content = 'function flashvars(){ '+ script +' return flashvars_' + data_id + ';}'
        context.execute(js_content)
        flashvars = context.flashvars()

        VideoUrl = ''
        for ele in flashvars['mediaDefinitions']:
            if ele['format']=='mp4':
                VideoUrl = ele['videoUrl']
        response = self.__get_response(VideoUrl)
        json = response.json()
        mp4_url = json[-1]['videoUrl']
        # # 几种清晰度
        # quality_list = ['quality_1080p', 'quality_720p', 'quality_480p', 'quality_240p', ]
        # quality_index = 0
        # 获取视频地址  始终获取最高品质
        # while True:
        #     try:
        #         mp4_url = flashvars[quality_list[quality_index]]
        #         break
        #     except IndexError as e:
        #         print(e)
        #         quality_index += 1
        #         if quality_index > 3:
        #             raise Exception('解析视频错误!')
        return mp4_url

    def get_video_list(self, details_page):
        """
            解析出详情页中的mp4下载地址
        :param details_page: 详情页--格式：{'data_id': data_id, 'url':url, 'title': title}
        :return: 返回mp4列表--格式：{'data_id': data_id, 'title': title, 'mp4_url': mp4_url}
        """
        mp4_url = self.get_video(details_page['url'], details_page['data_id'])
        if mp4_url is None:
            return None
        video_dic = {
            'data_id': details_page['data_id'],
            'title': details_page['title'],
            'mp4_url': mp4_url
        }
        print(video_dic)
        return video_dic

    def search(self, value, start, end):
        """
            使用搜索获取,返回一个详情页列表
        :param value:搜索内容
        :param start:开始页码
        :param end:结束页码
        :return:返回详情页列表--格式：[{'data_id': data_id, 'url':url, 'title': title}, ]
        """
        count = (end - start) + 1
        if count <= 0:
            print('选择页码出错~,请重新选择。')
            return None
        else:
            print('预计爬去页码数为：' + str(count))
        # 根据抓包得知Pornbub搜索规则，将小写转换为大写，并且将空格转换为+
        value_rep = value.lower().replace(' ', '+')
        # 需要遍历的页面数量
        details_page_list = []
        page_count = 0
        for page in range(start, end + 1):
            # https://cn.pornhub.com/video/search?search=mini+diva&page=2
            search_url = 'https://cn.pornhub.com/video/search?search=' + value_rep + '&page=' + str(page)
            print(search_url)
            temp = self.get_details_page_list(search_url)
            if temp is None:
                break
            else:
                details_page_list += temp
            page_count += 1
        print('实际爬取页码数量为：' + str(page_count))
        return details_page_list

    def author(self, value, start, end):
        """
            使用作者获取,返回一个详情页列表
        :param value:作者
        :param start:开始页码
        :param end:结束页码
        :return:返回详情页列表--格式：[{'data_id': data_id, 'url':url, 'title': title}, {'data_id': data_id, 'url':url, 'title': title}, ]
        """
        count = (end - start) + 1
        if count <= 0:
            print('选择页码出错~,请重新选择。')
            return None
        else:
            print('预计爬取页码数为：' + str(count))
        # 根据抓包得知Pornbub搜索规则，将小写转换为大写，并且将空格转换为+
        value_rep = value.lower().replace(' ', '-')
        # 需要遍历的页面数量
        details_page_list = []
        page_count = 0
        for page in range(start, end + 1):
            # 'https://cn.pornhub.com/model/mini-diva'
            # 这是获取作者首页，暂时需要的是她的视频页
            # self.author_url = 'https://cn.pornhub.com/model/' + temp
            # https://cn.pornhub.com/model/mini-diva/videos?page=2
            author_url = 'https://cn.pornhub.com/model/' + value_rep + '/videos' + '?page=' + str(page)
            print(author_url)
            temp = self.get_details_page_list(author_url)
            if temp is None:
                break
            else:
                details_page_list += temp
            page_count += 1
        print('实际爬取页码数量为：' + str(page_count))
        return details_page_list

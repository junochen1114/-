# coding:utf-8

import requests
import base64
from io import BytesIO
import numpy as np
from lxml import etree
import pymongo
from pymongo import MongoClient
import time
import datetime
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

username = 'root'
password = '1114'
host = '172.16.100.197'
port = 27017
authSource = 'chen'


class doubanMovie:
    def __init__(self):
        self.conn = MongoClient('mongodb://{}:{}@{}:{}/?authSource={}'.format(username, password, host, port, authSource))
        self.url_db = self.conn['chen']['doubanMovieURL']  # name/url/score
        self.db = self.conn['chen']['doubanMovie']
        # self.movie_label = ['热门', '最新', '经典', '可播放', '豆瓣高分', '冷门佳片', '华语', '欧美', '韩国', '日本',
        #                     '动作', '喜剧', '爱情', '科幻', '悬疑', '恐怖', '文艺']
        self.headers = {
            'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36'
        }

    def savedb(self, dic, db=''):
        if db == 'url':
            self.url_db.save(dic)
        else:
            self.db.save(dic)
        return True

    def sleep_time(self):
        s_time = np.random.randint(3, 6)
        # s_time = np.random.randint(4, 10)
        time.sleep(s_time)
        print('等待%s' % s_time, '秒')

    def check_repeat(self, movie_name, movie_url, db=''):
        query = {'$or': [{"name": movie_name}, {"url": movie_url}]}
        if db == 'url':
            search_cursor = self.url_db.find(query)
        else:
            search_cursor = self.db.find(query)
        if search_cursor.count() > 0:
            return True
        return False

    def run(self):
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug
        options.add_argument('--headless')  # 浏览器不提供可视化页面. linux下如果系统不支持可视化不加
        # browser = webdriver.Chrome(chrome_options=options)
        browser = webdriver.Chrome(options=options)
        browser.get('https://movie.douban.com/')
        browser.find_element_by_xpath("//div[2]/div/ul/li[2]/a").click()
        self.sleep_time()

        _selenium_html = browser.execute_script("return document.documentElement.outerHTML")
        _html = etree.HTML(_selenium_html)
        movie_label = _html.xpath("//div[@class='tag-list']/label")

        for i in range(len(movie_label)):
            try:
                browser.find_element_by_xpath("//div[@class='tag-list']/label[" + str(i + 1) + "]").click()
                print("time ", i+1, " click, success")
                self.sleep_time()
                while ~("display: none;" == browser.find_element_by_xpath("//div[4]/a").get_attribute("style")):
                    if "display: none;" == browser.find_element_by_xpath("//div[4]/a").get_attribute("style"):
                        break
                    try:
                        label_url = browser.current_url
                        _selenium_html = browser.execute_script("return document.documentElement.outerHTML")
                        _html = etree.HTML(_selenium_html)
                        #  爬取的起始和终止电影，终止点其实是电影个数
                        start = int(str(label_url).split("=")[-1])
                        end = len(_html.xpath("//div[@class='list']/a[@class='item']"))
                        ####### obtain page_url #######
                        for movie_num in range(start+1, end+1):
                            try:
                                movie_url = _html.xpath("//div[@class='list']/a[" + str(movie_num) + "]/@href")[0].split('?')[0]
                                movie_new = 'No'
                                movie_name = _html.xpath("//div[@class='list']/a[" + str(movie_num) + "]/p/text()")[0]\
                                    .replace('\n', '').strip()
                                movie_score = float(
                                    _html.xpath("//div[@class='list']/a[" + str(movie_num) + "]/p/strong/text()")[0])
                                if movie_name == '':
                                    movie_name = _html.xpath("//div[@class='list']/a[" + str(movie_num) + "]/p/text()")[1]\
                                        .replace('\n', '').strip()
                                    movie_new = 'Yes'

                                # myid = ''.join((str(uuid.uuid4())).split('-'))
                                update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                item = {
                                    # 'id': myid,
                                    'updateTime': update_time,
                                    'url': movie_url,
                                    'name': movie_name,
                                    'new': movie_new,
                                    'score': movie_score,
                                }
                                if not self.check_repeat(movie_name, movie_url, 'url'):
                                    self.savedb(item, 'url')
                                    print(item)
                                else:
                                    print('data replicated: ', movie_name)
                            except Exception as e:
                                print(e)
                        load_more = browser.find_element_by_xpath("//div[4]/a")
                        load_more.click()
                        self.sleep_time()
                    except Exception as e:
                        print(e)

                # 没有“加载更多”了
                label_url = browser.current_url
                _selenium_html = browser.execute_script("return document.documentElement.outerHTML")
                _html = etree.HTML(_selenium_html)
                start = int(str(label_url).split("=")[-1])
                end = len(_html.xpath("//div[@class='list']/a[@class='item']"))
                ####### obtain page_url #######
                for movie_num in range(start + 1, end + 1):
                    try:
                        movie_url = _html.xpath("//div[@class='list']/a[" + str(movie_num) + "]/@href")[0].split('?')[0]
                        movie_new = 'No'
                        movie_name = _html.xpath("//div[@class='list']/a[" + str(movie_num) + "]/p/text()")[0] \
                            .replace('\n', '').strip()
                        movie_score = float(
                            _html.xpath("//div[@class='list']/a[" + str(movie_num) + "]/p/strong/text()")[0])
                        if movie_name == '':
                            movie_name = _html.xpath("//div[@class='list']/a[" + str(movie_num) + "]/p/text()")[1] \
                                .replace('\n', '').strip()
                            movie_new = 'Yes'

                        # myid = ''.join((str(uuid.uuid4())).split('-'))
                        update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        item = {
                            # 'id': myid,
                            'updateTime': update_time,
                            'url': movie_url,
                            'name': movie_name,
                            'new': movie_new,
                            'score': movie_score,
                        }
                        if not self.check_repeat(movie_name, movie_url, 'url'):
                            self.savedb(item, 'url')
                            print(item)
                        else:
                            print('data replicated: ', movie_name)
                    except Exception as e:
                        print(e)
            except Exception as e:
                print(e)

    def spider(self):
        processed = 0
        while True:
            cursor = self.url_db.find(no_cursor_timeout=True).skip(processed)
            # with self.url_db.find(no_cursor_timeout=True) as cursor:

            try:
                for item in cursor:  # item type: dict
                    processed += 1
                    if self.check_repeat(item['name'], item['url']):
                        print('data replicated: ', item['name'])
                    else:
                        try:
                            page_url = item['url']
                            options = Options()
                            options.add_argument('--no-sandbox')
                            options.add_argument('--disable-dev-shm-usage')
                            options.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug
                            options.add_argument('--headless')  # 浏览器不提供可视化页面. linux下如果系统不支持可视化不加
                            # browser = webdriver.Chrome(chrome_options=options)
                            browser = webdriver.Chrome(options=options)
                            browser.get(page_url)

                            try:
                                browser.find_element_by_xpath("//span[@class='attrs']/a[@href='javascript:;']").get_attribute(
                                    'style')
                                if ~("display: none;" == browser.find_element_by_xpath(
                                        "//span[@class='attrs']/a[@href='javascript:;']").get_attribute('style')):
                                    browser.find_element_by_xpath("//span[@class='attrs']/a[@href='javascript:;']").click()
                                    self.sleep_time()
                            except selenium.common.exceptions.NoSuchElementException:
                                pass

                            # try:
                            #     browser.find_element_by_xpath(
                            #         "//div[@class='indent']/span[@class='short']").get_attribute('style')
                            #     if ~("display: none;" == browser.find_element_by_xpath(
                            #             "//div[@class='indent']/span[@class='short']")):
                            #         browser.find_element_by_xpath(
                            #             "//div[@class='indent']/span[@class='short']/a[@class='j a_show_full']").click()
                            # except selenium.common.exceptions.NoSuchElementException:
                            #     pass

                            _selenium_html = browser.execute_script("return document.documentElement.outerHTML")
                            _html = etree.HTML(_selenium_html)

                            # 名字
                            name = _html.xpath("//div[@id='content']/h1/span/text()")[0]

                            # url
                            url = page_url

                            # 图片码
                            image_src = _html.xpath("//div[@id='mainpic']/a/img/@src")[0]
                            image_rst = requests.get(url=image_src, headers=self.headers)
                            ls_f = base64.b64encode(BytesIO(image_rst.content).read())
                            image_code = base64.b64decode(ls_f)

                            # 导演 list
                            try:
                                browser.find_element_by_xpath("//span[@class='attrs']/a[@rel='v:directedBy']")
                                director = _html.xpath("//span[@class='attrs']/a[@rel='v:directedBy']/text()")
                            except selenium.common.exceptions.NoSuchElementException:
                                director = ''

                            # 编剧 list
                            try:
                                browser.find_elements_by_xpath(
                                    "//div[class='subjectwrap clearfix']/div[@id='info']/span/span[@class='pl'][contains(text(), 编剧)]")
                                scriptwriter_p = _html.xpath("//div[@id='info']/span[2]/span/a")
                                scriptwriters = []
                                for scriptwriter in scriptwriter_p:
                                    scriptwriters.append(scriptwriter.xpath('string(.)'))
                            except selenium.common.exceptions.NoSuchElementException:
                                scriptwriters = []

                            # 主演 list
                            actors_p = _html.xpath("//span[@class='actor']//span[@class='attrs']")
                            actors = []
                            for actor in actors_p:
                                actors.append(actor.xpath('string(.)'))
                            if len(actors) > 0:
                                actors = actors[0][:-5]

                            # 类型 list
                            types_p = _html.xpath("//div[@id='info']/span[@property='v:genre']")
                            types = []
                            for t in types_p:
                                types.append(t.xpath('string(.)'))

                            # 网站
                            try:
                                browser.find_element_by_xpath("//div[@id='info']/a")
                                website = _html.xpath("//div[@id='info']/a/@href")[0]
                            except selenium.common.exceptions.NoSuchElementException:
                                website = ''

                            # 制片国家
                            # 语言
                            # 别名
                            # IMDb
                            info = _html.xpath("//div[@id='info']/text()")
                            info_new = []

                            for i in info:
                                if ('\n' not in i) and i != ' / ' and i != ' ':
                                    info_new.append(i.strip())

                            location = info_new[0]
                            language = info_new[1]
                            if len(info_new) == 3:
                                if info_new[-1][:2].isalpha() and info_new[-1][2:].isdigit():
                                    other_name = ''
                                    IMDb = info_new[-1]
                                else:
                                    other_name = info_new[-1]
                                    IMDb = ''
                            elif len(info_new) == 2:
                                other_name = ''
                                IMDb = ''
                            else:
                                other_name = info_new[-2]
                                IMDb = info_new[-1]

                            # try:
                            #     language = info_new[1]
                            #     other_name = info_new[2]
                            # except IndexError:
                            #     language = ''
                            #     other_name = ''

                            # 上映时间 list
                            try:
                                browser.find_element_by_xpath("//div[@id='info']/span[@property='v:initialReleaseDate']")
                                release_time = _html.xpath("//div[@id='info']/span[@property='v:initialReleaseDate']/text()")
                            except selenium.common.exceptions.NoSuchElementException:
                                release_time = []

                            # 片长 str
                            try:
                                duration = _html.xpath("//div[@id='info']/span[@property='v:runtime']/text()")[0]
                            except IndexError:
                                duration = ''

                            # 评分 str
                            try:
                                score = _html.xpath("//div[@class='rating_self clearfix']/strong/text()")[0]
                            except IndexError:
                                score = ''

                            # 平台 platforms list
                            platforms_p = _html.xpath("//ul[@class='bs']/li")
                            platforms = []
                            for i in range(len(platforms_p)):
                                platforms.append(platforms_p[i].xpath("//li[" + str(i + 1) + "]/a/@data-cn")[0])

                            # 剧情简介
                            try:
                                intro = _html.xpath("//div//span[@property='v:summary']")[0].xpath('string(.)').replace(
                                    '\n', ' ').replace('  ', '').strip()
                            except IndexError:
                                intro = ''

                            update_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            item = {
                                "updateTime": update_time,
                                "name": name,
                                "url": url,
                                "image": image_code,
                                "director": director,
                                "scriptwriters": scriptwriters,
                                "actors": actors,
                                "type": types,
                                "website": website,
                                "location": location,
                                "IMDb": IMDb,
                                "language": language,
                                "otherName": other_name,
                                "releaseTime": release_time,
                                "duration": duration,
                                "score": score,
                                "platforms": platforms,
                                "introduction": intro
                            }
                            # if not self.check_repeat(name, url):
                            self.savedb(item)
                            print(item)
                            # else:
                            #     print('data replicated: ', name)
                        except Exception as e:
                            print(e, name, url)
                cursor.close()
                break
            except pymongo.errors.CursorNotFound:
                print("Lost cursor. Retry with skip")


if __name__ == '__main__':
    doubanmovie = doubanMovie()
    # doubanmovie.run()
    doubanmovie.spider()




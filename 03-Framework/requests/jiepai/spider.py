import re
import pymongo
import json

from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from urllib.parse import urlencode
from hashlib import md5 
import requests
from config import *
# from multiprocessing import 
from json.decoder import JSONDecodeError

client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_DB]

def get_page_index(offset, keyword):
     data = {
          'offset': offset,
          'format': 'json',
          'keyword': keyword,
          'autoload': 'true',
          'count': '20'
          'cur_tab': 1
          'from': 'search_tab'
     }
     url = 'http://www.toutiao.com/search_content/?' + urlencode(data)
     try:
          response = requests.get(url)
          if response.status_code == 200:
               return response.text
          return None
     except RequestException:
          print('请求索引页出错')
          return None

def parse_page_index(html):
     try:
          data = json.loads(html)
          if data and 'data' in data.keys():
               for item in data.get('data'):
                    yield item.get('article_url')
     except JSONDecodeError:
          pass

def get_page_detail(url):
     try:
          response = requests.get(url)
          if response.status_code == 200:
               return response.text
          return None
     except RequestException:
          print('请求详情页出错')
          return None

def parse parse_page_detail(html, url):
     soup = BeautifulSoup(html, 'lxml')
     title = soup.select('title')[0].get_text()
     # title = soup.title.string

     images_pattern = re.compile('var gallery = (.*?);', re.S)
     result = re.search(images_pattern, html)
     if result:
          data = json.loads(result.group(1))
          if data and 'sub_images' in data.keys():
               sub_images = data.get('sub_images')
               images = [item.get('url') for item in sub_images]
               
               for image in images:
                    download_image(image)

               return {
                    'title': title,
                    'url': url,
                    'image': images     
               }

def save_to_mongo(result):
     if db[MONGO_TABLE].insert(result):
          print('mongo save success', result)
          return True
     return False

def download_image(url):
     try:
          response = requests.get(url)
          if response.status_code == 200:
               #注：网页返回取.text，图片返回取.content
               save_image(response.content)
          return None
     except RequestException:
          print('请求图片出错')
          return None

def save_image(content):
     file_path = '{0}/{1}.{2}'.format(os.getcwd(), md5(content).hexdigest(), 'jpg')
     if not os.path.exists(file_path):
          with open(file_path, 'wb') as f:
               f.write(content)
               f.close()

def main(offset):
     html = get_page_index(0, KEYWORD)
     #print(html)
     for url in parse_page_index(html):
          #print(url)
          html = get_page_detail(url)
          if html:
               result = parse_page_detail(html)
               if result:
                    save_to_mongo(result)


if __name__ == '__main__':
     main()
     # groups = [x*20 for x in range(GROUP_START, GROUP_END+1)]
     # pool = Pool()
     # pool.map(main, groups)










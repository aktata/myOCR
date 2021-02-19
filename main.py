# coding=utf-8


import cv2
import csv
import os
import re
import sys
import json
import base64

# 保证兼容python2以及python3
import time
from typing import List

IS_PY3 = sys.version_info.major == 3
if IS_PY3:
    from urllib.request import urlopen
    from urllib.request import Request
    from urllib.error import URLError
    from urllib.parse import urlencode
    from urllib.parse import quote_plus
else:
    import urllib2
    from urllib import quote_plus
    from urllib2 import urlopen
    from urllib2 import Request
    from urllib2 import URLError
    from urllib import urlencode

# 防止https证书校验不正确
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

API_KEY = 'a43N0Gq8ukDUBKaIirec5wjH'

SECRET_KEY = 'eQRhNSINIQknSPASlM5wBQrSB47MT6a2'

OCR_URL = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic"

"""  TOKEN start """
TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token'

"""
    获取token
"""


def fetch_token():
    params = {'grant_type': 'client_credentials',
              'client_id': API_KEY,
              'client_secret': SECRET_KEY}
    post_data = urlencode(params)
    if (IS_PY3):
        post_data = post_data.encode('utf-8')
    req = Request(TOKEN_URL, post_data)
    try:
        f = urlopen(req, timeout=5)
        result_str = f.read()
    except URLError as err:
        print(err)
    if (IS_PY3):
        result_str = result_str.decode()

    result = json.loads(result_str)

    if ('access_token' in result.keys() and 'scope' in result.keys()):
        if not 'brain_all_scope' in result['scope'].split(' '):
            print('please ensure has check the  ability')
            exit()
        return result['access_token']
    else:
        print('please overwrite the correct API_KEY and SECRET_KEY')
        exit()


"""
    读取文件
"""


def read_file(image_path):
    f = None
    try:
        f = open(image_path, 'rb')
        return f.read()
    except:
        print('read image file fail')
        return None
    finally:
        if f:
            f.close()


"""
    调用远程服务
"""


def request(url, data):
    req = Request(url, data.encode('utf-8'))
    has_error = False
    try:
        f = urlopen(req)
        result_str = f.read()
        if (IS_PY3):
            result_str = result_str.decode()
        return result_str
    except  URLError as err:
        print(err)


"""
    内容匹配
"""


def match_text(txt, txt_start, txt_end, num, flag):
    if flag == 1:
        id_start = re.search(txt_start, txt).span()[1]
        id_end = re.search(txt_end, txt).span()[0]
        isname = txt[id_start:id_end]
    elif flag == 0:
        id_start = re.search(txt_start, txt).span()[1]
        isname = txt[id_start:id_start + num]
    else:
        print('ERROR:flag')
    return isname


"""
     创建文件夹
"""


def mkdir(mkpath):
    folder = os.path.exists(mkpath)
    if not folder:
        os.makedirs(mkpath)


if __name__ == '__main__':

    # 获取access token
    token = fetch_token()

    # 拼接通用文字识别高精度url
    image_url = OCR_URL + "?access_token=" + token

    text = ""

    # 读取书籍页面图片
    count = 0
    path = './img/'
    zip_path = './img_zip/'
    file_list: List = os.listdir(path)
    time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    row1 = [str(time)]
    row2 = ['姓名', '性别', '年龄', '身份证号', '联系电话', '科别', '申请医生']
    out = open("./result.csv", "a", newline="")
    csv_writer = csv.writer(out, dialect="excel")
    csv_writer.writerow(row1)
    csv_writer.writerow(row2)
    file_num = len([lists for lists in os.listdir(path) if os.path.isfile(os.path.join(path, lists))])
    mkdir(zip_path)
    print('共' + str(file_num) + '幅图像，正在识别：')
    while count < file_num:
        file_path = path + file_list[count]
        filezip_path = zip_path + file_list[count]
        print(file_list[count])
        count += 1

        # 压缩图像
        img = cv2.imread(file_path, 1)
        cv2.imwrite(filezip_path, img, [cv2.IMWRITE_JPEG_QUALITY, 50])

        # 调用文字识别服务
        file_content = read_file(filezip_path)
        result = request(image_url, urlencode({'image': base64.b64encode(file_content)}))
        os.remove(filezip_path)

        # 解析返回结果
        result_json = json.loads(result)
        for words_result in result_json["words_result"]:
            text = text + words_result["words"]
        name = match_text(txt=text, txt_start='姓名:', txt_end='性别', num=0, flag=1)
        gender = match_text(txt=text, txt_start='性别:', txt_end='', num=1, flag=0)
        age = match_text(txt=text, txt_start='年龄:', txt_end='岁身份证号', num=0, flag=1)
        idnum = match_text(txt=text, txt_start='身份证号', txt_end='', num=18, flag=0) + '\t'
        tel = match_text(txt=text, txt_start='联系电话', txt_end='', num=11, flag=0) + '\t'
        unit = match_text(txt=text, txt_start='科别:', txt_end='(申请单号|姓名)', num=0, flag=1)
        dr = match_text(txt=text, txt_start='申请医生:', txt_end='申请时间', num=0, flag=1)
        # print(text)
        text = ""
        # 写入csv文件
        row = [name, gender, age, idnum, tel, unit, dr]
        out = open("./result.csv", "a", newline="")
        csv_writer = csv.writer(out, dialect="excel")
        csv_writer.writerow(row)
    os.rmdir(zip_path)

# coding=utf-8

__author__ = 'Tacey Wong'

import os, sys, time, random
import urllib2
import zipfile
import re
import shutil
import sqlite3
import gl

try:
    import cStringIO as StringIO
except:
    import StringIO


class HttpTools:
    def __init__(self):
        self.head = {}
        self.head['User-Agent'] = random.choice(gl.USER_AGENT)
        # self.error = open(gl.ERROR_FILE, "a")

    def get_request(self, url):
        try:
            req = urllib2.Request(url, None, self.head)
        except Exception, e:
            print e
            return False
        return req

    def get_request_proxy(self, url):
        try:
            proxy_support = urllib2.ProxyHandler({'http': 'http://' + random.choice(gl.PROXY_IP)})
            opener = urllib2.build_opener(proxy_support, urllib2.HTTPHandler)
            urllib2.install_opener(opener)
            req = urllib2.Request(url, None, self.head)
            return req
        except Exception, e:
            print e
            return self.get_request(url)

    def get_html(self, url):
        req = self.get_request(url)
        if req:
            try:
                res = urllib2.urlopen(req, timeout=10)
                content = res.read()
                return content
            except Exception, e:
                print e
                return False
        return False

    def get_pic(self, imgurl,img_dir):
        print imgurl
        req = self.get_request(imgurl)
        if req:
            try:
                res = urllib2.urlopen(req, timeout=10)
                content = res.read()
                picname = img_dir+os.sep+imgurl.replace('/','_')
                with open(picname, 'wb') as f:
                    f.write(content)
                print "write success!", imgurl
                return True
            except Exception, e:
                print e
                return False
        return False

    def __del__(self):
        # self.error.close()
        pass

class CrawPics:
    def __init__(self):

        self.httptool = HttpTools()
        # aliexpress
        self.aliexpress_image_re = re.compile(r'window.runParams.imageBigViewURL=\[\s?(?P<image_list>.*?)\s?\]', re.S)
        self.aliexpress_detail_page_re = re.compile(r'window.runParams.descUrl="(.*?)"', re.S)
        self.aliexpress_detail_img_re = re.compile(r'img.*?src="(.*?)"')

        # amzone(无详情页面)
        self.amazon_image_json_re = re.compile(r"'colorImages'.*?:(.*?)'colorToAsin'", re.S)
        self.amazon_image_re = re.compile(r'"large":"(.*?)",', re.S)

        # ebay(详情页面模板不统一，不保证详情页面的图片能抓取下来)
        self.ebay_image_re = re.compile(r'"maxImageUrl":"(.*?)"', re.S)
        self.ebay_detail_page_re = re.compile(r'<div id="desc_div".*?src="(.*?)"',re.S)
        self.ebay_detail_image_re_1 = re.compile(r'<img onload.*?src="(.*?)"')
        self.ebay_detail_image_re_2 = re.compile(r'img.*?src="(.*?)"')

        # 1688
        self.alibaba_image_re = re.compile(r'"original":"(.*?)"', re.S)
        self.alibaba_detail_page_re = re.compile(r'data-tfs-url="(.*?)"', re.S)
        self.alibaba_detail_img_re = re.compile(r'src.*?"(.*?)\\')



    def filter_img_url(self,imgurl):
        if imgurl.endswith('.gif'):
            return False
        return True

    def get_pics(self,item_url,platform,filename,MAIN_PICS,DETAIL_PICS):
        # 尽量将颗粒度降低防止,以损失速度的代价求稳定
        # main_pics =[]
        # detail_pics = []

        item_co = self.httptool.get_html(item_url)
        if platform == 'amazon':
            for imgurl in self.amazon_image_re.findall(self.amazon_image_json_re.findall(item_co)[0]):
                self.httptool.get_pic(imgurl,filename+os.sep+'MAIN_PICS')

        elif platform == '1688':
            for imgurl in list(set(self.alibaba_image_re.findall(item_co))):
                    self.httptool.get_pic(imgurl,MAIN_PICS)
            for detail_page in list(set(self.alibaba_detail_page_re.findall(item_co))):
                detail_data = urllib2.urlopen(detail_page).read()
                for imgurl in list(set(self.alibaba_detail_img_re.findall(detail_data))):
                    if self.filter_img_url(imgurl):
                        self.httptool.get_pic(imgurl,DETAIL_PICS)
        elif platform == 'ebay':
            for imgurl in list(set(self.ebay_image_re.findall(item_co))):
                self.httptool.get_pic(imgurl.replace('\u002F','/'),MAIN_PICS)
            for detail_page in list(set(self.ebay_detail_page_re.findall(item_co))):
                detail_data = urllib2.urlopen(detail_page).read()
                for imgurl in self.ebay_detail_image_re_1.findall(detail_data):
                    self.httptool.get_pic(imgurl,DETAIL_PICS)
                for imgurl in self.ebay_detail_image_re_2.findall(detail_data):
                    self.httptool.get_pic(imgurl,DETAIL_PICS)
                # detail_tmp = list(set(detail_tmp))
                # detail_pics.extend(filter(self.filter_img_url,detail_tmp ))


        elif platform == 'aliexpress':
            for imgurl_list in list(set(self.aliexpress_image_re.findall(item_co))):
                for imgurl in imgurl_list.replace('"','').strip().split(',\n'):
                    self.httptool.get_pic(imgurl.strip('"'),MAIN_PICS)

            for detail_page in list(set(self.aliexpress_detail_page_re.findall(item_co))):
                detail_data = urllib2.urlopen('http:'+detail_page).read()
                for imgurl in list(set(self.aliexpress_detail_img_re.findall(detail_data))):
                    if self.filter_img_url(imgurl):
                        self.httptool.get_pic(imgurl,DETAIL_PICS)
        else:
            print 'Un-Konwn-platform'

        # self.httptool.get_pic(main_pics,gl.MAIN_PIC_DIR)
        # self.httptool.get_pic(detail_pics,DETAIL_PICS)



    def check_path(self,filename):
        print "check path ..."
        MAIN_PICS = gl.BASE_PATH+os.sep+filename+os.sep+'MAIN_PICS'
        DETAIL_PICS = gl.BASE_PATH+os.sep+filename+os.sep+'DETAIL_PICS'
        if not os.path.exists(gl.BASE_PATH):
            os.mkdir(gl.BASE_PATH)
        if not os.path.exists(MAIN_PICS):
            os.mkdir(MAIN_PICS)
        if not os.path.exists(DETAIL_PICS):
            os.mkdir(DETAIL_PICS)

    def zip_dir(self, dirname, zipfilename):
        print 'zip dir ...'
        filelist = []
        if os.path.isfile(dirname):
            filelist.append(dirname)
        else:
            for root, dirs, files in os.walk(dirname):
                for name in files:
                    filelist.append(os.path.join(root, name))
        zf = zipfile.ZipFile(zipfilename, "w", zipfile.zlib.DEFLATED)
        for tar in filelist:
            arcname = tar[len(dirname):]
            zf.write(tar, arcname)
        zf.close()

    def rm_dir(self, dirname, rm_root_file=False):
        for i in os.listdir(gl.BASE_PATH):
            tmp_path = os.path.join(gl.BASE_PATH, i)
            if os.path.isdir(tmp_path):
                try:
                    shutil.rmtree(tmp_path)
                    if rm_root_file:
                        os.remove(tmp_path)
                except Exception, e:
                    print e

    def rec_platform(self,item_url):
        if 'ebay.com' in item_url:
            return 'ebay',item_url
        elif '1688.com' in item_url:
            return '1688',item_url
        elif 'amazon.com' in item_url:
            return 'amazon',item_url
        elif 'aliexpress.com' in item_url:
            return 'aliexpress',item_url

    def __del__(self):
        self.zip_dir(gl.BASE_PATH,'test.zip')
        # self.rm_dir(gl.BASE_PATH)

    def __unicode__(self):
        return 'worker place-hold'


#
#
# def get_pic_url(item_url):
#     #aliexpress big pic
#     image_list_re = re.compile(r'window.runParams.imageBigViewURL=\[\s?(?P<image_list>.*?)\s?\]', re.S)
#     detail_page_re = re.compile(r'window.runParams.descUrl="(.*?)"',re.S)
#     for i in list(set(detail_page_re.findall(co))):
#         detail_data = urllib2.urlopen('http:'+i).read()
#         detail_re = re.compile(r'img.*?src="(.*?)"')
#         for j in list(set(detail_re.findall(detail_data))):
#           print j
#     #amzone big pic
#     pic_dic_re = re.compile(r"'colorImages'.*?:(.*?)'colorToAsin'" , re.S)
#     pic_list_re = re.compile(r'"large":"(.*?)",',re.S)
#     for i in pic_list_re.findall(pic_dic_re.findall(co)[0]):
#     print i
#     #ebay
#     piclist_re = re.compile(r'"maxImageUrl":"(.*?)"',re.S)
#     for i in list(set(piclist_re.findall(co))):
#         print i.replace('\u002F','/')
#
#     detail_page_re = re.compile(r'<div id="desc_div".*?src="(.*?)"',re.S)
#
#     for i in list(set(detail_page_re.findall(co))):
#         print '-++++++++++++++++++'
#         print i
#         detail_data = urllib2.urlopen(i).read()
#         # print detail_data
#         detail_re = re.compile(r'<img onload.*?src="(.*?)"')
#         for j in list(set(detail_re.findall(detail_data))):
#             print j
#         detail_re = re.compile(r'img.*?src="(.*?)"')
#         for j in list(set(detail_re.findall(detail_data))):
#             print j
#
#
#
#     #1688
#     piclist_re = re.compile(r'"original":"(.*?)"',re.S)
#     for i in list(set(piclist_re.findall(co))):
#         print i
#     detail_page_re = re.compile(r'data-tfs-url="(.*?)"',re.S)
#     for i in list(set(detail_page_re.findall(co))):
#         detail_data = urllib2.urlopen(i).read()
#         detail_re = re.compile(r'src.*?"(.*?)\\')
#         for j in list(set(detail_re.findall(detail_data))):
#             print j
#     pass


def rake():
    p = CrawPics()
    db = sqlite3.connect(gl.DATABASE)
    db.row_factory = sqlite3.Row
    urls=None
    while True:
        cur_job = db.execute('select jobname from job where  status IS NULL LIMIT 1')
        result = cur_job.fetchall()
        if len(result) > 0:
            jobname = result[0][0]
            cur_detail = db.execute("select itemurl from detail where jobname='%s'" % jobname)
            result = cur_detail.fetchall()
            if len(result) > 0:
                for url in [item[0] for item in result]:
                    plt,url = p.rec_platform(url)
                    p.get_pics(url,plt,jobname)
                    print '============================================================'


if __name__ == "__main__":

    item_urls = ['https://detail.1688.com/offer/40569258682.html?spm=a26qs.7705462.1998520159.1.xaXnlB',
                 'http://www.ebay.com/itm/401017868422',
                 'https://www.amazon.com/dp/B00XJGCC4O',
                 'http://www.aliexpress.com/item/Bathroom-Square-Digital-Clock-With-Temperature-and-Humidity-for-Wall-Mounting-or-Table-Standing/32390019916.html?spm=2114.01010108.3.11.FCW9xq&ws_ab_test=searchweb201556_8,searchweb201602_1_10049_10017_405_404_407_406_10040,searchweb201603_1&btsid=87058d8e-e042-48a6-a4ac-82c133b51e42'
                 ]
    rake(item_urls)




    # p = CrawPics()
    # p.check_path(gl.BASE_PATH)
    # for i in range(10):
    #     dir_name = time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime(time.time())) + '-' + str(random.randint(0, 1000))
    #     os.mkdir(gl.BASE_PATH + os.sep + dir_name)
    # for i in os.listdir(gl.BASE_PATH):
    #     tmp_path = os.path.join(gl.BASE_PATH, i)
    #     if os.path.isdir(tmp_path):
    #         try:
    #             shutil.rmtree(tmp_path)
    #         except:
    #             print e
    #
    # p.zip_dir('tmp', 'zip.zip')
    # import shutil
    # shutil.rmtree('tmp')
    # check_path(BASE_PATH)
    # dir_name = time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(time.time()))
    # os.mkdir(BASE_PATH+os.sep+dir_name)
    item_urls = ['https://detail.1688.com/offer/40569258682.html?spm=a26qs.7705462.1998520159.1.xaXnlB',
                 # 'http://www.ebay.com/itm/401017868422',
                 # 'https://www.amazon.com/dp/B00XJGCC4O',
                 'http://www.aliexpress.com/item/Bathroom-Square-Digital-Clock-With-Temperature-and-Humidity-for-Wall-Mounting-or-Table-Standing/32390019916.html?spm=2114.01010108.3.11.FCW9xq&ws_ab_test=searchweb201556_8,searchweb201602_1_10049_10017_405_404_407_406_10040,searchweb201603_1&btsid=87058d8e-e042-48a6-a4ac-82c133b51e42'
                 ]
    # for platform , url in rec_platform(item_urls):
    #     print platform , url


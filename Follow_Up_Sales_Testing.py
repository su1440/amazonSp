

'''
基本功能：
1.跟卖检测
    数据集：  店铺seller_id_list

    输出:
        被跟卖店铺 id
        被跟卖店铺 name
        被跟卖产品 asin 存在多个被跟卖产品
        返回数据结构
        {
            id:value
            name:value
            asin:[]
        }

    跟卖检测方式:
        获取店铺全部商品asin
        [
            {
                store_id:value
                follow_up_sales_asin:[]
            },
            {
                store_id:value
                follow_up_sales_asin:[]
            }
        ]
        进入asin主页面  ->   检查购物车是否存在其他卖家（包括卖家数量）

方式 ： selenium + requests   效率不够呀害，以后考虑多线程解决效率问题，目标一个店铺一个线程
     店铺多了内存不够，固定30个线程
'''
import time

from selenium import webdriver
import requests
import pymysql
from lxml import etree


def get_store_asin(store_id):
    """
    params: store_id  商店id
    return: store_asin 店铺的id 和 全部asin  字典形式
    {
        store_id:[asin,asin]
    }
    """
    # webdriver驱动
    driver = webdriver.Chrome()
    # 商店链接
    store_url = 'https://www.amazon.com/sp?seller=' + str(store_id)
    # 打开页面调整地区
    driver.get('https://www.amazon.com')
    # 调整地区至美国
    time.sleep(1.5)
    driver.find_element_by_id('nav-global-location-popover-link').click()
    time.sleep(1.5)
    driver.find_element_by_id('GLUXZipUpdateInput').send_keys('10001')
    driver.find_element_by_xpath('//input[@aria-labelledby="GLUXZipUpdate-announce"]').click()
    time.sleep(1)
    driver.find_element_by_xpath('//div[@class="a-popover-footer"]/span/span/input').click()

    # 打开商店商品界面
    time.sleep(1)
    driver.get(store_url)
    time.sleep(1)
    html = driver.page_source
    html_etree = etree.HTML(html)
    store_front_url = 'https:www.amazon.com'+html_etree.xpath('//div[@id="storefront-link"]/a/@href')[0]
    driver.get(store_front_url)

    page_asin_list = []
    try:
        while True:
            # 获取商品信息
            html = driver.page_source
            html_etree = etree.HTML(html)
            temp = html_etree.xpath(
                '//div[@class="s-desktop-width-max s-opposite-dir"]/div/div/div/span/div[2]/div/@data-asin')
            page_asin_list.extend(temp)
            next_url = 'https://www.amazon.com'+html_etree.xpath('//li[@class="a-last"]/a/@href')[0]
            driver.get(next_url)


    except:
        driver.close()
        while '' in page_asin_list:
            page_asin_list.remove('')
        store_asin = {
            store_id:page_asin_list
        }
        return store_asin


if __name__=="__main__":
    store_id = ['A1V1A8MPUOFP13', 'A39AZGBM0D7NTR', 'A2VPDYV4EYVY61']
    for x in store_id:
        t = get_store_asin(x)
        print(t)
import time
from lxml import etree
from selenium import webdriver
from pymysql import *
import xlwt

'''
pymysql   1.0.1
jsonpath   0.8
lxml    4.6.3
requests   2.10.0
selenium    3.141
xlwt     1.3
'''

# 获取商店所有的ASIN  返回值为商店的asin列表  参数为店铺的url
def from_store_url_get_all_product_asin(st_url):
    '''
    返回该店铺所有商品的asin

    返回所有商品的Asin
    '''
    driver = webdriver.Chrome()

    store_url = st_url
    # 进入主界面
    driver.get(store_url)

    # 1.更换地区
    driver.find_element_by_id('nav-global-location-popover-link').click()
    time.sleep(3)
    driver.find_element_by_id('GLUXZipUpdateInput').send_keys('10001')
    driver.find_element_by_xpath("//div[@id='GLUXZipInputSection']//input[@class='a-button-input']").click()
    time.sleep(3)
    driver.find_elements_by_class_name('a-button-input')[3].click()
    # 2.进入商店页面store_front 页面
    html = etree.HTML(driver.page_source)
    # store_front_url  是商店首页id
    store_front_url = 'https://www.amazon.com' + \
                      html.xpath("//div[@id='storefront-link']/a[@class='a-link-normal']/@href")[
                          0].replace('/-', '').replace(' ', '').replace('/zh', '')

    # driver.get(store_front_url)
    # 获取数据  该页面中展示的所有产品的链接

    all_item_asin = []

    driver.get(store_front_url)

    html = driver.page_source

    item_asin = etree.HTML(html).xpath(
        "//div[@class='s-desktop-width-max s-opposite-dir']//span[@class='rush-component s-latency-cf-section']/div[2]/div/@data-asin")

    all_item_asin.extend(item_asin)

    # print(all_item_asin)
    # 保存链接用于返回该页面   # 注意有的店铺商品只有一页   待解决
    try:
        next_button_class_name = etree.HTML(html).xpath("//div[@class='a-text-center']//li[last()]/@class")[0]

        # test 代码
        str = etree.HTML(html).xpath("//div[@class='a-text-center']/ul/li[last()]/a/@href")
        # print(str)

        while next_button_class_name == 'a-last':
            next_page_url = 'https://www.amazon.com' + \
                            etree.HTML(html).xpath("//div[@class='a-text-center']/ul/li[last()]/a/@href")[0].replace(
                                '/-',
                                '').replace(
                                ' ', '').replace('/zh', '')

            driver.get(next_page_url)

            html = driver.page_source

            item_asin = etree.HTML(html).xpath(
                "//div[@class='s-desktop-width-max s-opposite-dir']//span[@class='rush-component s-latency-cf-section']/div[2]/div/@data-asin")

            all_item_asin.extend(item_asin)

            next_button_class_name = etree.HTML(html).xpath("//div[@class='a-text-center']//li[last()]/@class")[0]
    except:
        pass
    # 1.获取当前页面数据  -> 商品独立页面链接

    while '' in all_item_asin:
        all_item_asin.remove('')
    driver.quit()

    return all_item_asin


# 获取商品信息  包含 name,asin，price，链接
def get_asin_info(asin_list):
    driver = webdriver.Chrome()
    # 界面地址设置
    # 初始设置，设置送货地址
    amazon_front_page_url = 'https://www.amazon.com'
    driver.get(amazon_front_page_url)
    driver.find_element_by_id('nav-global-location-popover-link').click()
    time.sleep(1)
    driver.find_element_by_id('GLUXZipUpdateInput').send_keys('10001')
    driver.find_element_by_xpath("//div[@id='GLUXZipInputSection']//input[@class='a-button-input']").click()
    time.sleep(1)
    driver.find_elements_by_class_name('a-button-input')[4].click()
    time.sleep(2)
    # 注意休眠2秒  程序点击确定后会自动产生跳转，如果没有等待会导致第一次页面
    # 进入调用失效

    # 处理asin 转换为产品链接    方式 ：  https://www.amazon.com/dp/ + asin
    asin_list_url = []  # 保存所有商品的直接链接
    for x in asin_list:
        temp = 'https://www.amazon.com/dp/' + str(x)
        asin_list_url.append(temp)

    # 通过链接 进入商品独立页面 获取信息 ： asin,name,price,link ,f_time
    # 创建列表保存信息
    asin_info = []

    for x in asin_list_url:
        driver.get(x)
        html = driver.page_source  # 获取当前网页源码
        html_etree = etree.HTML(html)  # 用etree处理，并查找数据
        name = html_etree.xpath("//span[@id='productTitle']/text()")[0].replace(' ', '').replace('\n', '')
        price = html_etree.xpath("//span[@id='priceblock_ourprice']/text()")[0].replace('$', '')
        # 用于保存商品信息的临时字典
        asin_dict = {
            'asin': x.replace('https://www.amazon.com/dp/', ''),
            'name': name,
            'price': float(price),
            'link': x,
            'f_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }

        asin_info.append(asin_dict)

    driver.quit()
    return asin_info


# 清理测试数据
def clear_datebase():
    # 清理测试数据
    conn = connect(host='localhost', port=3306, database='amazon', user='root', password='123456', charset='utf8')
    cs1 = conn.cursor()
    sql1 = 'drop table asin_a3oqfkfxqw7ibq;'
    sql2 = 'drop table asin_a8wy6mnqhoru3;'
    cs1.execute(sql1)
    cs1.execute(sql2)
    conn.commit()
    cs1.close()
    conn.close()


# 返回商店与产品asin数据   参数为列表 : 保存数据为所有的店铺id
def return_all_store_asin(store_id_list):
    """
    返回数据格式：
    [
        { store_id:[asin,asin,asin] },
        {}
    ]
    """
    all_store_asin_list = []
    store_url_list = []
    # 处理store_id_list 转换为实际店铺链接
    for x in store_id_list:
        url = 'https://www.amazon.com/sp?seller=' + str(x)
        store_url_list.append(url)

    for st_url in store_url_list:
        store_asin_list = from_store_url_get_all_product_asin(st_url)
        store_asin = {
            st_url.replace('https://www.amazon.com/sp?seller=', ''): store_asin_list
        }
        all_store_asin_list.append(store_asin)

    return all_store_asin_list


# #######################
# 数据库操作部分

# 根据商家id列表，在数据库中创建相应的数据库  -> 可用于添加数据表
def create_database(id_list):
    # 获取数据库中店铺列表
    conn = connect(host='localhost', port=3306, database='amazon', user='root', password='123456', charset='utf8')
    cs1 = conn.cursor()
    sql_get_store = 'select * from store_id_all'
    cs1.execute(sql_get_store)
    store_id_list = cs1.fetchall()
    store_id_all = []  # 保存所有获取到的 数据库中的店铺id
    for x in store_id_list:
        store_id_all.append(x[1])
    #  id,  asin，store_id,add_time
    for x in id_list:
        if x not in store_id_all:
            # 创建添加数据表的SQL语句
            sql = """
            create table """ + 'asin_' + x + """(
            id int unsigned not null auto_increment primary key,
            asin varchar(30) not null,
            store_id varchar(30) not null,
            add_time datetime); 
            """
            # 用于将商店id添加到总店铺表的SQL语句

            sql1 = """insert into store_id_all values(default,'""" + str(x) + """');"""
            cs1.execute(sql)
            cs1.execute(sql1)
            conn.commit()
    cs1.close()
    conn.close()
    # for x in id_list:


# 保存所有不存在asin_all表中的的asin
def save_all_asin(store_id_list):
    conn = connect(host='localhost', port=3306, database='amazon', charset='utf8', password='123456', user='root')
    cs1 = conn.cursor()
    sql_select_asin = 'select asin from asin_all;'
    cs1.execute(sql_select_asin)
    res = cs1.fetchall()  # 数据格式 (('testtesttest',), ('testtesttest0',), ('testtesttest1',)) 元组
    asin_all_list = []  # 数据库中所有的asin
    for x in res:
        asin_all_list.append(x[0])


#######################################################################@@@@@@@@
# 精简核心功能  获取所有商店的全部asin   找出新asin
def get_all_asin(store_id_list):
    '''
    参数  商店id列表
    返回值： 所有的asin
    '''
    asin_all = []
    for x in store_id_list:
        url = "https://www.amazon.com/sp?seller=" + str(x)
        temp = from_store_url_get_all_product_asin(url)  # asin 列表
        asin_all.extend(temp)  # 扩展保存到总asin列表中

    return asin_all


def save_all_asin_new(asin_list):
    '''
    参数： asin列表
    # 返回值 新asin列表
    '''
    # 获取数据中已经存在的asin列表    database_all_asin
    conn = connect(host='localhost', port=3306, user='root', password='123456', database='amazon', charset='utf8')
    cs1 = conn.cursor()
    sql_get_asin = 'select asin from asin_all;'
    cs1.execute(sql_get_asin)
    temp = cs1.fetchall()
    database_all_asin = []
    for x in temp:
        database_all_asin.append(x[0])

    # 对比新get到的list 与 数据中的asin  获取新asin
    new_asin = []
    for x in asin_list:
        if x not in database_all_asin:
            new_asin.append(x)

    # 新asin 添加到   asin_all 与asin_new中

    # 1. 清空asin_new数据
    sql_clear = 'delete from asin_new where id>1;'
    cs1.execute(sql_clear)
    conn.commit()
    # 生成sql语句
    add_asin_all_sql = []
    add_asin_new_sql = []
    for asin in new_asin:
        sql = "insert into asin_all values(default,'" + asin + "');"
        add_asin_all_sql.append(sql)
    for asin in new_asin:
        sql = "insert into asin_new values(0,'" + asin + "');"
        add_asin_new_sql.append(sql)
    # 执行sql语句
    for add_all, add_new in zip(add_asin_all_sql, add_asin_new_sql):
        cs1.execute(add_all)
        cs1.execute(add_new)

    conn.commit()

    cs1.close()
    conn.close()

    return new_asin


def asin_to_url(asin):
    url = "https://www.amazon.com/dp/"+str(asin)
    return url


def list_to_excel(url_list):
    # # 准备数据
    #
    # # 创建数据表
    book = xlwt.Workbook(encoding='utf-8', style_compression=0)
    sheet = book.add_sheet("店铺新品", cell_overwrite_ok=True)
    sheet.write(0, 0, '商品ASIN')
    sheet.write(0, 1, '商品链接')
    #
    # # 写入数据
    row = 1
    for url in url_list:
        temp = url
        asin = temp.replace('https://www.amazon.com/dp/', '')
        sheet.write(row, 0, asin)
        sheet.write(row, 1, url)
        row += 1

    book_name = time.strftime('%Y_%m_%d_%H_%M_%S_') + '新ASIN' + '.xls'
    book.save(book_name)

def main():
    # 此处的id需要进一步通过代码筛选url地址实现
    store_id_list = []
    # 林楠的店铺
    store_id_list_linnan = [
        'A1V1A8MPUOFP13', 'A39AZGBM0D7NTR', 'A2VPDYV4EYVY61', 'A26GYFXRRJA2CD', 'A1PKP3SUK162Y9', 'A1ED5NV5ZS8OQM',
        'A3DYQZS8QZ0FFN',
        'A1W2QX68YCMKMT', 'A3QQ4PBYAY33ZR', 'A1XJJODCH2N15I', 'A2MNTJ7P6H8X5S', 'AL1VJ4GXCWVQ9', 'A3SNNHVCPVNMJH',
        'A2GO6R9NWTN6AG',
        'A3P1RFS4CYSNJB', 'A5FSGLKI1JWPQ', 'A2ZGAF69EJTMW8', 'A1JJV1UININWPH', 'A8WY6MNQHORU3', 'A2XANU519V281U',
        'A2UDQBT1EV0GNM'
    ]

    asin_list = get_all_asin(store_id_list_linnan)
    new_asin_list = save_all_asin_new(asin_list)
    print(new_asin_list)
    url_list = []
    for asin in new_asin_list:
        url = asin_to_url(asin)
        url_list.append(url)
    list_to_excel(url_list)

if __name__ == "__main__":
    # 商店主页url  组成为： https://www.amazon.com/sp?seller=  +  商家的id
    # url = 'https://www.amazon.com/sp?seller=A8WY6MNQHORU3'
    #
    # # print(from_store_url_get_all_product_asin(url))
    #
    # # 用于测试的 asin列表
    # asin_list = ['B091TG2LVT', 'B09247CJXY', 'B091ZC93ZK', 'B091TYTFXY', 'B091CC8R31', 'B09245PYXH', 'B092J9BWDT',
    #              'B08LGZ8N7G', 'B08ZSXK5ZJ', 'B091Q4CL42', 'B091DX3ZG2', 'B08LL96BB4', 'B08ZXMPR3W', 'B08M5P9BDB',]
    # asin_list1 = ['B07T2HX7QC','B00CYN67QM']
    # # # get_asin_info(asin_list)
    # id_list = ['A8WY6MNQHORU3', 'A3OQFKFXQW7IBQ']
    # # # create_database(id_list)
    # # # clear_datebase()
    # # a = return_all_store_asin(id_list)
    # # print(a)
    #
    # # print(save_all_asin())
    # # temp = get_all_asin(id_list)
    # # print(temp)
    # temp1 = save_all_asin_new(asin_list1)
    # print('*'*50)
    # print(temp1)
    # store_id_list = ['A8WY6MNQHORU3','A2XANU519V281U','A2UDQBT1EV0GNM']
    store_id_list_linnan = [
        'A1V1A8MPUOFP13', 'A39AZGBM0D7NTR', 'A2VPDYV4EYVY61', 'A26GYFXRRJA2CD', 'A1PKP3SUK162Y9', 'A1ED5NV5ZS8OQM',
        'A3DYQZS8QZ0FFN',
        'A1W2QX68YCMKMT', 'A3QQ4PBYAY33ZR', 'A1XJJODCH2N15I', 'A2MNTJ7P6H8X5S', 'AL1VJ4GXCWVQ9', 'A3SNNHVCPVNMJH',
        'A2GO6R9NWTN6AG',
        'A3P1RFS4CYSNJB', 'A5FSGLKI1JWPQ', 'A2ZGAF69EJTMW8', 'A1JJV1UININWPH'
    ]
    main()

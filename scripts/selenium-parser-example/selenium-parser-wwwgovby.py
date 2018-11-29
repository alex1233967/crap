#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import re
import csv
import datetime
import requests
from lxml import etree, html
from selenium import webdriver
from urllib.parse import quote
from optparse import OptionParser
from html.parser import HTMLParser
from selenium.webdriver.common.by import By
from html_table_parser import HTMLTableParser
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC


scheme = 'https://'
domain = 'www.portal.gov.by'
path = '/PortalGovBy/faces/oracle/webcenter/portalapp/pagehierarchy/Page15.jspx'
PAGELOAD_TIMEOUT = 10


def request(driver):
    s = requests.Session()
    cookies = driver.get_cookies()
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])
    return s


def parse_xml(xml, fragment):
    # xml header is not supported in etree.fromstring
    xml = re.sub(r'<\?xml.*?\?>\n?', '', xml)

    root = etree.fromstring(xml)
    root = root.findall(fragment)

    table = root[0].text
    p = HTMLTableParser()
    p.feed(table)

    header = p.tables[0][1]
    rows = p.tables[1]

    return (header, rows)


def saveto_csv(header, rows, fn):
    write_header = False if os.path.isfile(fn) else True

    with open(fn, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        if write_header:
            writer.writerow(header)

        for row in rows:
            writer.writerow(row)


def main():
    # parse options
    parser = OptionParser(usage='usage: %prog [options]')
    parser.add_option('--proxy',
                      action='store_true',
                      dest='proxy',
                      default=False,
                      help='route requests via 127.0.0.1:8080')
    parser.add_option('-s',
                      action='store',
                      dest='search_for',
                      default=None,
                      help='domain name to search')
    parser.add_option('-d',
                      action='store',
                      dest='chrome_driver',
                      default='chromedriver',
                      help=('chrome driver path [default: chromedriver] '
                            'see http://chromedriver.chromium.org/downloads'))
    (options, args) = parser.parse_args()

    if options.search_for:
        search_for = options.search_for
    else:
        print('wrong arguments:\n')
        parser.print_help()
        exit()

    if options.chrome_driver:
        chrome_driver = options.chrome_driver

    # for debugging purposes
    if options.proxy:
        proxies = {
            'http': '127.0.0.1:8080',
            'https': '127.0.0.1:8080'
        }
    else:
        proxies = {}

    # start
    driver = webdriver.Chrome('./' + chrome_driver)

    # open page in browser
    driver.get(scheme + domain + path)
    assert 'Получение сведений из торгового реестра' in driver.title

    # get search form location from page source
    form_location = re.search(r'element.src = "([^"]+)',
                              driver.page_source).group(1)
    form_location = HTMLParser().unescape(form_location)

    driver.get(form_location)

    # wait for page load and go to search tab
    # on small resolution screens overflow indicator must be clicked first
    try:
        WebDriverWait(driver, PAGELOAD_TIMEOUT).until(
            EC.element_to_be_clickable((By.XPATH,
                                        '//*[@id="_jpfcpncuivr___ns1724898665__j_id_id0:r1:0:pt1::tabh::eoi"]'))
        ).click()
    except NoSuchElementException:
        WebDriverWait(driver, PAGELOAD_TIMEOUT).until(
            EC.element_to_be_clickable((By.LINK_TEXT,
                                        'Поиск по доменному имени'))
        ).click()
    else:
        WebDriverWait(driver, PAGELOAD_TIMEOUT).until(
            EC.element_to_be_clickable((By.LINK_TEXT,
                                        'Поиск по доменному имени'))
        ).click()

    # submit search form
    try:
        WebDriverWait(driver, PAGELOAD_TIMEOUT).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                                        'input.af_inputText_content'))
        )
    finally:
        # TODO get rid of next line
        __import__('time').sleep(2)
        search_form = driver.find_element_by_css_selector('input.af_inputText_content')
        search_form.send_keys(search_for)
        search_form.send_keys(Keys.RETURN)

    # wait for page load (search button disappears)
    try:
        WebDriverWait(driver, PAGELOAD_TIMEOUT).until(
            EC.invisibility_of_element((By.XPATH, 
                                        '//button[text()="Выполнить поиск"]'))
        )
    except TimeoutException:
        print('[*] Nothing found. Exiting...')
        driver.quit()
        quit()

    # parsing page source
    tree = html.fromstring(driver.page_source)

    try:
        pages_total = tree.cssselect('td.af_table_navbar-row-range-text')[1].text
        pages_total = int(re.search(r'\d+', pages_total).group(0))
    except Exception:
        pages_total = 1

    _adfcustompprurlexpando = re.search(r'_adfcustompprurlexpando="([^"]+)',
                                        driver.page_source).group(1)

    viewstate = re.search(r'name="javax.faces.ViewState".+?value="([^"]+)',
                          driver.page_source).group(1)

    form_name = tree.cssselect('form.af_form')[0].get('name')
    form = form_name.split(':')[0]

    # starting python requests...
    print('[*] Sending automated requests...')

    # disable insecure cert warnings
    requests.packages.urllib3.disable_warnings() 

    req = request(driver)

    headers = {
        'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/70.0.3538.77 Safari/537.36'),
        'Referer': form_location,
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Adf-Rich-Message': 'true'
    }

    filename = '{}_{}_{}.csv'.format(search_for, domain, datetime.date.today())

    start = 0
    end = 24
    for i in range(pages_total):
        params = (
            'org.apache.myfaces.trinidad.faces.FORM=' + quote(form_name) + '&'
            'javax.faces.ViewState=' + viewstate + '&'
            'oracle.adf.view.rich.RENDER=' + quote(form + ':r1:1:t1') + '&'
            'oracle.adf.view.rich.DELTAS=' + quote('{' + form + ':r1:1:t1={viewportSize=26,first|p=25}}') + '&'
            'event=' + quote(form + ':r1:1:t1') + '&'
            # this param is also vulnerable to xxe :)
            'event.' + form + ':r1:1:t1=' + quote(('<m xmlns="http://oracle.com/richClient/comm">'
                                                   '<k v="oldStart"><s>0</s></k>'
                                                   '<k v="oldEnd"><s>24</s></k>'
                                                   '<k v="newStart"><s>' + str(start) + '</s></k>'
                                                   '<k v="newEnd"><s>' + str(end) + '</s></k>'
                                                   '<k v="type"><s>rangeChange</s></k></m>')) + '&'
            'oracle.adf.view.rich.PROCESS=' + quote(form + ':r1:1:t1')
        )

        resp = req.post(_adfcustompprurlexpando,
                        verify=False,
                        data=params,
                        headers=headers,
                        proxies=proxies)

        print('[+] Parsing {} out of {} pages'.format(i + 1, pages_total))
        header, rows = parse_xml(resp.text, 'fragment')
        saveto_csv(header, rows, filename)
        start += 25
        end += 25

    driver.quit()
    print('[*] Saved to: ' + filename)


if __name__ == '__main__':
    main()

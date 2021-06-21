#!/usr/bin/python3
# -*- coding: utf-8 -*-

# @Description: Lite Version of EroCool Downloader
# @Author:      PetrelPine [https://github.com/PetrelPine]
# @Contact:     petrelpine@gmail.com (report bugs or give suggestions)
# @Version:     Lite V1.2


from bs4 import BeautifulSoup
from random import uniform
from shutil import copyfile
import requests
import os
import json
import time
import sys
import logging
import colorlog


# print a long line on console to separate different areas
def sep_line():
    logger.debug('\b' * 7 + '--' * 47)


# before calling download_gallery function
def pre_download(input_link):
    sep_line()
    
    def detail_dl(_link):
        try:
            _content = requests.get(_link, headers=HEADERS, timeout=TIMEOUT, proxies=PROXIES)
            _content_status = _content.status_code
            logger.info('Detail page content received.')
            _content_html = BeautifulSoup(_content.text, 'lxml')
        except Exception as _error:
            logger.error('An error has occurred when requesting for detail page!')
            logger.error('Detail Page Error: ' + _link)
            logger.error(repr(_error))
            sep_line()
            return -3
        if _content_status >= 500:
            logger.error('Server Error (%d)! Please try again later.' % _content_status)
            sep_line()
            return -4
        else:
            _status = download_gallery(_content_html, _link)
            return _status

    # detail page
    if 'detail' in input_link:
        return detail_dl(input_link)

    # list page
    else:
        server_error_times = 0  # status code >= 500 times
        no_gallery_times = 0  # # no gallery found times

        # no 'page' in link, identified as the first page
        if 'page' not in input_link:
            input_link = os.path.join(input_link, 'page/1')
            page_num = 1

        # 'page' in link, get the page number
        else:
            try:
                if input_link.endswith('/'):
                    input_link = input_link[0:-1]
                page_num = int(input_link.split('/')[-1])
            except ValueError:
                logger.warning('Cannot find page number, set to 1 instead.')
                input_link = input_link[0:input_link.rfind('page')] + 'page/1'
                page_num = 1

        # 'rank/popular' can't have page number, change to 'rank/day'
        if 'rank/popular' in input_link:
            input_link = input_link.replace('rank/popular', 'rank/day')

        while True:
            list_page_link = os.path.join(os.path.dirname(input_link), str(page_num)).replace('\\', '/')

            try:
                content = requests.get(list_page_link, headers=HEADERS, timeout=TIMEOUT, proxies=PROXIES)
                content_status = content.status_code
                logger.info('List page content received.')
                content_html = BeautifulSoup(content.text, 'lxml')
            except Exception as error:
                logger.error('An error has occurred when requesting for list page!')
                logger.error('List Page Error: ' + list_page_link)
                logger.error(repr(error))
                sep_line()
                return -5
            
            if content_status >= 500:
                logger.error('Server Error (%d)!' % content_status)
                server_error_times += 1
                if server_error_times == 3:
                    logger.error('Server Error times exceed the limit! Please try again later.')
                    sep_line()
                    return -4
                page_num += 1
                sep_line()
                continue
            else:
                server_error_times = 0  # set to 0 if not continuous

            raw_detail_links = content_html.find_all('a', class_='list-wrap gallery')
            
            if raw_detail_links is None:
                logger.warning('No galleries found in current list page!')
                logger.warning('Possible reasons: page exceeded / incorrect class selector.')
                no_gallery_times += 1
                if no_gallery_times == 3:
                    logger.warning('Gallery Not Found times exceed the limit!')
                    sep_line()
                    return -6
                page_num += 1
                sep_line()
                continue
            else:
                no_gallery_times = 0  # set to 0 if not continuous

            for raw_detail_link in raw_detail_links:
                detail_link = PRE_LINK + raw_detail_link.get('href')
                detail_dl(detail_link)
            page_num += 1


# download images from detail page
def download_gallery(content_html, detail_link):
    sep_line()
    timer_start = time.perf_counter()

    if not (content_html.find('h1') and content_html.find('h2')):
        logger.error('Gallery Access Failed! [%s]' % detail_link)
        sep_line()
        return -1

    name_jap = content_html.find('h1').get_text()\
        .replace('?', '？').replace(':', '：').replace('/', ' ').replace('|', '、')\
        .replace('*', '·').replace('"', '\'').replace('<', '《').replace('>', '》')\
        .replace("...", "").replace('\t', ' ').replace('\n', ' ').replace('\\', ' ')\
        .strip('.').strip().strip('.').strip()

    gal_root_path = os.path.join('Gallery', name_jap)
    incomplete_path = os.path.join(gal_root_path, 'incomplete.json')
    incomplete_dict = {"name_jap": name_jap, "detail_link": detail_link}

    # Gallery folder doesn't exist
    if not os.path.exists(gal_root_path):
        os.mkdir(gal_root_path)
        with open(incomplete_path, 'w', encoding='utf-8') as incomplete_file:
            incomplete_file.write(json.dumps(incomplete_dict, ensure_ascii=False))

    # Gallery folder already exists
    else:
        if not os.path.exists(incomplete_path):
            logger.info('Gallery Already Downloaded.')
            sep_line()
            return 1
        else:
            logger.warning('Incomplete Gallery! Initiating Download Process...')

    name_en = content_html.find('h2').get_text()\
        .replace('?', '？').replace(':', '：').replace('/', ' ').replace('|', '、')\
        .replace('*', '·').replace('"', '\'').replace('<', '《').replace('>', '》')\
        .replace("...", "").replace('\t', ' ').replace('\n', ' ').replace('\\', ' ')\
        .strip('.').strip().strip('.').strip()

    # Saves all tags for the current gallery
    raw_tags = content_html.find(class_='listdetail_box ldb1').find_all('div')[-1].find_all('a')
    tags = []
    for raw_tag in raw_tags:
        tags.append(raw_tag.get_text())

    # Save the URLs of all images in the current gallery
    img_links = []
    for img_html in content_html.find_all(class_='vimg lazyload'):
        img_links.append(img_html.get('data-src'))
    img_num_ttl = len(img_links)  # How many images in current gallery

    meta_path = os.path.join(gal_root_path, 'meta.json')
    if not os.path.exists(meta_path):
        with open(meta_path, 'w', encoding='utf-8') as json_file:
            # json.dumps: Encode Python objects as json strings
            # ensure_ascii = True: The default output is ASCII code. If you change this to False, it can accept Chinese
            json_file.write(json.dumps({"name_jap": name_jap, "name_en": name_en, "tags": tags,
                                        "detail_link": detail_link, "img_num_ttl": img_num_ttl,
                                        "img_links": img_links}, ensure_ascii=False))

    logger.info('Downloading Images...')
    untried_links = img_links[:]  # Image links haven't been tried to download
    failed_links = []  # Image links failed to be downloaded
    pic_num_cur = 0  # Number of image that is currently being downloaded

    for img_link in img_links:
        pic_num_cur += 1  # current image number
        img_name = img_link.split('/')[-1]  # image name (sample: 1.jpg / 2.jpg / 3.png / 4.png)
        img_path = os.path.join('Gallery', name_jap, img_name)
        progress = pic_num_cur / img_num_ttl  # progress calculate
        random_wait_time = uniform(2, 4.5)  # sleep, reduce the workload of website
        sep_line()

        # Image not downloaded
        if not os.path.exists(img_path):
            try:
                img_data_raw = requests.get(img_link, headers=HEADERS, timeout=TIMEOUT, proxies=PROXIES)
                img_data = img_data_raw.content
                img_status = img_data_raw.status_code
            except Exception as error:
                logger.error('Download Failed (Request Failed): [%s]  Progress: %.2f%% (%d/%d)'
                             % (img_name, progress * 100, pic_num_cur, img_num_ttl))
                logger.error(repr(error))
                img_data = ''
                img_status = -1

            # Download success (code 200)
            if img_status == 200:
                logger.info('Download Success: [%s]  Progress: %.2f%% (%d/%d)  Sleep: %.2f seconds'
                            % (img_name, progress * 100, pic_num_cur, img_num_ttl, random_wait_time))
                with open(img_path, 'wb') as img_file:
                    img_file.write(img_data)
                time.sleep(random_wait_time)

            elif img_status == -1:
                failed_links.append(img_link)

            # Download failed (code 404) (image not found)
            elif img_status == 404:
                # EroCool's common problem, change the suffix may fix this
                if img_link.endswith('jpg'):
                    untried_links.remove(img_link)
                    img_link = img_link.replace('jpg', 'png')
                    untried_links.append(img_link)
                    img_name = img_name.replace('jpg', 'png')
                    img_path = img_path.replace('jpg', 'png')
                else:
                    untried_links.remove(img_link)
                    img_link = img_link.replace('png', 'jpg')
                    untried_links.append(img_link)
                    img_name = img_name.replace('png', 'jpg')
                    img_path = img_path.replace('png', 'jpg')

                # Try to download the image again
                try:
                    img_data_raw = requests.get(img_link, headers=HEADERS, timeout=TIMEOUT, proxies=PROXIES)
                    img_data = img_data_raw.content
                    img_status = img_data_raw.status_code
                except Exception as error:
                    logger.error('Download Failed (Request Failed): [%s]  Progress: %.2f%% (%d/%d)'
                                 % (img_name, progress * 100, pic_num_cur, img_num_ttl))
                    logger.error(repr(error))
                    img_data = ''
                    img_status = -1

                # Download success (code 200)
                if img_status == 200:
                    logger.info('Download Success: [%s]  Progress: %.2f%% (%d/%d)  Sleep: %.2f seconds'
                                % (img_name, progress * 100, pic_num_cur, img_num_ttl, random_wait_time))
                    with open(img_path, 'wb') as img_file:
                        img_file.write(img_data)
                    time.sleep(random_wait_time)

                elif img_status == -1:
                    failed_links.append(img_link)

                # Download failed (code 400)
                elif img_status == 400:
                    logger.error('Download Failed (Image Lost; code=400): [%s]  Progress: %.2f%% (%d/%d)'
                                 % (img_name, progress * 100, pic_num_cur, img_num_ttl))
                    failed_links.append(img_link)

                # Download failed (other code)
                else:
                    logger.error('Download Failed (Unknown Reason; code=%d): [%s]  Progress: %.2f%% (%d/%d)'
                                 % (img_status, img_name, progress * 100, pic_num_cur, img_num_ttl))
                    failed_links.append(img_link)

            # Download failed (code 400)
            elif img_status == 400:
                logger.error('Download Failed (Image Lost; code=400): [%s]  Progress: %.2f%% (%d/%d)'
                             % (img_name, progress * 100, pic_num_cur, img_num_ttl))
                failed_links.append(img_link)

            # Download failed (other code)
            else:
                logger.error('Download Failed (Unknown Reason; code=%d): [%s]  Progress: %.2f%% (%d/%d)'
                             % (img_status, img_name, progress * 100, pic_num_cur, img_num_ttl))
                failed_links.append(img_link)

        # Image already exists
        else:
            logger.warning('Image Exists: [%s]  Progress: %.2f%% (%d/%d)'
                           % (img_name, progress * 100, pic_num_cur, img_num_ttl))
            untried_links.remove(img_link)
            continue

        # update incomplete info after every image download
        untried_links.remove(img_link)
        incomplete_dict['untried_num'] = len(untried_links)
        incomplete_dict['untried_links'] = untried_links
        incomplete_dict['failed_num'] = len(failed_links)
        incomplete_dict['failed_links'] = failed_links
        with open(incomplete_path, 'w', encoding='utf-8') as incomplete_file:
            incomplete_file.write(json.dumps(incomplete_dict, ensure_ascii=False))

    sep_line()
    timer_stop = time.perf_counter()
    # calculate the time used
    time_used = timer_stop - timer_start
    time_hour = time_used // 3600
    time_used %= 3600
    time_minute = time_used // 60
    time_second = time_used % 60
    logger.info('Process time: %d hours, %d minutes, %.2f seconds.' % (time_hour, time_minute, time_second))

    # Current gallery is complete
    if len(failed_links) == 0:
        try:
            os.remove(incomplete_path)
        except FileNotFoundError:
            pass
        logger.info('Download Complete!')
        sep_line()
        return 1

    # Current gallery is incomplete
    else:
        logger.warning('Download Incomplete!')
        logger.warning('[%d] Failed Images: ' % len(failed_links))
        i = 1
        for failed_link in failed_links:
            logger.error('[%d]: %s' % (i, failed_link))
            i += 1
        sep_line()
        return -2


# save covers of all galleries to 'Cover' folder
def collect_cover():
    sep_line()
    exist_covers = os.listdir('Cover')

    # The list of galleries that have no cover in it.
    cover_missing = []

    for folder_name in os.listdir('Gallery'):
        cover_name_jpg = folder_name + '.jpg'
        cover_name_png = folder_name + '.png'

        if (cover_name_jpg in exist_covers) or (cover_name_png in exist_covers):
            logger.warning('Cover Exists: ' + folder_name)
            continue
        else:
            img_src_jpg = os.path.join(os.path.curdir, 'Gallery', folder_name, '1.jpg')
            img_src_png = os.path.join(os.path.curdir, 'Gallery', folder_name, '1.png')
            img_dst_jpg = os.path.join(os.path.curdir, 'Cover', folder_name + '.jpg')
            img_dst_png = os.path.join(os.path.curdir, 'Cover', folder_name + '.png')
            if os.path.exists(img_src_jpg):
                copyfile(src=img_src_jpg, dst=img_dst_jpg)
                logger.info('Cover Collected: ' + folder_name)
            elif os.path.exists(img_src_png):
                copyfile(src=img_src_png, dst=img_dst_png)
                logger.info('Cover Collected: ' + folder_name)
            else:
                logger.error('Cover Not Found: ' + folder_name)
                cover_missing.append(folder_name)
                continue

    sep_line()
    if len(cover_missing) > 0:
        logger.error('Cover Collection Incomplete: [%d] Covers Missing!' % len(cover_missing))
        i = 1
        for folder in cover_missing:
            logger.error('Cover Not Found [%d]: ' % i + folder)
            i += 1
    else:
        logger.info('Cover Collection Complete!')
    sep_line()


# incomplete galleries download restart
def incomplete_restart():
    sep_line()
    gal_names = os.listdir('Gallery')

    # Find all incomplete galleries
    incomplete_links = []
    incomplete_names = []
    for _gal_name in gal_names:
        incomplete_path = os.path.join('Gallery', _gal_name, 'incomplete.json')

        # load fail info from 'fail.json'
        if os.path.exists(incomplete_path):
            with open(incomplete_path, 'r', encoding='utf-8') as incomplete_file:
                detail_link = json.load(incomplete_file)['detail_link']
                incomplete_links.append(detail_link)
                incomplete_names.append(_gal_name)

    incomplete_num = len(incomplete_links)
    if incomplete_num > 0:
        logger.warning('[%d] incomplete galleries: ' % incomplete_num)
        i = 1
        for incomplete_name in incomplete_names:
            logger.warning('[%d]: %s' % (i, incomplete_name))
            i += 1

        sep_line()
        logger.info('Incomplete Download Process Starts!')
        for detail_link in incomplete_links:
            pre_download(detail_link)

        sep_line()
        logger.info('Incomplete Download Process Finished!')
        sep_line()

    else:
        logger.info('No Incomplete Galleries Found!')
        sep_line()


def set_logger():
    # log color setting
    color_config = {
        'DEBUG': 'white',  # cyan white
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }

    # create logger
    _logger = logging.getLogger()
    # set logger info output minimum value
    _logger.setLevel(logging.NOTSET)

    # local time formatted
    log_time = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime(time.time()))
    # log output save path
    log_path = os.path.join('Log', log_time + '.log')

    # create handler
    file_handler = logging.FileHandler(log_path, mode='w', encoding='utf-8')
    console_handler = logging.StreamHandler()

    # set info output minimum level of each handler
    file_handler.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.DEBUG)

    # create formatter
    file_formatter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s: %(message)s',
                                       datefmt='%Y-%m-%d  %H:%M:%S')
    console_formatter = colorlog.ColoredFormatter(fmt='%(log_color)s[%(asctime)s] %(levelname)s: %(message)s',
                                                  datefmt='%Y-%m-%d  %H:%M:%S',
                                                  log_colors=color_config)
    # set each handler's formatter
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    # add handlers to the main logger
    _logger.addHandler(file_handler)
    _logger.addHandler(console_handler)

    # close all the handlers, to avoid duplicate output
    file_handler.close()
    console_handler.close()

    return _logger


# create folder: 'Gallery', 'Cover', 'Log'
if not os.path.exists('Gallery'):
    os.mkdir('Gallery')
if not os.path.exists('Cover'):
    os.mkdir('Cover')
if not os.path.exists('Log'):
    os.mkdir('Log')

logger = set_logger()

TIMEOUT = (15, 15)
PRE_LINK = 'https://zh.erocool3.com'
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"}
# PROXIES = {'https': 'https://127.0.0.1:1080', 'http': 'http://127.0.0.1:1080'}
PROXIES = {'https': None, 'http': None}  # in order to use ssr

logger.info('This is the lite edition of EroCool Downloader.')
logger.info('Programed by PetrelPine [https://github.com/PetrelPine].')
logger.info('Report bugs or give suggestions: petrelpine@gmail.com')
time.sleep(0.5)  # wait in order to let logger info appears first

# Main Loop
while True:
    print('''
Mode Selection (enter the number):
1  >>> Download From Links
2  >>> Download Daily Ranked Galleries
3  >>> Collect Covers
4  >>> Resume Incomplete Downloads
0  >>> Exit
    ''')
    mode = input('Select Mode (Number Only): ')
    try:
        mode = int(mode)
    except ValueError:
        logger.warning('Invalid Input!')
        time.sleep(0.5)
        continue

    # 0-5 different modes
    if mode == 1:  # detail page / list page download
        links = []
        while True:
            link = input('Please enter the link (Leave blank to finish):')
            if len(link) == 0 or link.isspace():
                break
            else:
                links.append(link)
        if len(links) > 0:
            logger.info('Link Sequence Download Starts.')
            for link in links:
                pre_download(link)
        else:
            continue

    elif mode == 2:  # daily ranked galleries download
        link = PRE_LINK + '/rank/day/'
        pre_download(link)

    elif mode == 3:  # collect covers of downloaded galleries
        collect_cover()

    elif mode == 4:  # resume downloads of all incomplete galleries
        incomplete_restart()

    elif mode == 0:
        sys.exit()

    else:
        logger.warning('Invalid Input!')
        time.sleep(0.5)
        continue

    time.sleep(2)

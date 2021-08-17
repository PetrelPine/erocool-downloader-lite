#!/usr/bin/python3
# -*- coding: utf-8 -*-

# @Description:  EroCool Downloader Lite
# @Github:       https://github.com/PetrelPine/EroCoolDownloaderLite
# @Contact:      petrelpine@gmail.com (report bugs or give suggestions)
# @Version:      v2.1


from win32api import SetFileAttributes as setFiAttr
from bs4 import BeautifulSoup
from random import uniform
from shutil import copyfile
from colorama import init  # show color in cmd window
import requests
import os
import json
import time
import imghdr
init(autoreset=True)  # show color in cmd window


class ColorPrint:
    def __init__(self):
        self.red = 31
        self.green = 32
        self.yellow = 33

    def print_red(self, text):
        print(u'\033[{0}m{1}\033[0m'.format(self.red, text))

    def print_green(self, text):
        print(u'\033[{0}m{1}\033[0m'.format(self.green, text))

    def print_yellow(self, text):
        print(u'\033[{0}m{1}\033[0m'.format(self.yellow, text))


# save untried links to json file
def save_inc_links():
    # remove duplication
    global incomplete_links
    incomplete_links[0] = list(set(incomplete_links[0]))
    incomplete_links[1] = list(set(incomplete_links[1]))

    # save incomplete_links to json file
    with open('_incomplete_links.json', 'w', encoding='utf-8') as _inc_links_json:
        _inc_links_json.write(json.dumps(incomplete_links, ensure_ascii=False))


# before calling gal_download function
def pre_download(input_link):
    input_link_dup = input_link
    print('---' * 20)

    # function: get detail page content
    def get_detail_page(_link, _from_which):
        incomplete_links[0].append(_link)
        save_inc_links()

        try:
            _content = requests.get(_link, headers=HEADERS, timeout=TIMEOUT, proxies=PROXIES)
            _content_status = _content.status_code
            printg('Detail page content received: ' + _link)
            _content_html = BeautifulSoup(_content.text, 'lxml')
        except Exception as _error:
            printr('An error has occurred when requesting for detail page: ' + _link)
            printr('Detail Page Error: ' + _link)
            printr(repr(_error))
            print('---' * 20)
            return -3  # detail page error
        if _content_status >= 500:
            printr('Server Error (%d)! Please try again later.' % _content_status)
            print('---' * 20)
            return -4  # server error
        else:
            _status = gal_download(_content_html, _link, _from_which)  # call gal_download function to dl images
            if _status in [1, 2, -7, -8]:
                incomplete_links[0].remove(_link)
                save_inc_links()
            return _status

    # detail page
    if 'detail' in input_link:
        return get_detail_page(input_link, 'dt')

    # list page
    else:
        server_error_times = 0  # status code >= 500 times
        no_gallery_times = 0  # # no gallery found times

        # first ask to set page range
        page_range_raw = input('Please enter the page number (leave blank to download all pages): \n')
        if not (page_range_raw.isspace() or len(page_range_raw) == 0):
            page_range = page_range_raw.split('-')
            if len(page_range) == 1:
                start_pg = 1
                try:
                    end_pg = int(page_range[0])
                except ValueError:
                    end_pg = 10000
            else:
                try:
                    start_pg = int(page_range[0])
                except ValueError:
                    start_pg = 1
                try:
                    end_pg = int(page_range[1])
                except (ValueError, IndexError):
                    end_pg = 10000
        else:
            start_pg = 1
            end_pg = 10000

        # no 'page' in link, identified as the first page
        if 'page' not in input_link:
            input_link = os.path.join(input_link, 'page/' + str(start_pg))

        # 'page' in link, get the page number
        else:
            try:
                if input_link.endswith('/'):
                    input_link = input_link[0:-1]
                start_pg = int(input_link.split('/')[-1])
                end_pg = start_pg
            except ValueError:
                printy('Cannot find page number in link, follow page range set (%d - %d).' % (start_pg, end_pg))
                input_link = input_link[0:input_link.rfind('page')] + 'page/' + str(start_pg)
                print('---' * 20)

        # show page range that will be downloaded
        printg('These pages will be downloaded: %d -> %d' % (start_pg, end_pg))
        print('---' * 20)

        # 'rank/popular' can't have page number, change to 'rank/day'
        if 'rank/popular' in input_link:
            input_link = input_link.replace('rank/popular', 'rank/day')

        for page_num in range(start_pg, end_pg + 1):
            list_page_link = os.path.join(os.path.dirname(input_link), str(page_num)).replace('\\', '/')
            try:
                content = requests.get(list_page_link, headers=HEADERS, timeout=TIMEOUT, proxies=PROXIES)
                content_status = content.status_code
                printg('List page [%d] content received: %s' % (page_num, list_page_link))
                content_html = BeautifulSoup(content.text, 'lxml')
            except Exception as error:
                printr('An error has occurred when requesting for list page [%d]: %s' % (page_num, list_page_link))
                printr('List Page Error: ' + list_page_link)
                printr(repr(error))
                print('---' * 20)
                return -5  # list page error

            # check server error
            if content_status >= 500:
                print('---' * 20)
                printr('Server Error (%d)!' % content_status)
                server_error_times += 1
                if server_error_times == 3:
                    printr('Server Error times exceed the limit! Please try again later.')
                    print('---' * 20)
                    return -4  # server error
                print('---' * 20)
                continue
            else:
                server_error_times = 0  # set to 0 if not continuous

            raw_info_objs = content_html.find_all('a', class_='list-wrap gallery')
            # check current list page has galleries
            if not raw_info_objs:
                print('---' * 20)
                printy('No galleries found in current list page! (possible reason: page exceeded)')
                no_gallery_times += 1
                if no_gallery_times == 3:
                    print('---' * 20)
                    printy('Gallery Not Found times exceed the limit!')
                    print('---' * 20)
                    # after going through all pages, delete current list page links from incomplete links
                    incomplete_links[1].remove(input_link_dup)
                    save_inc_links()
                    return -6  # list page number exceeded
                print('---' * 20)
                continue
            else:
                no_gallery_times = 0  # set to 0 if not continuous

            print('---' * 20)
            for raw_info_obj in raw_info_objs:
                detail_link = 'https://zh.erocool3.com' + raw_info_obj.get('href')
                name_jap = raw_info_obj.find('h3', class_='caption').get('title') \
                    .replace('?', '？').replace(':', '：').replace('/', ' ').replace('|', '、') \
                    .replace('*', '·').replace('"', '\'').replace('<', '《').replace('>', '》') \
                    .replace("...", "").replace('\t', ' ').replace('\n', ' ').replace('\\', ' ') \
                    .strip('.').strip().strip('.').strip()
                gal_path = os.path.join('Gallery', name_jap)

                # gallery folder exists
                if os.path.exists(gal_path):
                    # and gallery download complete
                    if not os.path.exists(os.path.join(gal_path, 'incomplete.json')):
                        printg('Gallery Already Downloaded: ' + detail_link)
                        print('---' * 20)
                    # gallery download incomplete
                    else:
                        # with excluded tags
                        if os.path.exists(os.path.join(gal_path, 'excluded_tags.json')):
                            printy('Gallery has excluded tags: ' + detail_link)
                            print('---' * 20)
                        # no chinese version
                        elif os.path.exists(os.path.join(gal_path, 'not_chn_ver.json')):
                            printy('Gallery has no chinese version: ' + detail_link)
                            print('---' * 20)
                        else:
                            get_detail_page(detail_link, 'li')
                else:
                    get_detail_page(detail_link, 'li')
        # after going through all the pages in page range
        else:
            # delete current list page links from incomplete links
            incomplete_links[1].remove(input_link_dup)
            save_inc_links()


# download images from detail page
def gal_download(content_html, detail_link, from_which):
    print('---' * 20)
    timer_start = time.perf_counter()

    if not (content_html.find('h1') and content_html.find('h2')):
        printr('Gallery Access Failed! [%s]' % detail_link)
        print('---' * 20)
        return -1  # gallery access error

    name_jap = content_html.find('h1').get_text() \
        .replace('?', '？').replace(':', '：').replace('/', ' ').replace('|', '、') \
        .replace('*', '·').replace('"', '\'').replace('<', '《').replace('>', '》') \
        .replace("...", "").replace('\t', ' ').replace('\n', ' ').replace('\\', ' ') \
        .strip('.').strip().strip('.').strip()

    gal_root_path = os.path.join('Gallery', name_jap)
    incomplete_path = os.path.join(gal_root_path, 'incomplete.json')
    incomplete_dict = {"name_jap": name_jap, "detail_link": detail_link}

    # gallery folder doesn't exist
    if not os.path.exists(gal_root_path):
        os.mkdir(gal_root_path)
        with open(incomplete_path, 'w', encoding='utf-8') as incomplete_file:
            incomplete_file.write(json.dumps(incomplete_dict, ensure_ascii=False))

    # gallery folder already exists
    else:
        if not os.path.exists(incomplete_path):
            printg('Gallery Already Downloaded: ' + detail_link)
            print('---' * 20)
            return 2  # success
        else:
            printy('Incomplete Gallery: ' + detail_link)

    name_en = content_html.find('h2').get_text() \
        .replace('?', '？').replace(':', '：').replace('/', ' ').replace('|', '、') \
        .replace('*', '·').replace('"', '\'').replace('<', '《').replace('>', '》') \
        .replace("...", "").replace('\t', ' ').replace('\n', ' ').replace('\\', ' ') \
        .strip('.').strip().strip('.').strip()

    # all tags of current gallery
    raw_tags = content_html.find(class_='listdetail_box ldb1').find_all('div')[-1].find_all('a')
    tags = []
    # check if excluded tags in current gallery
    excluded_tag_found = False
    for raw_tag in raw_tags:
        tag_text = raw_tag.get_text()
        tags.append(tag_text)
        if tag_text in EXCLUDED_TAGS:
            excluded_tag_found = True

    # the URLs of all images in the current gallery
    img_links = []
    for img_html in content_html.find_all(class_='vimg lazyload'):
        img_links.append(img_html.get('data-src'))
    img_num_ttl = len(img_links)  # How many images in current gallery

    # save the meta info of the gallery
    meta_path = os.path.join(gal_root_path, 'meta.json')
    if not os.path.exists(meta_path):
        with open(meta_path, 'w', encoding='utf-8') as json_file:
            # json.dumps: Encode Python objects as json strings
            # ensure_ascii = True: The default output is ASCII code. False: Chinese available
            json_file.write(json.dumps({"name_jap": name_jap, "name_en": name_en, "tags": tags,
                                        "detail_link": detail_link, "img_num_ttl": img_num_ttl,
                                        "img_links": img_links}, ensure_ascii=False))

    # if from list page, and the gallery has excluded tags
    if from_which == 'li' and excluded_tag_found:
        printy('Excluded tags found; download cancelled.')
        with open(os.path.join(gal_root_path, 'excluded_tags.json'), 'w', encoding='utf-8') as exc_file:
            exc_file.write(json.dumps({'tags': tags, 'excluded_tags': EXCLUDED_TAGS}, ensure_ascii=False))
        # hide folder of current gallery
        setFiAttr(gal_root_path, 2)
        print('---' * 20)
        return -7  # excluded tags found

    # if from list page, check if the language is chinese
    if from_which == 'li':
        # find the language of current gallery
        raw_gal_languages = content_html.find(class_='listdetail_box ldb1') \
            .find_all('div')[0].find_all('div')[10].find_all('a')
        gal_languages = []
        for raw_gal_language in raw_gal_languages:
            gal_languages.append(raw_gal_language.get_text())
        # not chinese version
        if '漢化' not in gal_languages:
            printy('Not Chinese version; download cancelled.')
            with open(os.path.join(gal_root_path, 'not_chn_ver.json'), 'w', encoding='utf-8') as lang_file:
                lang_file.write(json.dumps({'language': gal_languages}, ensure_ascii=False))
            # hide folder of current gallery
            setFiAttr(gal_root_path, 2)
            print('---' * 20)
            return -8  # not chinese version

    # function: make sure images have the right extensions
    def check_ext():
        img_real_ext = imghdr.what(img_path)
        if img_real_ext == 'jpeg':
            img_real_ext = 'jpg'
        # some image's extension cannot be identified, set to jpg
        if img_real_ext is None:
            img_real_ext = 'jpg'
        img_cur_ext = os.path.splitext(img_path)[1][1:]
        # incorrect image extension
        if img_real_ext != img_cur_ext:
            _dst_path = os.path.join(os.path.dirname(img_path), str(img_num) + '.' + img_real_ext)
            os.rename(img_path, _dst_path)

    printg('Downloading Images...')
    failed_links = []  # image links download failed
    same_err_times = 0  # continuous same error occur times
    img_status_prev = -100  # img_status of previous image
    for img_link in img_links:
        img_name = img_link.split('/')[-1]  # image name (sample: 1.jpg / 2.jpg / 3.png / 4.png)
        img_num = int(img_name.split('.')[0])  # image number (sample: 1 / 2 / 3 / 4)
        img_path = os.path.join('Gallery', name_jap, img_name)

        progress = img_num / img_num_ttl  # progress
        random_wait_time = uniform(0, 1)  # random wait time after each image download
        print('---' * 20)

        img_path_jpg = os.path.join('Gallery', name_jap, str(img_num) + '.jpg')
        img_path_png = os.path.join('Gallery', name_jap, str(img_num) + '.png')
        # image not downloaded
        if not os.path.exists(img_path_jpg or img_path_png):
            try:
                img_data_raw = requests.get(img_link, headers=HEADERS, timeout=TIMEOUT, proxies=PROXIES,
                                            allow_redirects=False)
                img_data = img_data_raw.content
                img_status = img_data_raw.status_code
            except Exception as error:
                img_status = -1
                img_data = 'None'
                printr(repr(error))

            # download success (code 200)
            if img_status == 200:
                same_err_times = 0
                printg('Download Success.  Progress: %.2f%% (%d/%d)' % (progress * 100, img_num, img_num_ttl))
                with open(img_path, 'wb') as img_file:
                    img_file.write(img_data)
                check_ext()  # check image extension

            # download failed (code 404) (image not found)
            elif img_status == 404:
                printy('Extension Changed.')
                # common problem of EroCool, change the suffix may fix this
                if img_link.endswith('jpg'):
                    img_link = img_link.replace('jpg', 'png')
                    img_path = img_path.replace('jpg', 'png')
                else:
                    img_link = img_link.replace('png', 'jpg')
                    img_path = img_path.replace('png', 'jpg')

                # try to download the image again
                try:
                    img_data_raw = requests.get(img_link, headers=HEADERS, timeout=TIMEOUT, proxies=PROXIES,
                                                allow_redirects=False)
                    img_data = img_data_raw.content
                    img_status = img_data_raw.status_code
                except Exception as error:
                    img_status = -1
                    img_data = 'None'
                    printr(repr(error))

                # download success (code 200)
                if img_status == 200:
                    same_err_times = 0
                    printg('Download Success.  Progress: %.2f%% (%d/%d)' % (progress * 100, img_num, img_num_ttl))
                    with open(img_path, 'wb') as img_file:
                        img_file.write(img_data)
                    check_ext()  # check image extension

                # download failed with error code
                else:
                    printr('Download Failed! (code=%d)  Progress: %.2f%% (%d/%d)'
                           % (img_status, progress * 100, img_num, img_num_ttl))
                    failed_links.append(img_link)
                    if img_status == img_status_prev:
                        same_err_times += 1
                        if same_err_times >= 5:
                            print('---' * 20)
                            printr('Error (code=%d) Times Exceed the Limit!' % img_status)
                            break
                    else:
                        same_err_times = 0

            # download failed with error code
            else:
                printr('Download Failed! (code=%d)  Progress: %.2f%% (%d/%d)'
                       % (img_status, progress * 100, img_num, img_num_ttl))
                failed_links.append(img_link)
                if img_status == img_status_prev:
                    same_err_times += 1
                    if same_err_times >= 5:
                        print('---' * 20)
                        printr('Error (code=%d) Times Exceed the Limit!' % img_status)
                        break
                else:
                    same_err_times = 0

            img_status_prev = img_status
            time.sleep(random_wait_time)

        # image already exists
        else:
            printy('Image Exists.  Progress: %.2f%% (%d/%d)' % (progress * 100, img_num, img_num_ttl))

    # calculate the time used
    print('---' * 20)
    timer_stop = time.perf_counter()
    time_used = timer_stop - timer_start
    time_hour = time_used // 3600
    time_used %= 3600
    time_minute = time_used // 60
    time_second = time_used % 60
    printg('Process time: %d hours, %d minutes, %.2f seconds.' % (time_hour, time_minute, time_second))

    # download complete
    if len(failed_links) == 0:
        # delete 'incomplete.json' file
        if os.path.exists(incomplete_path):
            os.remove(incomplete_path)
        printg('Download Complete.')
        print('---' * 20)
        return 1  # download complete

    # download incomplete
    else:
        printy('Download Incomplete: [%d] Failed Images: ' % len(failed_links))
        for failed_link in failed_links:
            printr(failed_link)
        print('---' * 20)
        return -2  # gallery download incomplete: failed images


# download from input links (detail / list page links)
def download_links():
    links = [[], []]
    while True:
        link = input('Please enter the link (Leave blank to finish): ')
        if len(link) == 0 or link.isspace():
            break
        else:
            if not link.startswith('https://zh.erocool3.com/'):
                printy("Warning: Link doesn't start with 'https://zh.erocool3.com', current link will be skipped.")
            else:
                if '/detail/' in link:
                    links[0].append(link)
                    incomplete_links[0].append(link)
                else:
                    links[1].append(link)
                    incomplete_links[1].append(link)

    save_inc_links()
    # link sequence download
    if len(links[0]) > 0 or len(links[1]) > 0:
        printg('Link Sequence Download Started.')
        for link in links[0]:
            pre_download(link)
        for link in links[1]:
            pre_download(link)
        printg('Link Sequence Download Finished.')
        print('---' * 20)
    else:
        printy('No Link Added!')
        print('---' * 20)


# save covers of all galleries to 'Cover' folder
def collect_cover():
    print('---' * 20)
    exist_covers = os.listdir('Cover')

    cover_missing = []
    cover_missing_chn = []
    cover_missing_tag = []
    cover_collected = []

    for folder_name in os.listdir('Gallery'):
        cover_name_jpg = folder_name + '.jpg'
        cover_name_png = folder_name + '.png'

        # cover exists
        if (cover_name_jpg in exist_covers) or (cover_name_png in exist_covers):
            print('Cover Exists: ' + folder_name)

        # cover not exists
        else:
            img_src_jpg = os.path.join(os.path.curdir, 'Gallery', folder_name, '1.jpg')
            img_src_png = os.path.join(os.path.curdir, 'Gallery', folder_name, '1.png')
            img_dst_jpg = os.path.join(os.path.curdir, 'Cover', folder_name + '.jpg')
            img_dst_png = os.path.join(os.path.curdir, 'Cover', folder_name + '.png')

            # cover found
            if os.path.exists(img_src_jpg):
                copyfile(src=img_src_jpg, dst=img_dst_jpg)
                cover_collected.append(folder_name)
            elif os.path.exists(img_src_png):
                copyfile(src=img_src_png, dst=img_dst_png)
                cover_collected.append(folder_name)

            # cover not found
            else:
                # gallery with excluded tags
                if os.path.exists(os.path.join('Gallery', folder_name, 'excluded_tags.json')):
                    cover_missing_tag.append(folder_name)
                # gallery without chinese version
                elif os.path.exists(os.path.join('Gallery', folder_name, 'not_chn_ver.json')):
                    cover_missing_chn.append(folder_name)
                else:
                    cover_missing.append(folder_name)

    if len(cover_missing_chn) > 0:
        print('---' * 20)
        for folder_name in cover_missing_chn:
            printy('Cover Not Found (NOT-CHN-LANG): ' + folder_name)

    if len(cover_missing_tag) > 0:
        print('---' * 20)
        for folder_name in cover_missing_tag:
            printy('Cover Not Found (EXCLUDED-TAGS): ' + folder_name)

    if len(cover_collected) > 0:
        print('---' * 20)
        for folder_name in cover_collected:
            printg('Cover Collected: ' + folder_name)

    if len(cover_missing) > 0:
        print('---' * 20)
        printr('Warning: %d Covers Missing!' % len(cover_missing))
        for folder_name in cover_missing:
            printr('Cover Not Found: ' + folder_name)

    print('---' * 20)
    printg('Cover Collect Process Finished.')
    print('---' * 20)


# incomplete galleries download
def incomplete_restart():
    incomplete_dtlinks = incomplete_links[0][:]
    incomplete_num = len(incomplete_dtlinks)
    if incomplete_num > 0:
        printy('[%d] Incomplete Galleries: ' % incomplete_num)
        for incomplete_dtlink in incomplete_dtlinks:
            printy(incomplete_dtlink)

        print('---' * 20)
        printg('Incomplete Download Process Started.')
        for detail_link in incomplete_dtlinks:
            pre_download(detail_link)

        print('---' * 20)
        # still have incomplete detail links
        if len(incomplete_links[0]) > 0:
            printy('%d Incomplete Galleries Remaining!' % len(incomplete_links[0]))
            for incomplete_link in incomplete_links[0]:
                printy(incomplete_link)
        else:
            printg('All Incomplete Links Finished.')

        print('---' * 20)
        printg('Incomplete Download Process Finished.')
        print('---' * 20)
    # no incomplete links
    else:
        print('---' * 20)
        printg('No Incomplete Galleries Found.')
        print('---' * 20)


# open gallery with specific name
def open_gallery():
    name = input('Please enter the name of the gallery: ')
    exist_galleries = os.listdir('Gallery')
    if name in exist_galleries:
        print('---' * 20)
        printg('Target gallery found, opening...')
        os.system("explorer \"" + os.getcwd() + "\\Gallery\\" + name + "\"")
        print('---' * 20)
    else:
        print('---' * 20)
        printy('Target gallery not found, gallery folder will be opened instead.')
        os.system("explorer \"" + os.getcwd() + "\\Gallery\"")
        print('---' * 20)


# create folder: 'Gallery', 'Cover'
if not os.path.exists('Gallery'):
    os.mkdir('Gallery')
if not os.path.exists('Cover'):
    os.mkdir('Cover')

# load incomplete_links from json file
incomplete_links = [['Error'], ['Error']]
if not os.path.exists('_incomplete_links.json'):
    incomplete_links = [[], []]
    with open('_incomplete_links.json', 'w', encoding='utf-8') as inc_links_json:
        inc_links_json.write(json.dumps(incomplete_links, ensure_ascii=False))
else:
    with open('_incomplete_links.json', 'r', encoding='utf-8') as inc_links_json:
        incomplete_links = json.load(inc_links_json)


TIMEOUT = (15, 15)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"}
PROXIES = {'https': None, 'http': None}  # support ssr global mode
# Exclude the galleries that have tags you don't want to see
EXCLUDED_TAGS = ['㚻 (男男性愛)', 'yaoi', '扶她', 'futanari', '只有男性', 'males only', '性轉換', 'gender bender',
                 '藥娘', 'tomgirl', 'tomboy', '獵奇向', 'guro', '殘缺', 'incomplete', '釘住', 'pegging',
                 '雙肛門', 'double anal', '腦交', 'brain fuck', '殭屍', 'zombie',
                 'dickgirl on male', 'male on dickgirl', 'sole dickgirl', ]

color_print = ColorPrint()
printr = color_print.print_red
printg = color_print.print_green
printy = color_print.print_yellow

printg('EroCool Downloader Lite v2.1')
printg('https://github.com/PetrelPine/EroCoolDownloaderLite')
time.sleep(0.5)

# main loop
while True:
    print('''
Mode Selection (enter the number):
1  >>>  Download from Links
2  >>>  Collect Covers
3  >>>  Resume Incomplete Downloads
4  >>>  Open Gallery by Name
    ''')
    mode = input('Select Mode (Number Only): \n')
    try:
        mode = int(mode)
    except ValueError:
        printy('Invalid Input!')
        time.sleep(0.5)
        continue

    # return status of pre_download func and gal_download func
    # return  1  download success
    # return  2  gallery already downloaded
    # return -1  gallery access error (h1 or h2 not found)
    # return -2  gallery download incomplete (failed images)
    # return -3  detail page error (request failed)
    # return -4  server error (request failed)
    # return -5  list page error (request failed)
    # return -6  list page number exceeded
    # return -7  excluded tags found
    # return -8  not chinese version

    # 1-4 different modes
    if mode == 1:  # detail page / list page download
        download_links()
        time.sleep(2)

    elif mode == 2:  # collect covers of downloaded galleries
        collect_cover()
        time.sleep(2)

    elif mode == 3:  # resume downloads of all incomplete galleries
        incomplete_restart()
        time.sleep(2)

    elif mode == 4:  # open the gallery with specific name
        open_gallery()
        time.sleep(2)

    else:
        printy('Invalid Input!')
        time.sleep(0.5)

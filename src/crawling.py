from bs4 import BeautifulSoup
import requests
import re
import queue
import threading
import time
from datetime import datetime
from dateutil.relativedelta import *
import json
import schedule
import cnn_lstm
import gen_data
import numpy as np

HOST = '127.0.0.1'
PORT = 9999
BUFSIZE = 1024
ADDR = (HOST, PORT)
bokjiro_list = []
jungbu24_list = []
urls_bok = "http://www.bokjiro.go.kr"
urls_jung = "https://www.gov.kr"
lock = threading.Lock()
que = queue.Queue()
keyword = [
    '저소득',
    '다문화',
    '한부모',
    '고령자',
    '장애인'
]
latest_url = {  # 가장 최신글 url 딕셔너리
    '복지로최신url': ' ',
    '저소득': ' ',
    '한부모': ' ',
    '다문화': ' ',
    '고령자': ' ',
    '장애인': ' '
}
config = {
    "user": "gajok",
    "password": "1234!",
    "host": "192.168.1.10",  # local
    "database": "crolls",  # Database name
    "port": "3306"  # port는 최초 설치 시 입력한 값(기본값은 3306)
}


def change_date(day1, day2):
    day1 = str(day1 + relativedelta(months=-1)).split(" ")[0].replace('-','.')
    day2 = str(day2 + relativedelta(months=-1)).split(" ")[0].replace('-','.')

    if day1.split(".")[2] != day2.split(".")[2]:
        day2 = day2.split(".")[0]+"."+day2.split(".")[1]+"."+day1.split(".")[2]
    return day1, day2


def bokjiro(que, t):
    url = requests.get("http://www.bokjiro.go.kr/nwel/helpus/welsha/selectWelShaInfoBbrdMngList.do", verify=False)
    urls = "http://www.bokjiro.go.kr"
    soup = BeautifulSoup(url.content, "lxml")
    a = soup.find("a", {"class": "num"})
    list_page_urls = [a['href']]
    page_token = list_page_urls[0].split('pageIndex=')[0]
    last_page = soup.find_all("a", {'class': 'goLast'})
    last_page_num = last_page[0].get('href').split('pageIndex=')[1]
    latest = ''
    lock.acquire()
    try:
        with open('../data/url.json', 'r', encoding='utf-8')as f:
            latest_url = json.load(f)
    except json.decoder.JSONDecodeError:
        with open('../data/url.json', 'w', encoding='utf-8')as make_file:
            json.dump(latest_url, make_file, ensure_ascii=False, indent="\t")
        print("json 예외발생")
    lock.release()
    cnt = 1
    first = 1
    break_point = 0
    print('복지로')
    ########################### 최신 url없고 모두 가져올 때 #################################3
    if latest_url['복지로최신url'] == " ":
        while cnt < int(last_page_num) + 1:
            urls = "http://www.bokjiro.go.kr"
            origin_urls = urls + page_token + 'pageIndex=' + str(cnt)
            page_urls = requests.get(origin_urls, verify=False)
            soup = BeautifulSoup(page_urls.content, "lxml")
            try:
                data = soup.find_all("a", {'class': 'point10'})
            except IndexError as e:
                print('복지로: 해당 페이지에 공지사항이 없습니다.')
                cnt = cnt + 1
                continue
            for i in data:
                if first == 1:
                    latest_url['복지로최신url'] = str(i['href'])
                    first = first + 1
                with open('../data/url.json', 'r', encoding='utf-8')as f:
                    json_data = json.load(f)
                if str(i['href']) == str(json_data['복지로최신url']):
                    print("제일 최신글입니다.")
                    break_point = 1
                    break
                else:
                    lock.acquire()
                    que.put(i['href'] + " b")
                    lock.release()
            cnt = cnt + 1
            print(" 복지로 " + origin_urls)
        lock.acquire()
        with open('../data/url.json', 'w', encoding='utf-8')as make_file:
            json.dump(latest_url, make_file, ensure_ascii=False, indent="\t")
        lock.release()
    else:  ################ 최신 url있을 때 ######################
        while cnt < int(last_page_num) + 1:
            if break_point == 1:
                break
            origin_urls = urls + page_token + 'pageIndex=' + str(cnt)
            page_urls = requests.get(origin_urls, verify=False)
            soup = BeautifulSoup(page_urls.content, "lxml")
            cnt = cnt + 1
            try:
                data = soup.find_all("a", {'class': 'point10'})
            except IndexError as e:
                print('복지로: 해당 페이지에 공지사항이 없습니다.')
                continue
            for i in data:
                print(i['href'], end='')
                print(t)
                if first == 1:
                    latest = str(i['href'])
                    first = first + 1
                with open('../data/url.json', 'r', encoding='utf-8')as f:
                    json_data = json.load(f)
                if str(i['href']) == str(json_data['복지로최신url']):
                    print("복지로: 제일 최신글입니다.")
                    break_point = 1
                    break
                else:
                    lock.acquire()
                    que.put(i['href'] + " b")
                    lock.release()
        latest_url['복지로최신url'] = latest
        lock.acquire()
        with open('../data/url.json', 'w', encoding='utf-8')as make_file:
            json.dump(latest_url, make_file, ensure_ascii=False, indent="\t")
        lock.release()


def government24(que, t):
    page_token0 = "https://www.gov.kr/portal/locgovNews"
    page_token1 = "?srchOrder=&sido=&signgu=&srchArea=&srchSidoArea=&srchStDtFmt="
    page_token2 = "&srchEdDtFmt="
    page_token3 = "&srchTxt="
    page_token4 = "&initSrch=false&pageIndex="
    date = datetime.now().date()
    before_date = str(date + relativedelta(months=-1)).replace('-', '.')
    date = str(date).replace('-', '.')
    change_date1, change_date2 = before_date, date
    latest = []
    lock.acquire()
    try:
        with open('../data/url.json', 'r', encoding='utf-8')as f:
            latest_url = json.load(f)
    except json.decoder.JSONDecodeError:
        with open('../data/url.json', 'r', encoding='utf-8')as make_file:
            json.dump(latest_url, make_file, ensure_ascii=False, indent="\t")
        print("json 예외발생")
    lock.release()
    for j in range(0, len(keyword)):
        first = 0
        ########## 최신 url이 비어있을 때 전체 공지 크롤링 ################
        if latest_url[keyword[j]] == " ":
            print('정부24 : ' + keyword[j])
            start_url = page_token0 + page_token1 + change_date1 + page_token2 + change_date2 + page_token3 + str(
                keyword[j]) + page_token4 + '1'
            url = requests.get(start_url, verify=False)
            soup = BeautifulSoup(url.content, "lxml")
            last_page_url = soup.select('.pagination li a')
            sp = re.split('pageIndex=', str(last_page_url[len(last_page_url) - 1]))[1]
            last_page_num = sp.split('"')[0]
            for term in range(1, 100):  # 몇 년?
                change_date1, change_date2 = before_date, date
                if term != 1:
                    change_date1, change_date2 = change_date(datetime.strptime(change_date1, '%Y.%m.%d'), change_date2)  # 날짜 변경
                for count in range(1, int(last_page_num) + 1):
                    origin_urls = page_token0 + page_token1 + change_date1 + page_token2 + change_date2 + page_token3 + str(
                        keyword[j]) + page_token4 + str(count)
                    url = requests.get(origin_urls, verify=False)
                    soup = BeautifulSoup(url.content, "lxml")
                    try:
                        data2 = soup.select(".pcb > a")
                    except IndexError as e:
                        print("정부24" + keyword[j] + ": 해당 페이지(" + last_page_num + ")에 공지사항이 없습니다.")
                        continue
                    for i in data2:
                        if first == 0:
                            latest_url[keyword[j]] = str(i['href'])
                            first = first + 1
                        lock.acquire()
                        que.put(str(i['href']) + " j")
                        lock.release()
                        print(str(i['href']))
                lock.acquire()
                with open('../data/url.json', 'w', encoding='utf-8')as make_file:
                    json.dump(latest_url, make_file, ensure_ascii=False, indent="\t")
                lock.release()
        #################### 최신 url이 있을 때 업데이트 확인 여부 ################
        else:
            first = 0
            break_point = 0
            print(keyword[j])
            change_date1, change_date2 = before_date, date
            start_url = page_token0 + page_token1 + change_date1 + page_token2 + change_date2 + page_token3 + str(
                keyword[j]) + page_token4 + '1'
            url = requests.get(start_url, verify=False)
            soup = BeautifulSoup(url.content, "lxml")
            last_page_url = soup.select('.pagination li a')
            try:
                sp = re.split('pageIndex=', str(last_page_url[len(last_page_url) - 1]))[1]
            except IndexError:
                print('page error')
                continue
            last_page_num = sp.split('"')[0]
            for term in range(1, 100):  # 몇 년?
                if break_point == 1:
                    break
                if term != 1:

                    change_date1, change_date2 = change_date(datetime.strptime(change_date1, '%Y.%m.%d'), datetime.strptime(change_date2, '%Y.%m.%d'))  # 날짜 변경
                for count in range(1, int(last_page_num) + 1):
                    if break_point == 1:
                        break
                    origin_urls = page_token0 + page_token1 + change_date1 + page_token2 + change_date2 + page_token3 + str(
                        keyword[j]) + page_token4 + str(count)
                    url = requests.get(origin_urls, verify=False)
                    soup = BeautifulSoup(url.content, "lxml")
                    try:
                        data2 = soup.select(".pcb > a")  # soup.find_all("dt>a", {'class': 'pcb'})
                    except IndexError as e:
                        print("정부24" + keyword[j] + ": 해당 페이지(" + last_page_num + ")에 공지사항이 없습니다.")
                        continue
                    for i in data2:
                        if first == 0:
                            latest = str(i['href']).split('?')[0].split('/')[3]
                            first = first + 1
                        if latest_url[keyword[j]] == str(i['href']).split('?')[0].split('/')[3]:
                            print('최신글입니다.')
                            break_point = 1
                            break
                        else:
                            lock.acquire()
                            que.put(str(i['href']).split('pageIndex')[0] + 'hideurl=N' + " j")
                            lock.release()
                            print(str(i['href']).split('pageIndex')[0] + 'hideurl=N', end='')
                            print(t)
            latest_url[keyword[j]] = latest
            lock.acquire()
            with open('../data/url.json', 'w', encoding='utf-8')as make_file:
                json.dump(latest_url, make_file, ensure_ascii=False, indent="\t")
            lock.release()


def save_content(que, t):
    while que.qsize() != 0:
        list_urls = que.get()
        try:
            confirm = list_urls.split(" ")[1]
        except IndexError:
            continue
        list_urls = list_urls.split(" ")[0]
        if confirm == 'b':  # 복지로
            next_urls = urls_bok + list_urls
            url_b = next_urls
            New_url = requests.get(next_urls, verify=False)
            soup = BeautifulSoup(New_url.content, "lxml")
            titles = str(soup.select('.serviceName'))
            if titles == '[]':
                print('복지로: 해당 게시글이 비어있습니다.')
            else:
                title_b = re.sub('<.+?>', '', titles, 0).strip()
                print('복지로' + title_b, end='')
                print(t)
                content_b = re.sub('<.+?>', '', str(soup.select('.shareServiceCont')), 0).strip()
                html_b = str(soup.select('.shareServiceCont'))
                lock.acquire()
                bokjiro_list.append([title_b, content_b, html_b, url_b])
                lock.release()
        ################################################################################################################
        elif confirm == 'j':  # 정부24
            next_urls = urls_jung + list_urls
            url_j = next_urls
            New_url = requests.get(next_urls, verify=False)
            soup = BeautifulSoup(New_url.content, "lxml")
            content = soup.select('body > div.contentsWrap.r2n > .contents > .cont-inner > '
                                  '.tbl-view.gallery-detail > .view-contents')
            if content == '[]':
                print('정부 24: 해당 게시글이 비어있습니다.')
            else:
                html_j = str(content)
                content_j = re.sub('<.+?>', '', str(content), 0).strip()
                title_j = re.sub('<.+?>', '', str(soup.select('.tit2')), 0).strip()
                print(" 정부 24 " + re.sub('<.+?>', '', str(soup.select('.tit2')), 0).strip(), end='')
                print(t)
                lock.acquire()
                jungbu24_list.append([title_j, content_j, html_j, url_j])
                lock.release()


def thread(que):
    t1 = threading.Thread(target=bokjiro, args=(que, '스레드1'))
    t2 = threading.Thread(target=government24, args=(que, '스레드2'))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    t3 = threading.Thread(target=save_content, args=(que, '스레드3'))
    t4 = threading.Thread(target=save_content, args=(que, '스레드4'))
    t5 = threading.Thread(target=save_content, args=(que, '스레드5'))
    t6 = threading.Thread(target=save_content, args=(que, '스레드6'))
    t3.start()
    t4.start()
    t5.start()
    t6.start()
    t3.join()
    t4.join()
    t5.join()
    t6.join()
    print('Finish')
    print('start categorizing')
    # conn = mysql.connector.connect(**config)
    # cursor = conn.cursor()
    # _cursor = conn.cursor(dictionary=True)
    result = []
    result.extend(bokjiro_list)
    result.extend(jungbu24_list)
    if len(result) != 0:
        word2vector = gen_data.update_support(result)
        category = cnn_lstm.categorization(word2vector)
        category2 = np.array(category).reshape(1, len(category))
        complete = np.concatenate((result, category2.T), axis=1)  # 카테고리화된 리스트와 지원사업 원본 합치기
        body = [{'title': i[0], 'content': i[1], 'url': i[3], 'category': i[4]} for i in complete]  # json 변환

        for i in body:
            try:
                response = requests.post("https://api.bluemango.me/update", data=i)  # api 전송
                # json리스트를 한번에 보내려고했으나 에러떠서 하나씩 보냄
                # 도메인 때문인지 postman도 그렇고 api get,post 요청 먹통
                print(response)
            except requests.exceptions.ConnectionError:
                print('api post failed!')
                break
    else:
        print('no updated support post!')
    print('end categorizing')
    a = 1
    # for i in result:
    #     sql = "INSERT INTO data_set2 (title, CONTENT, url) select %s, %s, %s from dual WHERE NOT EXISTS(SELECT title, CONTENT,url FROM data_set2 WHERE CONTENT = %s);"
    #     _cursor.execute(sql, (i[0], i[2], i[3], i[2]))
    #     conn.commit()

    # print('end db')
    # conn.close()
    bokjiro_list.clear()
    jungbu24_list.clear()
    result.clear()


schedule.every().day.at("12:00").do(thread, que)

if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    while True:
        thread(que)
        # schedule.run_pending()
        time.sleep(1)

from konlpy.tag import Mecab
import pandas as pd
import pymysql
import re
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

metadata = pd.read_csv("../make_data/metadata_1.tsv", delimiter='\t')
vector = pd.read_csv("../make_data/vectors_1.tsv", delimiter='\t')
tags = ['NNG', 'NNP', 'NNB', 'XR']


def get_vector(sentense):
    mecab = Mecab()
    selected = []
    pos = mecab.pos(
        re.sub('<.+?>', '', sentense, 0, re.I | re.S).replace('[', '').replace(']', '').replace('\r', '').replace('\n',
                                                                                                                  ''))
    for one in pos: # 여기 예외처리
        try:
            idx = metadata.index[metadata['word'] == one[0]].tolist()
        except IndexError:
            continue
        if one[1] in tags and len(idx) == 1:
            selected.append(vector.iloc[idx[0]].tolist())
    return selected


def update_support(result):
    data = []
    for i in result:
        article = get_vector(i[0])
        article += get_vector(i[1])
        word_count = len(article)
        if word_count > 40:
            data.append(article[0:40])
        elif word_count<40:
            for i in range(0, 40-word_count):
                article.append([0 for j in range(0,16)])
            data.append(article)
        else:
            data.append(article)

    update_data = np.array(data)
    return update_data


if __name__ == "__main__":
    data = []
    label = []
    count = {}

    conn = pymysql.connect(host='192.168.1.10', user='gajok', password='1234!', charset='utf8', db='crolls')
    cursor = conn.cursor()

    sql = "SELECT title, content, etc FROM data_set2"
    cursor.execute(sql)
    res = cursor.fetchall()
    mecab = Mecab()
    for one in tqdm(res):
        article = get_vector(one[0])
        article += get_vector(one[1])
        word_count = len(article)
        if word_count>40:
            data.append(article[0:40])
        elif word_count<40:
            for i in range(0,40-word_count):
                article.append([0 for j in range(0,16)])
            data.append(article)
        else:
            data.append(article)

        if one[2].split(',')[0] == "장애인":
            label.append([1, 0, 0, 0, 0])
        elif one[2].split(',')[0] == "저소득":
            label.append([0, 1, 0, 0, 0])
        elif one[2].split(',')[0] == "다문화":
            label.append([0, 0, 1, 0, 0])
        elif one[2].split(',')[0] == "고령자":
            label.append([0, 0, 0, 1, 0])
        elif one[2].split(',')[0] == "한부모":
            label.append([0, 0, 0, 0, 1])

    data = np.array(data)
    label = np.array(label)
    np.save("data", data)
    np.save("label", label)

    a=1

    plt.plot(count.values(), count.keys())
    plt.show()
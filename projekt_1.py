from flask import *
import os
from io import BytesIO
import base64
import csv
import operator
from collections import Counter
from collections import OrderedDict
from itertools import islice
from pandas import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


app = Flask(__name__)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))


@app.route('/')
def form():
    return render_template("form.html")


def read_data():
    with open(os.path.join(APP_ROOT, "DFE-Biomedical-Images.csv")) as csvfile:
        data = [row for row in csv.reader(csvfile.read().splitlines())]
    return data


@app.route('/data')
def data_view():
    data = read_data()
    index = request.args.get("index")
    index = int(index)
    f = open(os.path.join(APP_ROOT, 'config.txt'), 'w')
    f.write(str(index))
    f.close()
    return render_template('data_view.html', data=data[index + 1:])


@app.route('/stats')
def stats_view():
    data = read_data()

    f = open(os.path.join(APP_ROOT, 'config.txt'), 'r')
    index = int(f.readline())
    f.close()

    classification = Counter()
    category = Counter()
    yes_category = Counter()
    no_category = Counter()
    c_category = Counter()
    good_confidence = 0
    wrong_confidence = 0
    yes_count = 0
    confidence = Counter()

    number = len(data) - index
    for i in range(index+1, len(data)):
        if data[i][5] == "Yes, perfect classification":
            yes_category[data[i][7]] += 1
            yes_count += 1
            good_confidence += float(data[i][6])
            confidence[data[i][7]] += float(data[i][6])
        elif data[i][5] == "No, wrong category":
            no_category[data[i][7]] += 1
            wrong_confidence += float(data[i][6])
        else:
            c_category[data[i][7]] += 1
        category[data[i][7]] += 1
        classification[data[i][5]] += 1

    max_category = max(category.iteritems(), key=operator.itemgetter(1))
    max_yes = max(yes_category.iteritems(), key=operator.itemgetter(1))

    stats = OrderedDict([
                ('Starting index: ', index),
                ('Selected number of records: ', number),
                ('Good classification confidence average: ', round(good_confidence/classification["Yes, perfect classification"], 2)),
                ('Wrong classification confidence average: ', round(wrong_confidence/classification["No, wrong category"], 2)),
                ('Most frequent category: ', max_category[0]),
                ('Most frequent category percentage in selected records: ', round(max_category[1] / float(number), 2) * 100),
                ('Best classified category: ', max_yes[0]),
                ('Best classified category percentage in good classification results: ', round(max_yes[1] / float(yes_count), 2) * 100)
    ])

    yes = round(classification["Yes, perfect classification"] / float(number), 2) * 100
    no = round(classification["No, wrong category"] / float(number), 2) * 100
    compound = round(classification["Compound image"] / float(number), 2) * 100

    s3 = Series([yes, no, compound], name='')
    s3.plot.pie(legend=False, labels=['good', 'wrong', 'undefined'], colors=['#33691E', '#B71C1C', '#9E9E9E'],
                explode=(0.15, 0, 0), autopct='%.2f%%', fontsize=12, figsize=(6, 6))

    f3 = BytesIO()
    plt.savefig(f3, format='png')
    f3.seek(0)
    d3 = f3.getvalue()
    d3 = base64.b64encode(d3)

    f3.flush()
    plt.cla()
    plt.clf()

    category_sort = sorted(category.items(), key=lambda (k, val): (-val, k))
    c = OrderedDict(islice(OrderedDict(category_sort).items(), 5))

    arr = [[yes_category[c.items()[i][0]], no_category[c.items()[i][0]], c_category[c.items()[i][0]]] for i in range(5)]
    label = [c.items()[i][0][:6] for i in range(5)]

    df1 = DataFrame(arr, label, columns=['good', 'wrong', 'undefined'])
    df1.plot.bar(stacked=True, color=['#33691E', '#B71C1C', '#9E9E9E'], rot=0)
    plt.xlabel('Category')
    plt.ylabel('Classification result')

    f1 = BytesIO()
    plt.savefig(f1, format='png')
    f1.seek(0)
    d1 = f1.getvalue()
    d1 = base64.b64encode(d1)

    f1.flush()
    plt.cla()
    plt.clf()

    ###
    yes_sort = sorted(yes_category.items(), key=lambda (k, val): (-val, k))
    c2 = OrderedDict(islice(OrderedDict(yes_sort).items(), 5))

    arr2 = [round(confidence[c2.items()[i][0]]/c2.items()[i][1], 2) for i in range(5)]
    label2 = [c2.items()[i][0][:6] for i in range(5)]

    df2 = DataFrame(arr2, label2)
    df2.plot.bar(legend=False, color='#FF5722', rot=0)
    plt.xlabel('Category')
    plt.ylabel('Classification confidence')

    f2 = BytesIO()
    plt.savefig(f2, format='png')
    f2.seek(0)
    d2 = f2.getvalue()
    d2 = base64.b64encode(d2)

    f2.flush()
    plt.cla()
    plt.clf()

    return render_template('stats_view.html', stats=stats, category=category_sort, classification=yes_sort, path1=d1,
                           path2=d2, path3=d3)


if __name__ == '__main__':
    app.run()

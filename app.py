from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV
import pandas as pd
import os
from sklearn.svm import SVR
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import csv
import re
import matplotlib.pyplot as plt

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import pymysql

db = pymysql.connect(host='localhost', user='root',
                     password='1234', db='electricity')
cursor = db.cursor()

app = Flask(__name__)
current_directory = os.path.dirname(__file__)
uploads_directory = os.path.join(current_directory, 'uploads')
app.config['UPLOAD_FOLDER'] = uploads_directory


def future_forecast(x_train, model):
    window_size = 5
    future_predictions = {}

    for feature in x_train.columns:
        moving_avg = x_train[feature].rolling(window=window_size).mean()
        future_predictions[feature] = moving_avg.iloc[-1]

    forecast_df = pd.DataFrame(future_predictions, index=[x_train.index[-1]])
    print(forecast_df)
    pred2 = model.predict(forecast_df)
    print(pred2)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/load data', methods=["POST", "GET"])
def load_data():
    if request.method == "POST":
        f = request.files['file']
        filetype = os.path.splitext(f.filename)[1]
        print(filetype)
        if filetype == '.csv':
            mypath = os.path.join(app.config['UPLOAD_FOLDER'], f.filename)
            f.save(mypath)
            print(mypath)
            df = pd.read_csv(mypath)
            type(df)
            df.drop(['Unnamed: 0'], axis=1, inplace=True)
            print(df)
            s = mypath
            sql = "Truncate table tablename1"
            cursor.execute(sql)
            db.commit()
            sql = "INSERT INTO tablename1 ("
            for col in df.columns.values:
                query = f"{col}, "
                sql = sql + query
            sql = sql[:-2] + ") values (" + ('%s, ' * 10)
            sql = sql[:-2] + ")"
            for row in df.iterrows():
                val = [str(row[1][i]) for i in range(len(row[1]))]
                cursor.execute(sql, tuple(val))
            db.commit()

            return render_template('load data.html', msg='success')
        elif filetype != '.csv':
            return render_template('load data.html', msg='invalid')
    return render_template('load data.html')


@app.route('/view data')
def view_data():
    data = pd.read_sql_query('SELECT * FROM tablename1', db)
    data.drop(['id'], axis=1, inplace=True)
    return render_template('view data.html', msg='data', data=data, col_name=data.columns.values, row_val=data.values.tolist())


@app.route('/model', methods=["POST", "GET"])
def model():
    # if a>0:
    if request.method == 'POST':
        selected = int(request.form['selected'])
        global df
        testsize = 0.2
        filename = 'cleaned_data.csv'
        # global df
        df = pd.read_csv(os.path.join(
            app.config['UPLOAD_FOLDER'], filename))

        df.drop("Unnamed: 0", axis=1, inplace=True)
        X = df.drop(['priceactual'], axis=1)
        y = df['priceactual']

        global x_train, x_test, y_train, y_test
        x_train, x_test, y_train, y_test = train_test_split(
            X, y, test_size=testsize, random_state=10)
        if (selected == 1):
            rfr = RandomForestRegressor(n_estimators=50, max_depth=14)
            model1 = rfr.fit(x_train, y_train)
            pred1 = model1.predict(x_test)
            mae = mean_absolute_error(y_test, pred1)
            mse = mean_squared_error(y_test, pred1)
            score = r2_score(y_test, pred1)
            plt.scatter(y_test, pred1)
            plt.xlabel('Actual Cost')
            plt.ylabel('Predicted Cost')
            plt.title('Actual vs Predicted Cost')
            # plt.show
            future_forecast(x_train, model1)
            return render_template('model.html', msg='accuracy', mae=round(mae, 2), mse=round(mse, 2),  result=round(score, 4),  selected='RANDOM FOREST REGRESSOR')
        if (selected == 2):
            xgbr = xgb.XGBRegressor(learning_rate=0.4, n_estimators=200)
            model2 = xgbr.fit(x_train, y_train)
            pred2 = model2.predict(x_test)
            mae = mean_absolute_error(y_test, pred2)
            mse = mean_squared_error(y_test, pred2)
            score = r2_score(y_test, pred2)
            plt.scatter(y_test, pred2)
            plt.xlabel('Actual Cost')
            plt.ylabel('Predicted Cost')
            plt.title('Actual vs Predicted Cost')
            # plt.show
            future_forecast(x_train, model2)
            return render_template('model.html', msg='accuracy', mae=round(mae, 2), mse=round(mse, 2), result=round(score, 4), selected='XGBOOST REGRESSOR')
    return render_template('model.html')


@app.route('/registration', methods=["POST", "GET"])
def registration():
    if request.method == "POST":

        name = request.form['name']
        email = request.form['email']
        pwd = request.form['pwd']
        cpwd = request.form['cpwd']
        phno = request.form['phno']
        # print('sss')
        if pwd == cpwd:
            global sql
            sql = "select * from registration where name = '%s' and email='%s'" % (
                name, email)
            print(sql)
            a = cursor.execute(sql)
            # print(a)
            if (a > 0):
                return render_template('registration.html', msg='invalid')
            else:
                sql = "insert into registration(name,email,pwd,phno) values (%s,%s,%s,%s)"
                print(sql)
                # print('GHGH')
                val = (name, email, pwd, phno)
                # print('OIJO')
                cursor.execute(sql, val)
                # print('kjjh')
                db.commit()
                # print('lkjh')
                return render_template('registration.html', msg='success')
        else:
            return render_template('registration.html', msg='mismatch')
    return render_template('registration.html')


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == 'POST':
        name = request.form['name']
        pwd = request.form['pwd']
        sql = "select * from registration where name = '%s' and pwd='%s'" % (
            name, pwd)

        a = cursor.execute(sql)

        if a > 0:
            return render_template('index1.html')
        else:
            return render_template('login.html', msg='invalid')
    return render_template('login.html')


@app.route('/admin', methods=["POST", "GET"])
@app.route('/index1')
def index():
    return render_template('index1.html')


@app.route('/prediction', methods=['POST', 'GET'])
def prediction():
    # if a>0:
    if request.method == "POST":
        gfg = request.form['gfg']
        gfhc = request.form['gfhc']
        ghpsc = request.form['ghpsc']
        ghwr = request.form['ghwr']
        gor = request.form['gor']
        gw = request.form['gw']
        tlf = request.form['tlf']
        tla = request.form['tla']
        time = request.form['time']
        values = [[float(gfg), float(gfhc), float(ghpsc), float(ghwr), float(
            gor), float(gw), float(tlf), float(tla), float((time))]]
        xgbr = xgb.XGBRegressor(learning_rate=0.4, n_estimators=200)
        model = xgbr.fit(x_train, y_train)
        df_pred = pd.DataFrame(values[0], index=x_test.columns).transpose()
        pred = model.predict(df_pred)
        # score = r2_score(y_test, pred)
        return render_template('prediction.html', msg='success', result=pred)
    return render_template('prediction.html')


@app.route('/logout')
def logout():
    return render_template('logout.html')


@app.route('/view users')
def view_users():
    print('lkmn')
    sql1 = "select * from  registration"
    cursor.execute(sql1)
    data = cursor.fetchall()
    print(data)
    df = pd.read_sql_query(sql1, con=db)
    g = re.split(',', data)
    print(g)
    d = pd.DataFrame(g, columns=['id', 'name', 'email', 'pwd', 'phno'])
    return render_template('view users.html', table=d)


if __name__ == ('__main__'):
    app.run(debug=True)

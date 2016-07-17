# coding:utf-8
__author__ = 'Tacey Wong'

"""
！！！注意！！！
由于实际业务需求，每次的任务不会超过50个，
业务过于密集的话本应用将不再适用！
"""



import sys
import os

#######解决posixpath.py 的编码错误###
reload(sys)
sys.setdefaultencoding("utf-8")
#######################################

from flask import Flask, render_template, url_for, redirect, jsonify, request, g, session, flash
from werkzeug.utils import secure_filename
from flask import send_from_directory
from datetime import datetime
import sqlite3
import time,datetime
from threading import Thread
import gl
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import random

ALLOWED_EXTENSIONS = set(['csv', 'xls', 'jpg'])

app = Flask(__name__)

app.config.from_object(__name__)
app.config['DATABASE'] = gl.DATABASE
app.config['DOWNNLOAD_FOLDER'] = gl.DOWNNLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
app.secret_key = 'Tacey-Wong'


# from datetime import timedelta
# session.permanent = True
# app.permanent_session_lifetime = timedelta(minutes=5)
# session['key'] = value




def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


# 用户名和密码控制
@app.route('/login/control', methods=['GET', 'POST'])
def control():
    print 'get post '
    if request.method == 'POST':
        username = request.form['email']
        print type(username)
        if username.strip() == 'admin@admin.com':
            session['usertype'] = 1
        else:
            session['usertype'] = 0
            print '222222'
        session['username'] = username
        session['logged_in'] = True
        return redirect(url_for('showMain'))  # render_template("index.html")
        # return jsonify(status="success")
    else:
        return redirect(url_for('login'))  # render_template('login.html')


# 渲染登陆页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('showMain'))
    return render_template('login.html')


# 登出操作
@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


# 控制面板，主界面
@app.route('/')
def showMain():
    # 检测用户是否登录及用户类型
    if session.get('logged_in'):
        if session['usertype'] == 1:
            usertype = "Admin"
        elif session['usertype'] == 0:
            usertype = "Standart User"
        else:
            redirect(url_for('login'))

        # 将数据传递给模板文件，并渲染
        return render_template('index.html',
                               username=session['username'])

    else:
        return redirect(url_for('login'))


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            url_list = set([url for url in file.readlines()])
            db = get_db()
            jobname = datetime.datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S-%f')
            print jobname
            cur = db.execute('insert into job (username, jobname) values (?, ?)',
                 [session['username'], jobname])
            values = [(jobname,url) for url in url_list]
            cur.executemany('insert into detail (jobname,itemurl)VALUES (?, ?)', values)
            db.commit()

    return redirect(url_for('showMain'))


@app.route('/downloads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/get_job_list')
def get_job_list():
    if session['logged_in']:
        db = get_db()
        cur = db.execute('select jobname, status from job order by jobname desc')
        entries = cur.fetchall()
        job_list=[]
        for i in range(6):
            jobname= datetime.datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S-%f')
            status = random.randint(0,100)
            job_list.append({"jobname":jobname,"status":status})
        print str(job_list).replace("'",'"')
        return str(job_list).replace("'",'"')



def async(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()
    return wrapper

@async
def async_worker():
    pass

@app.route("/test")
def test():
    import random
    num = random.randint(1,100)
    return jsonify({"jobname":"Tacey","num":num})


if __name__ == '__main__':
    #初始化数据库
    init_db()
    #开启异步服务
    async_worker()
    #开启Web服务
    app.run(debug=True,host='0.0.0.0')
    # print test()
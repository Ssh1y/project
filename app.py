import json
import sqlite3
import re
import os
import pytz
import time
from datetime import datetime

from flask import Flask, redirect, render_template, request, session, url_for

# from IoT_device.client.IoT_client_config import IoTClientConfig
# from IoT_device.client.IoT_client import IotClient

app = Flask(__name__)
app.secret_key = "its_a_secret"
db_path = './huawei.db'


# server_ip = 'iot-mqtts.cn-north-4.myhuaweicloud.com'
# device_id = 'Ssh1y_s_device1'
# secret = '8ZpuGtN7WWXxQyn'
# client_cfg = IoTClientConfig(
#     server_ip=server_ip,
#     device_id=device_id,
#     secret=secret,
#     is_ssl=True)
# iot_client = IotClient(client_cfg)


def insert(table, *args):
    """
    :param table: 操作的表
    :param args: 输入的value，以逗号隔开
    :return:返回插入的结果
    """
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # 插入单条语句
        if table == 'users':
            values = '(username,dev_name)'
        elif table == 'sub_history':
            values = '(test_id,test_name,status,sub_time,username)'
        elif table == 'test_dbs':
            values = '(test_name,test_desc,difficulty)'
        else:
            return False

        insert_sql = """insert into {}{} values{};""".format(
            table, values, args)
        print(insert_sql)

        cur.execute(insert_sql)
        print("成功插入{}条语句".format(cur.rowcount))
        conn.commit()
        return True
    except Exception as e:
        print(str(e))
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def delete(table, where):
    """
    :param table: 操作的表
    :param where: 条件
    :return: 返回删除结果
    """
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        delete_sql = """delete from {} where {}""".format(table, where)
        print(delete_sql)
        cur.execute(delete_sql)
        conn.commit()
        return True
    except Exception as e:
        print(str(e))
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def update(table, operate, where):
    """
    :param table: 操作的表
    :param operate: 执行的操作
    :param where: 条件
    :return: 返回更新结果
    """
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        update_sql = """update {} set {} where {}""".format(table, operate, where)
        print(update_sql)
        cur.execute(update_sql)
        conn.commit()
        return True
    except Exception as e:
        print(str(e))
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def select(table, where="1=1", order="", limit=""):
    """
    :param table: 操作的表
    :param where: 条件
    :param order: 排序
    :param limit: 限制结果数量
    :return: 返回为一个列表，列表内为元组。[(),(),...]
    """
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        select_sql = """select * from {} where {} {} {}""".format(table, where, order, limit)
        print(select_sql)
        cur.execute(select_sql)
        conn.commit()
        return cur.fetchall()
    except Exception as e:
        print(str(e))
    finally:
        cur.close()
        conn.close()


def check_login():  # 检查是否登陆
    if "username" not in session:
        return False
    return True


def anti_sql_injection(var):  # 防止sql注入，将除了数字字母下划线以外的字符都替换成空
    return re.sub(r"\W", "", var)


@app.route("/", methods=["GET"])
@app.route("/index", methods=["GET"])
def index():
    # global iot_client
    if not check_login():
        return redirect(url_for('register'))
    # 连接华为云
    # if not iot_client.is_connected():
    #     iot_client.connect()
    #     iot_client.start()
    records = []
    name = ["id", "test_id", "test_name", "status", "sub_time", "username"]
    r = select("sub_history", "1=1", "order by sub_time desc", "limit 0,5")
    for i in range(len(r)):
        records.append(dict(zip(name, list(r[i]))))
    return render_template("index.html", records=records)


@app.route("/register", methods=["POST", "GET"])
def register():
    msg = ''
    if request.method == "POST":
        username = anti_sql_injection(request.form["username"])
        dev_name = anti_sql_injection(request.form["dev_name"])
        device_ip = request.form["device_ip"]
        print(username, dev_name, device_ip)
        r = select("users", "username='{}' and dev_name='{}'".format(username, dev_name))
        if len(r) == 0:
            if len(select("users", "dev_name = '{}'".format(dev_name))) > 0:
                msg = '该设备已被其他用户绑定！'
                print(msg)
            else:
                if len(select("users", "username = '{}'".format(username))) > 0:
                    update("users", "dev_name = '{}'".format(dev_name), "username = '{}'".format(username))
                else:
                    insert("users", username, dev_name)
        if len(r) > 0 or msg == '':
            session["username"] = username
            session["device_ip"] = device_ip

    if "username" in session:
        print(session)
        return redirect(url_for('index'))
    return render_template('register.html', msg=msg)


@app.route("/test_db", methods=["GET"])
def test_db():
    tests = []
    name = ["test_id", "test_name", "test_desc", "difficulty", "total_num", "correct_num", "ac_rate", "color", "status"]
    key = request.args.get('key')
    # print(key)
    if key is None:
        r = select("test_dbs", "1=1")
    else:
        r = select("test_dbs", "test_id LIKE '%{}%' or test_name LIKE '%{}%'".format(key, key))
    for i in range(len(r)):
        t = list(r[i])
        if t[5] == 0:
            t.append(format(float(0), '.2f'))
        else:
            t.append(format(float(t[5] / t[4]), '.2f'))
        if t[3] == 1:
            t.append("table-primary")
        elif t[3] == 2:
            t.append("table-success")
        elif t[3] == 3:
            t.append("table-info")
        elif t[3] == 4:
            t.append("table-warning")
        else:
            t.append("table-danger")
        if "username" in session:
            rc = select("sub_history",
                        "test_id={} and username='{}' and status = '{}'".format(t[0], session["username"], "正确"))
            rw = select("sub_history",
                        "test_id={} and username='{}' and status = '{}'".format(t[0], session["username"], "错误"))
            if len(rc) != 0:
                t.append("已答对")
            elif len(rw) != 0:
                t.append("已尝试")
            else:
                t.append("未尝试")
        else:
            t.append("未尝试")
        tests.append(dict(zip(name, list(t))))
    return render_template("test_db.html", tests=tests)


@app.route("/submit_history", methods=["GET"])
def submit_history():
    if not check_login():
        return redirect(url_for('register'))
    records = []
    username = session["username"]
    name = ["id", "test_id", "test_name", "status", "sub_time", "username"]
    r = select("sub_history", "username='{}'".format(username), "order by sub_time desc")
    for i in range(len(r)):
        records.append(dict(zip(name, list(r[i]))))
    return render_template("submit_history.html", records=records)


@app.route("/test/<test_id>")
def test(test_id):
    if not check_login():
        return redirect(url_for('register'))
    test_id = int(test_id)
    ip = session["device_ip"]
    r = select("test_dbs", "test_id={}".format(test_id))
    if len(r) == 1:
        title = r[0][1]
        description = r[0][2]
        return render_template("test.html", title=title, description=description, test_id=test_id, device_ip=ip)
    return "Something Wrong!"


@app.route("/upload_test", methods=["POST", "GET"])
def upload_test():
    if not check_login():
        return redirect(url_for('register'))
    if session["username"] != "nimda":
        return "您无此权限!"
    if request.method == "POST":
        try:
            test_name = request.form["test_name"]
            test_desc = request.form["test_desc"]
            new_test_difficulty = request.form["new_test_difficulty"]
            file = request.files.get("input_file")
            if insert("test_dbs", test_name, test_desc, new_test_difficulty):
                test_id = select("test_dbs", "test_name='{}' and test_desc='{}'".format(test_name, test_desc))[0][0]
                new_filename = r'static/answer/{}.json'.format(test_id)
                file.save(new_filename)
                return "<script>alert('添加成功！');window.location.href='/upload_test'</script>"
        except Exception as e:
            print(str(e))
            return "<script>alert('添加失败！');window.location.href='/upload_test'</script>"

    return render_template("upload.html")


@app.route("/help")
def help_():
    return render_template("help.html")


@app.route("/get_answer/<test_id>")
def get_answer(test_id):
    if test_id is None:
        return "Error!"
    return redirect(url_for('static', filename='answer/{}.json'.format(test_id)))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route("/init_all")
def init_all():
    # 删除所有题目
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        sql_s = ["""drop table users""",
                 """drop table test_dbs""",
                 """drop table sub_history""",
                 """CREATE TABLE if not exists users(
                        id integer primary key autoincrement,
                        username varchar(20) not null,
                        dev_name varchar(20) not null
                );""",
                 """CREATE TABLE if not exists sub_history(
                        id integer primary key autoincrement,
                        test_id integer not null,
                        test_name varchar(20) not null,
                        status varchar(10) not null,
                        sub_time date,
                        username varchar(20) not null
                );""",
                 """CREATE TABLE if not exists test_dbs(
                        test_id integer primary key autoincrement,
                        test_name varchar(20) not null,
                        test_desc varchar(100) not null,
                        difficulty integer not null,
                        total_num integer default 0,
                        correct_num integer default 0
                );"""
                 ]
        for sql in sql_s:
            print(sql)
            cur.execute(sql)

        filepath = "static/answer/"
        del_list = os.listdir(filepath)
        for f in del_list:
            file_path = os.path.join(filepath, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
        session.clear()

    except Exception as e:
        print(str(e))
        conn.rollback()
    finally:
        cur.close()
        conn.close()
        return redirect(url_for('index'))


@app.route("/Data_Analyse", methods=["POST"])
def data_analyse():
    try:
        res = json.loads(request.get_data())
        dev_name = anti_sql_injection(res["notify_data"]["body"]["services"][0]["properties"]["dev_name"])
        status = res["notify_data"]["body"]["services"][0]["properties"]["status"]
        if str(status) == '1':
            status = '正确'
            s = "total_num=total_num+1,correct_num=correct_num+1"
        else:
            status = '错误'
            s = "total_num=total_num+1"
        test_id = int(res["notify_data"]["body"]["services"][0]["properties"]["id"])
        now = datetime.fromtimestamp(int(time.time()),
                                     pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        username = select("users", "dev_name='{}'".format(dev_name))[0][1]
        test_name = select("test_dbs", "test_id={}".format(test_id))[0][1]
        if insert("sub_history", test_id, test_name, status, now, username) \
                and update("test_dbs", s, "test_id={}".format(test_id)):
            return "提交成功！"
    except Exception as e:
        print(e)
        return "提交失败"


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)

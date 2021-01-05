from flask import Flask, request  # 导入Flask类
from re import *
import pymysql
from flaskext.mysql import MySQL
import random
import smtplib    
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import json
import logging
import urllib
import smtplib
import socket
from enum import Enum

app = Flask(__name__)  # 实例化Flask对象
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '12345678'
app.config['MYSQL_DATABASE_DB'] = 'pkutodo'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

types = ['set_up', 'verify', 'login', 'add_task', 'del_task', 'del_list', 'finish_task',
         'find', 'join', 'handle', 'assignment', 'transfer']
new_user_list = []  # 存储在注册过程中的用户类实例
verify_code = []


class MessageType():
    """
    消息类型枚举类
    """
    set_up = 'set_up'
    verify = 'verify'
    login = 'login'
    refresh='refresh'
    add_task = 'add_task'
    del_task = 'del_task'
    del_list = 'del_list'
    finish = 'finish'
    find_list = 'find_list'
    join = 'join'
    handle = 'handle'
    assignment = 'assignment'
    find_member = 'find_member'
    transfer = 'transfer'


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))
class User():
    """
    用户类
    """

    def __init__(self, name, email, password, create=False, id=-1):
        self.id = id
        self.name = name
        self.email = email
        self.password = password


def jsonencoder(ifsuccess, response=""):
    return json.dumps({"success": 1}) if ifsuccess else json.dumps({"error": 1, "error_msg": response})

@app.route("/", methods=["POST", "GET"])  # app中的route装饰器
def respond():  # 视图函数
    print(request.values)
    data = request.values.to_dict()
    if request.method == 'POST':
        try:
            if(data['type'] == MessageType.set_up):
                print(data['type'])
                verify_code.append((data['email'], random.randint(1000, 9999)))
                print(data['email'],verify_code[-1])
                # 第三方 SMTP 服务
                mail_host="smtp.163.com"  #设置服务器
                mail_user="pkutodo@163.com"   #用户名
                mail_pass="ENRHVYHFKAKADNUG"   #口令 
                
                
                sender = 'pkutodo@163.com'
                receivers = [data['email']]  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱

                msg = MIMEText('你好，亲爱的同学,以下是您的PKUTODO注册验证码。\n %s'%verify_code[-1][-1], 'plain', 'utf-8')
                msg['From'] = _format_addr('PKUTODO <%s>' % sender)
                msg['To'] = _format_addr('%s <%s>' % ('张维昱', data['email']))
                msg['Subject'] = Header("PKUTODO注册验证码", 'utf-8').encode()

                try:
                    smtpObj = smtplib.SMTP() 
                    smtpObj.connect(mail_host,25)    # 25 为 SMTP 端口号
                    smtpObj.login(mail_user,mail_pass) 
                    #smtpObj.sendmail(sender, receivers, message.as_string())
                    print(receivers)
                    smtpObj.sendmail(sender, receivers,msg.as_string())

                    print ("邮件发送成功")
                    return  jsonencoder(1, "email send")
                except smtplib.SMTPException as e:
                    print (e)
                    return jsonencoder(0, "Error: 无法发送邮件")
            elif data['type'] == MessageType.verify:
                try:
                    user = User(data['name'],
                                    data['email'], data['password'],True)
                    print("verifycode:" ,data['verify_code'])
                    for email, code in list(reversed(verify_code)):
                        if (email.lower() == user.email.lower() and str(code) == data['verify_code']):
                            print("Verify code matched.")
                            cur = mysql.get_db().cursor()
                            print(
                                "INSERT INTO pkutodo.user (`name`,`email`,`password`) VALUES ('{name}', '{email}', '{password}');".\
                                    format(email=user.email,
                                           name=user.name,
                                           password=user.password
                                    ))
                            cur.execute(
                                "INSERT INTO pkutodo.user (`name`,`email`,`password`) VALUES ('{name}', '{email}', '{password}');".\
                                    format(email=user.email,
                                           name=user.name,
                                           password=user.password
                                    ))
                            mysql.get_db().commit()
                            cur.close()
                            return jsonencoder(1, "set up success")
                        elif (email == user.email) :
                            return jsonencoder(0, "set up fail")
                        return jsonencoder(0, "no such user to set up")
                except Exception as e:
                    return jsonencoder(0, "unknown failure")
            elif data['type'] == MessageType.login:
                # print("!!!!")
                try:
                    cur = mysql.get_db().cursor()
                    print(
                        "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".\
                            format(email=data['email'],password=data['password']))
                    cur.execute(
                        "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".\
                            format(email=data['email'],password=data['password']))
                    #mysql.get_db().commit()
                    user_=cur.fetchall()
                    cur.close()
                    user_info={}
                    user_info['user_id']=user_[0][0]
                    user_info['password']=data['password']
                    user_info['success']=1
                    user_j=json.dumps(user_info)
                    return user_j
                except:
                    return jsonencoder(0, 'not existing user or wrong password')
            elif data['type'] == MessageType.refresh:
                cur = mysql.get_db().cursor()
                #验证登录
                try:
                    cur.execute(
                    "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".\
                        format(email=data['email'],password=data['password']))
                except:
                    return jsonencoder(0, 'not existing user or wrong password')
                objects_list = []
                cur.execute(
                    "SELECT * FROM pkutodo.list WHERE admin_id='{id}';".format(id=data['user_id']))
                results = cur.fetchall()
                for row in results:
                    d = collections.OrderedDict()
                    d['list_id']=results[0]
                    d['admin_id']=results[1]
                    d['is_public']=results[2]
                    d['list_name']=results[3]
                    objects_list.append(d)
                cur.execute(
                    "SELECT * FROM pkutodo.task WHERE user_id='{id}';".format(id=data['user_id']))
                results = cur.fetchall()
                for row in results:
                    d = collections.OrderedDict()
                    d['task_id']=results[0]
                    d['user_id']=results[1]
                    d['list_id']=results[2]
                    d['task_name']=results[3]
                    d['content']=results[4]
                    d['create_date']=results[5]
                    d['due_date']=results[6]
                    d['position_x']=results[7]
                    d['position_y']=results[8]
                    d['is_finished']=results[9]
                    objects_list.append(d)
                j = json.dumps(objects_list)
                cur.close()
                return j
            elif data['type'] == MessageType.del_list:
                cur = mysql.get_db().cursor()
                #验证登录
                try:
                    cur.execute(
                    "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".\
                        format(email=data['email'],password=data['password']))
                except:
                    return jsonencoder(0, 'not existing user or wrong password')
                print("DELETE FROM list WHERE id = {}".format(data['list_id']))
                cur.execute(
                    "DELETE FROM list WHERE id = {}".format(data['list_id']))
                mysql.get_db().commit()
                cur.close()
            elif data['type'] == MessageType.del_task:
                cur = mysql.get_db().cursor()
                print("DELETE FROM task WHERE id = {task_id} and user_id = {user_id}".format(
                    task_id=data['task_id'], user_id=data['user_id']))
                try:
                    cur.execute(
                        "DELETE FROM task WHERE id = {task_id} and user_id = {user_id}".format(task_id=data['task_id'], user_id=data['user_id']))
                    mysql.get_db().commit()
                except:
                    return jsonencoder(0, "Cannot Delete. Please check task id")
                cur.close()
                return jsonencoder(1, 'success')
            elif data['type'] == MessageType.finish:
                cur = mysql.get_db.cursor()
                print(
                    "UPDATE task set is_finished = {state} where user_id = {user_id} and id = {task_id}".format(state=data['state'],user_id=data['user_id'], task_id=data['task_id'])
                )
                try:
                    cur.execute(    
                        "UPDATE task set is_finished = {state} where user_id = {user_id} and id = {task_id}".format(state=data['state'],user_id=data['user_id'], task_id=data['task_id'])
                    )
                    mysql.get_db().commit()
                except:
                    return jsonencoder(0, "Update Failed. Please check")
                cur.close()
                return jsonencoder(1, 'success')
            elif data['type'] == MessageType.assignment:
                cur = mysql.get_db.cursor()
                print(
                    "INSERT INTO task(user_id, list_id, name, content, create_date, due_date, pos_x, pos_y)"+
                    "VALUES({user_id}, {list_id}, {task_name}, {content}, {create_date}, {due_date}, {position_x}, {position_y})".format(
                        list_id=data['list_id'],
                        user_id=data['user_id'],
                        task_name=data['task_name'],
                        content=data['content'],
                        create_date=data['create_date'],
                        due_date=data['due_date'],
                        position_x=data['position_x'],
                        position_y=data['position_y']
                        )
                )
                try:
                    cur.execute(
                    "INSERT INTO task(user_id, list_id, name, content, create_date, due_date, pos_x, pos_y)"+
                    "VALUES({user_id}, {list_id}, {task_name}, {content}, {create_date}, {due_date}, {position_x}, {position_y})".format(
                        list_id=data['list_id'],
                        user_id=data['user_id'],
                        task_name=data['task_name'],
                        content=data['content'],
                        create_date=data['create_date'],
                        due_date=data['due_date'],
                        position_x=data['position_x'],
                        position_y=data['position_y']
                        )
                    )
                    mysql.get_db().commit()
                except:
                    return jsonencoder(0, 'Insert Failed. Please check')
                cur.close() 
                return jsonencoder(1, 'success')
            elif data['type'] == MessageType.join:
                cur = mysql.get_db.cursor()
                print(
                    "INSERT INTO class_member VALUES({list_id}, {user_id})".format(
                        list_id=data['list_id'],
                        user_id=data['user_id']
                    )
                )
                try:
                    cur.execute(
                        "INSERT INTO class_member VALUES({list_id}, {user_id})".format(
                            list_id=data['list_id'],
                            user_id=data['user_id']
                        )
                    )
                    mysql.get_db().commit()
                except:
                    return jsonencoder(0, "Joining class Failed. Please check")
                cur.close()
                return jsonencoder(1, "success")
            elif data['type'] == MessageType.find_list:
                cur = mysql.get_db.cursor()
                print(
                    "SELECT * FROM list where name LIKE '\%{keyword}\%'".format(
                        keyword=data['keyword']
                    )
                )
                objects_list = []
                try:
                    cur.execute(
                        "SELECT * FROM list where name LIKE '\%{keyword}\%'".format(
                            keyword=data['keyword']
                        )
                    )
                    mysql.get_db().commit()
                    results = cur.fetchall()
                    for row in results:
                        d = collections.OrderedDict()
                        d['list_id']=results[0]
                        d['admin_id']=results[1]
                        d['is_public']=results[2]
                        d['list_name']=results[3]
                        objects_list.append(d)
                except:
                    return jsonencoder(0, "Selection failed. Please check.")
                cur.close()
                return json.dumps(objects_list)
            elif data['type'] == MessageType.find_member:
                cur = mysql.get_db.cursor()
                print(
                    "SELECT * FROM class_member where list_id = {list_id}".format(
                        list_id=data['list_id']
                    )
                )
                objects_list = []
                try:
                    cur.execute(
                        "SELECT * FROM class_member where list_id = {list_id}".format(
                            list_id=data['list_id']
                        )
                    )
                    mysql.get_db().commit()
                    results = cur.fetchall()
                    for row in results:
                        d = collections.OrderedDict()
                        d['list_id']=results[0]
                        d['admin_id']=results[1]
                        d['is_public']=results[2]
                        d['list_name']=results[3]
                        objects_list.append(d)
                except:
                    return jsonencoder(0, "Selection failed. Please check.")
                cur.close()
                return json.dumps(objects_list)    
            elif data['type'] == MessageType.transfer:
                cur = mysql.get_db.cursor()
                print(
                    "UPDATE list set admin_id = {target_user_id} where admin_id = {user_id} and list_id = {list_id}".format(
                        list_id=data['list_id'],
                        user_id=data['user_id'],
                        target_user_id=data['target_user_id']
                    )
                )
                try:
                    cur.execute(
                        "UPDATE list set admin_id = {target_user_id} where admin_id = {user_id} and list_id = {list_id}".format(
                            list_id=data['list_id'],
                            user_id=data['user_id'],
                            target_user_id=data['target_user_id']
                        )
                    )
                    mysql.get_db().commit()
                except:
                    return jsonencoder(0, "Admin transfer failed. Please check.")
                cur.close()    
                return jsonencoder(1, 'success')
            else: return jsonencoder(0, "wrong")
        except:
            return jsonencoder(0, "wrong type")
    else:
        return "Hello World"


@app.route("/req", methods=["POST", "GET"])
def req():
    print(request.method)
    print(request.values.to_dict())
    return "hello"


@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return 'User %s' % escape(username)


# 监听地址为0.0.0.0,表示服务器的所有网卡
# 5000是监听端口
# debug=True表示启动debug模式。当代码有改动时,Flask会自动加载,无序重启！
app.run("0.0.0.0", 5000, debug=True)  # 启动Flask服务
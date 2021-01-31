
from flask import Flask, request  # 导入Flask类
from re import *
from flask.helpers import send_from_directory
from flaskext.mysql import MySQL
import random
import imaplib
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import os, copy, traceback, collections, smtplib, json
from config import * # 导入配置
import json
import datetime




app = Flask(__name__)  # 实例化Flask对象
app.config['MYSQL_DATABASE_USER'] = 'pkutodo'
app.config['MYSQL_DATABASE_PASSWORD'] = '12345678'
app.config['MYSQL_DATABASE_DB'] = 'pkutodo'
app.config['MYSQL_DATABASE_HOST'] = '127.0.0.1'

mysql = MySQL()
mysql.init_app(app)

new_user_list = []  # 存储在注册过程中的用户类实例
verify_code = []

class MessageType():
    """
    消息类型枚举类
    """
    set_up = 'set_up'
    verify = 'verify'
    login = 'login'
    refresh = 'refresh'
    add_task = 'add_task'
    add_list = 'add_list'
    modify_task = 'modify_task'
    modify_list = "modify_list"
    del_task = 'del_task'
    del_list = 'del_list'
    finish = 'finish'
    find_list = 'find_list'
    join = 'join'
    handle = 'handle'
    assignment = 'assignment'
    find_member = 'find_member'
    transfer = 'transfer'
    quit_class = 'quit_class'


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

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj,datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return json.JSONEncoder.default(self,obj)

def jsonencoder(ifsuccess, response="", data=None):
    if ifsuccess:
        if data:
            return json.dumps({"success": 1, "data":data},cls=DateEncoder)
        else:
            return json.dumps({"success": 1},cls=DateEncoder)
    else:
        return json.dumps({"success": 0, "error_msg": response})

def get_task_id(cur, data):
    cur.execute(
                    "select id from task where user_id={user_id} and list_id={list_id} and name='{task_name}' and content='{content}' and \
                        create_date='{create_date}' and due_date='{due_date}' and pos_x={position_x} and pos_y={position_y}".format(
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
    test = cur.fetchall()
    return cur.fetchall()[0][-1]

def get_list_id(cur, data):
    cur.execute(
        "select id from list where admin_id={admin_id} and name='{list_name}'".format(
            admin_id=data['user_id'], list_name=data['list_name']
        )
    )
    mysql.get_db().commit()
    return cur.fetchall()[0][0]

@app.route("/", methods=["POST", "GET"])  # app中的route装饰器
def respond():  # 视图函数
    if request.method == 'POST':
        try:
            # print("request: {}". format(request.get_data(as_text=True)))
            data = json.loads(request.get_data(as_text=True))
            print(data)
            if(data['type'] == MessageType.set_up):
                print(data['type'])
                verify_code.append((data['email'], random.randint(1000, 9999)))
                print(data['email'], verify_code[-1])
                # 第三方 SMTP 服务
                mail_host = "smtp.163.com"  # 设置服务器
                mail_user = "pkutodo@163.com"  # 用户名
                mail_pass = "ENRHVYHFKAKADNUG"  # 口令
                
                sender = 'pkutodo@163.com'
                receivers = [data['email']]  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱

                msg = MIMEText('你好，亲爱的同学,以下是您的PKUTODO注册验证码。\n %s' %
                               verify_code[-1][-1], 'plain', 'utf-8')
                msg['From'] = _format_addr('PKUTODO <%s>' % sender)
                msg['To'] = _format_addr('%s <%s>' % ('张维昱', data['email']))
                msg['Subject'] = Header("PKUTODO注册验证码", 'utf-8').encode()

                try:
                    smtpObj = smtplib.SMTP_SSL(mail_host, 465)
                    # smtpObj.connect(mail_host, 465)    # 25 为 SMTP 端口号
                    smtpObj.login(mail_user, mail_pass)
                    #smtpObj.sendmail(sender, receivers, message.as_string())
                    print(receivers)
                    smtpObj.sendmail(sender, receivers, msg.as_string())

                    print("邮件发送成功")
                    return jsonencoder(1, "email send")
                except smtplib.SMTPException as e:
                    print(e)
                    return jsonencoder(0, "Error: 无法发送邮件")
            elif data['type'] == MessageType.verify:
                try:
                    user = User(data['name'],
                                data['email'], data['password'], True)
                    print("verifycode:", data['verify_code'])
                    for email, code in list(reversed(verify_code)):
                        if (email.lower() == user.email.lower() and str(code) == data['verify_code']):
                            print("Verify code matched.")
                            cur = mysql.get_db().cursor()
                            print(
                                "INSERT INTO pkutodo.user (`name`,`email`,`password`) VALUES ('{name}', '{email}', '{password}');".
                                format(email=user.email,
                                       name=user.name,
                                       password=user.password
                                       ))
                            cur.execute(
                                "INSERT INTO pkutodo.user (`name`,`email`,`password`) VALUES ('{name}', '{email}', '{password}');".
                                format(email=user.email,
                                       name=user.name,
                                       password=user.password
                                       ))
                            mysql.get_db().commit()
                            cur.close()
                            user_info={}
                            user_info["user_id"]=user.id
                            user_info["email"]=user.email
                            user_info["password"]=user.password
                            user_info["name"]=user.name
                            return jsonencoder(1, "set up success",user_info)
                        elif (email == user.email):
                            return jsonencoder(0, "set up fail")
                        return jsonencoder(0, "no such user to set up")
                except Exception as e:
                    return jsonencoder(0, "unknown failure")
            elif data['type'] == MessageType.login:
                try:
                    cur = mysql.get_db().cursor()
                    print(
                        "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".
                        format(email=data['email'], password=data['password']))
                    cur.execute(
                        "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".
                        format(email=data['email'], password=data['password']))
                    # mysql.get_db().commit()
                    user_ = cur.fetchall()
                    cur.close()
                    user_info = {}
                    user_info['user_id'] = user_[0][0]
                    user_info['password'] = data['password']
                    user_info['name']=user_[0][1]
                    user_info['email']=user_[0][2]
                    user_info['success'] = 1
                    # user_j = json.dumps(user_info)
                    user_j = jsonencoder(1, 'success', user_info)
                    return user_j
                except:
                    return jsonencoder(0, 'not existing user or wrong password')
            elif data['type'] == MessageType.refresh:
                cur = mysql.get_db().cursor()
                # 验证登录
                try:
                    cur.execute(
                        "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".
                        format(email=data['email'], password=data['password']))
                except:
                    return jsonencoder(0, 'not existing user or wrong password')

                list_list = [] # 来自用户
                task_list = [] # 来自用户
                class_list = [] # 所有课程
                cur.execute(
                    "SELECT * FROM pkutodo.list WHERE admin_id='{id}' UNION SELECT * FROM pkutodo.list WHERE id IN (SELECT list_id FROM pkutodo.class_member WHERE user_id = {id} ) ;".format(id=data['user_id']))
                results = cur.fetchall()
                for row in results:
                    d = collections.OrderedDict()
                    d['list_id'] = row[0]
                    d['admin_id'] = row[1]
                    d['is_public'] = row[2]
                    d['list_name'] = row[3]
                    list_list.append(d)
                
                cur.execute(
                    "SELECT * FROM pkutodo.task WHERE user_id='{id}';".format(id=data['user_id']))
                results = cur.fetchall()
                for row in results:
                    d = collections.OrderedDict()
                    d['task_id'] = row[0]
                    d['user_id'] = row[1]
                    d['list_id'] = row[2]
                    d['task_name'] = row[3]
                    d['content'] = row[4]
                    d['create_date'] = row[5]
                    d['due_date'] = row[6]
                    d['position_x'] = row[7]
                    d['position_y'] = row[8]
                    d['is_finished'] = row[9]
                    task_list.append(d)

                cur.execute(
                    "SELECT * FROM pkutodo.list WHERE is_public=1;"
                )
                results = cur.fetchall()
                for row in results:
                    d = collections.OrderedDict()
                    d['list_id'] = row[0]
                    d['admin_id'] = row[1]
                    d['is_public'] = row[2]
                    d['list_name'] = row[3]
                    class_list.append(d)

                object_dic={'list':list_list,'task':task_list, 'class':class_list}
                # j = json.dumps(objects_list)
                j = jsonencoder(1, 'success', data=object_dic)
                cur.close()
                return j
            elif data['type'] == MessageType.add_list:
                cur = mysql.get_db().cursor()
                # 验证登录
                try:
                    cur.execute(
                        "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".
                        format(email=data['email'], password=data['password']))
                except:
                    cur.close()
                    return jsonencoder(0, 'not existing user or wrong password')
                # print("INSERT INTO  list(admin_id, is_public, name) " +
                #       "VALUES ({admin_id}, {is_public}, '{list_name}')".format(
                #           admin_id=data['user_id'], is_public=0, list_name=data['list_name']))
                try:
                    cur.execute(
                        "INSERT INTO  list(admin_id, is_public, name) " +
                        "VALUES ({admin_id}, {is_public}, '{list_name}')".format(
                            admin_id=data['user_id'], is_public=0, list_name=data['list_name']))
                    
                    
                    list_id = get_list_id(cur, data)
                    mysql.get_db().commit()
                except Exception as e:
                    cur.close()
                    print(traceback.print_exc())
                    return jsonencoder(0, 'Create new list failed.')
                cur.close()
                return jsonencoder(1, 'success', data={'list_id':list_id})

            elif data['type'] == MessageType.add_task:
                cur = mysql.get_db().cursor()
                # 验证登录
                try:
                    cur.execute(
                        "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".
                        format(email=data['email'], password=data['password']))
                except:
                    cur.close()
                    return jsonencoder(0, 'not existing user or wrong password')

                try:
                    # 如果是admin才能对列表进行添加修改操作
                    cur.execute(
                        "SELECT admin_id, is_public from list where id={}".format(data['list_id']))
                    admin_id, is_public = cur.fetchall()[0]
                    print(admin_id, is_public)
                    if admin_id != data["user_id"]:
                        cur.close()
                        return jsonencoder(0, "No authority to change list")
                    task_id = 0
                    # 现在判断是不是class
                    # print(
                    #     "INSERT INTO task(user_id, list_id, name, content, create_date, due_date, pos_x, pos_y,is_finished)" +
                    #     "VALUES({user_id}, {list_id}, {task_name}, {content}, {create_date}, {due_date}, {position_x}, {position_y}, 0)".format(
                    #         list_id=data['list_id'],
                    #         user_id=data['user_id'],
                    #         task_name=data['task_name'],
                    #         content=data['content'],
                    #         create_date=data['create_date'],
                    #         due_date=data['due_date'],
                    #         position_x=data['position_x'],
                    #         position_y=data['position_y']
                    #     )
                    # )

                    if not is_public:
                        cur.execute(
                            "INSERT INTO task(user_id, list_id, name, content, create_date, due_date, pos_x, pos_y, is_finished)" +
                            "VALUES({user_id}, {list_id}, '{task_name}', '{content}', '{create_date}', '{due_date}', {position_x}, {position_y}, 0)".format(
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
                        attr = dict(
                            list_id=data['list_id'],
                            user_id=data['user_id'],
                            task_name=data['task_name'],
                            content=data['content'],
                            create_date=data['create_date'],
                            due_date=data['due_date'],
                            position_x=data['position_x'],
                            position_y=data['position_y']
                        )
                        mysql.get_db().commit()
                    else:  # Q: 为class时先插入一个userid为-1的task，再通过assignment进行分发。
                        cur.execute(
                            "INSERT INTO task(user_id, list_id, name, content, create_date, due_date, pos_x, pos_y, is_finished)" +
                            "VALUES({user_id}, {list_id}, '{task_name}', '{content}', '{create_date}', '{due_date}', {position_x}, {position_y}, 0)".format(
                                list_id=data['list_id'],
                                user_id=-1,
                                task_name=data['task_name'],
                                content=data['content'],
                                create_date=data['create_date'],
                                due_date=data['due_date'],
                                position_x=data['position_x'],
                                position_y=data['position_y']
                            )
                        )
                        attr = dict(
                            list_id=data['list_id'],
                            user_id=data['user_id'],
                            task_name=data['task_name'],
                            content=data['content'],
                            create_date=data['create_date'],
                            due_date=data['due_date'],
                            position_x=data['position_x'],
                            position_y=data['position_y']
                        )

                        mysql.get_db().commit()

                        cur.execute(
                        "SELECT user_id from class_member where list_id={}".format(data['list_id']))
                        users = cur.fetchall()
                        if len(users):
                            sql_string = "INSERT INTO task(user_id, list_id, name, content, create_date, due_date, pos_x, pos_y) Values"
                            for i in range(len(users)):
                                if i:
                                    sql_string += ","
                                sql_string += "({user_id}, {list_id}, '{task_name}', '{content}', '{create_date}', '{due_date}', {position_x}, {position_y})".format(
                                    list_id=data['list_id'],
                                    user_id=users[i][0],
                                    task_name=data['task_name'],
                                    content=data['content'],
                                    create_date=data['create_date'],
                                    due_date=data['due_date'],
                                    position_x=data['position_x'],
                                    position_y=data['position_y']
                                )
                                
                            cur.execute(sql_string)
                            mysql.get_db().commit()
                    task_id = get_task_id(cur, attr)
                except Exception as e:
                    cur.close()
                    print(traceback.print_exc())
                    return jsonencoder(0, 'Insert Failed. Please check')
                    
                cur.close()
                return jsonencoder(1, 'success', data={'task_id':task_id})

            elif data['type'] == MessageType.modify_list:
                cur = mysql.get_db().cursor()
                # 验证登录
                try:
                    cur.execute(
                        "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".
                        format(email=data['email'], password=data['password']))
                except:
                    cur.close()
                    return jsonencoder(0, 'not existing user or wrong password')

                try:
                    # 如果是admin才能对列表进行添加修改操作
                    cur.execute(
                        "SELECT admin_id from list where id={}".format(data['list_id']))
                    admin_id = cur.fetchall()[0][0]
                    if admin_id != data["user_id"]:
                        cur.close()
                        return jsonencoder(0, "No authority to change list")

                    cur.execute("UPDATE list set name='{list_name}' where id={list_id}".format(
                        list_name=data['list_name'], list_id=data['list_id']))
                    mysql.get_db().commit()
                except:
                    cur.close()
                    # print(traceback.print_exc())
                    return jsonencoder(0, 'Modifying failed.')
                cur.close()
                return jsonencoder(1, 'success')

            elif data['type'] == MessageType.modify_task:
                cur = mysql.get_db().cursor()
                # 验证登录
                try:
                    cur.execute(
                        "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".
                        format(email=data['email'], password=data['password']))
                except:
                    cur.close()
                    return jsonencoder(0, 'not existing user or wrong password')

                try:
                    # 验证当前用户是否为list的admin
                    cur.execute("SELECT admin_id from list where id= (select list_id from task where id={})".format(
                        data['task_id']))
                    admin_id = cur.fetchall()[0][0]
                    if admin_id != data['user_id']:
                        cur.close()
                        return jsonencoder(0, "No authority to change list")

                    cur.execute(
                        "Update task set name='{task_name}', content='{content}', create_date='{create_date}', due_date='{due_date}'\
                            , pos_x={position_x}, pos_y={position_y} where id={task_id}".format(
                            task_id=data['task_id'],
                            task_name=data['task_name'],
                            content=data['content'],
                            create_date=data['create_date'],
                            due_date=data['due_date'],
                            position_x=data['position_x'],
                            position_y=data['position_y']
                        )
                    )
                except Exception as e:
                    print(e)
                    cur.close()
                    # print(traceback.print_exc())
                    return jsonencoder(0, 'Modifying failed.')
                cur.close()
                return jsonencoder(1, 'success')

            elif data['type'] == MessageType.del_list:
                cur = mysql.get_db().cursor()
                # 验证登录
                try:
                    cur.execute(
                        "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".
                        format(email=data['email'], password=data['password']))
                except:
                    cur.close()
                    return jsonencoder(0, 'not existing user or wrong password')

                try:
                    print("DELETE FROM list WHERE id = {}".format(
                        data['list_id']))
                    # 如果是admin才能对列表进行添加修改操作
                    cur.execute(
                        "SELECT admin_id from list where id={}".format(data['list_id']))
                    fetch = cur.fetchall()
                    if not fetch:
                        cur.close()
                        return jsonencoder(0, "没有找到对应id的list") 
                    admin_id= fetch[0][0]
                    if admin_id != data["user_id"]:
                        cur.close()
                        return jsonencoder(0, "No authority to change list")
                    cur.execute(
                        "DELETE FROM list WHERE id = {}".format(data['list_id']))
                    mysql.get_db().commit()
                except:
                    cur.close()
                    print(traceback.print_exc())
                    return jsonencoder(0, 'Cannot delete. Please check')
                cur.close()
                return jsonencoder(1, 'success')

            elif data['type'] == MessageType.del_task:
                cur = mysql.get_db().cursor()
                # 验证登录
                try:
                    cur.execute(
                        "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".
                        format(email=data['email'], password=data['password']))
                except:
                    cur.close()
                    return jsonencoder(0, 'not existing user or wrong password')

                try:
                    # 验证当前用户是否为list的admin
                    cur.execute("SELECT admin_id from list where id= (select list_id from task where id={})".format(
                        data['task_id']))
                    admin_id = cur.fetchall()[0][0]
                    if admin_id != data['user_id']:
                        cur.close()
                        return jsonencoder(0, "No authority to change list")

                    print("DELETE FROM task WHERE id = {task_id} ".format(
                        task_id=data['task_id']))
                    cur.execute(
                        "DELETE FROM task WHERE id = {task_id} ".format(task_id=data['task_id']))
                    mysql.get_db().commit()
                except:
                    cur.close()
                    print(traceback.print_exc())
                    return jsonencoder(0, "Cannot Delete. Please check ")
                cur.close()
                return jsonencoder(1, 'success')

            elif data['type'] == MessageType.finish:
                cur = mysql.get_db().cursor()
                # 验证登录
                try:
                    cur.execute(
                        "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".
                        format(email=data['email'], password=data['password']))
                except:
                    cur.close()
                    return jsonencoder(0, 'not existing user or wrong password')

                print(
                    "UPDATE task set is_finished = {state} where user_id = {user_id} and id = {task_id}".format(
                        state=data['state'], user_id=data['user_id'], task_id=data['task_id'])
                )
                try:
                    cur.execute(
                        "UPDATE task set is_finished = {state} where user_id = {user_id} and id = {task_id}".format(
                            state=data['state'], user_id=data['user_id'], task_id=data['task_id'])
                    )
                    mysql.get_db().commit()
                except:
                    cur.close()
                    return jsonencoder(0, "Update Failed. Please check")
                cur.close()
                return jsonencoder(1, 'success')

            elif data['type'] == MessageType.assignment:
                cur = mysql.get_db().cursor()
                # 验证登录
                try:
                    cur.execute(
                        "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".
                        format(email=data['email'], password=data['password']))
                except:
                    cur.close()
                    return jsonencoder(0, 'not existing user or wrong password')

                print(
                    "INSERT INTO task(user_id, list_id, name, content, create_date, due_date, pos_x, pos_y)" +
                    "VALUES({user_id}, {list_id}, '{task_name}', '{content}', '{create_date}', '{due_date}', {position_x}, {position_y})".format(
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
                    # 如果是admin才能对列表进行添加修改操作
                    cur.execute(
                        "SELECT admin_id from list where id={}".format(data['list_id']))
                    admin_id= cur.fetchall()[0][0]
                    if admin_id != data["user_id"]:
                        cur.close()
                        return jsonencoder(0, "No authority to change list")
                        
                    cur.execute(
                        "SELECT user_id from class_member where list_id={}".format(data['list_id']))
                    users = cur.fetchall()
                    if len(users):
                        sql_string = "INSERT INTO task(user_id, list_id, name, content, create_date, due_date, pos_x, pos_y) Values"
                        for i in range(len(users)):
                            if i:
                                sql_string += ","
                            sql_string += "({user_id}, {list_id}, '{task_name}', '{content}', '{create_date}', '{due_date}', {position_x}, {position_y})".format(
                                list_id=data['list_id'],
                                user_id=users[i][0],
                                task_name=data['task_name'],
                                content=data['content'],
                                create_date=data['create_date'],
                                due_date=data['due_date'],
                                position_x=data['position_x'],
                                position_y=data['position_y']
                            )

                        cur.execute(sql_string)
                        mysql.get_db().commit()
                except:
                    cur.close()
                    print(traceback.print_exc())
                    return jsonencoder(0, 'Assigning Assignment Failed. Please check')
                cur.close()
                return jsonencoder(1, 'success')

            elif data['type'] == MessageType.join:
                cur = mysql.get_db().cursor()
                # 验证登录
                try:
                    cur.execute(
                        "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".
                        format(email=data['email'], password=data['password']))
                except:
                    cur.close()
                    return jsonencoder(0, 'not existing user or wrong password')
                #验证是否为班级
                print(
                    "INSERT INTO class_member VALUES({list_id}, {user_id})".format(
                        list_id=data['list_id'],
                        user_id=data['user_id']
                    )
                )
                objects_list = []
                try:
                    # 先加入班级
                    cur.execute(
                        "INSERT INTO class_member VALUES({list_id}, {user_id})".format(
                            list_id=data['list_id'],
                            user_id=data['user_id']
                        )
                    )
                    cur.execute(
                        "SELECT count(*) from class_member where list_id={list_id}".format(list_id=data['list_id'])
                    )
                    if cur.fetchall()[0][0] == 1:
                        print("需要将其设置为管理员")
                        cur.execute(
                            "Update list set admin_id={user_id} where id={list_id}".format( 
                                list_id=data['list_id'],
                                user_id=data['user_id']
                            )
                        )

                    # 然后设置所有的作业
                    cur.execute(
                        "SELECT name, content, create_date, due_date, pos_x, pos_y from task where user_id=-1 and list_id={}".format(
                            data['list_id']
                        )
                    )
                    tasks = cur.fetchall()
                    print(tasks)
                    if len(tasks):
                        sql_string = "INSERT INTO task(user_id, list_id, name, content, create_date, due_date, pos_x, pos_y) Values"
                        for i in range(len(tasks)):
                            if i:
                                sql_string += ","
                            sql_string += "('{user_id}', '{list_id}', '{task_name}', '{content}', '{create_date}', '{due_date}', {position_x}, {position_y})".format(
                                list_id=data['list_id'],
                                user_id=data['user_id'],
                                task_name=tasks[i][0],
                                content=tasks[i][1],
                                create_date=tasks[i][2],
                                due_date=tasks[i][3],
                                position_x=tasks[i][4],
                                position_y=tasks[i][5]
                            )
                            
                            
                        cur.execute(sql_string)

                    cur.execute(
                        r"SELECT * FROM task where user_id='{user_id}' and list_id='{list_id}'".format(
                            user_id=data['user_id'], list_id=data['list_id']
                        )
                    )
                    mysql.get_db().commit()
                    results = cur.fetchall()
                    # print(results)
                    for row in results:
                        d = collections.OrderedDict()
                        d['id'] = row[0]
                        d['user_id'] = row[1]
                        d['list_id'] = row[2]
                        d['name'] = row[3]
                        d['content'] = row[4]
                        d['create_date'] = str(row[5])
                        d['due_date'] = str(row[6])
                        d['pos_x'] = row[7]
                        d['pos_y'] = row[8]
                        d['is_finished'] = row[9]

                        objects_list.append(copy.deepcopy(d))
                    
                        mysql.get_db().commit()
                except:
                    cur.close()
                    print(traceback.print_exc())
                    return jsonencoder(0, "Joining class Failed. Please check")
                cur.close()
                resp = {'list_id':data['list_id'], 'task_list':objects_list}
                
                print(objects_list)
                return jsonencoder(1, 'success', resp)
            
            elif data['type'] == MessageType.quit_class:
                cur = mysql.get_db().cursor()
                # 验证登录
                try:
                    cur.execute(
                        "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".
                        format(email=data['email'], password=data['password']))
                    
                except:
                    cur.close()
                    return jsonencoder(0, 'not existing user or wrong password')
                
                try:
                    # 删除class_member中的记录
                    cur.execute(
                        "Delete from class_member where user_id={} and list_id={}".format(
                            data["user_id"], data["list_id"]
                        )
                    )
                    # 删除task中的所有记录
                    cur.execute(
                        "Delete from task where user_id={} and list_id={}".format(
                            data["user_id"], data["list_id"]
                        )
                    )

                    # 查看同list中成员数量
                    cur.execute(
                        "SELECT * FROM class_member WHERE list_id={}".format(
                            data['list_id']
                        )
                    )

                    results = cur.fetchall()

                    if len(results) != 0:
                        # 直接将任意一个成员设定为管理员
                        cur.execute(
                            "UPDATE list SET admin_id=-1 WHERE id={list_id}".format(
                                list_id=data['list_id']
                            )
                        )
                    else:
                        # 直接设为没有管理员的list
                        cur.execute(
                            "UPDATE list SET admin_id={new_admin_id} WHERE id={list_id}".format(
                                list_id=data['list_id'], new_admin_id=-1
                            )
                        )

                    mysql.get_db().commit()
                except Exception as e:
                    cur.close()
                    print(traceback.print_exc())
                    return jsonencoder(0, "Cannot quit class, error: {}".format(e))
                cur.close()
                return jsonencoder(1, 'success')

            elif data['type'] == MessageType.find_list:
                cur = mysql.get_db().cursor()
                # 验证登录
                try:
                    cur.execute(
                        "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".
                        format(email=data['email'], password=data['password']))
                except:
                    cur.close()
                    return jsonencoder(0, 'not existing user or wrong password')
                print(
                    "SELECT * FROM list where name LIKE '\%{keyword}\%'".format(
                        keyword=data['keyword']
                    )
                )
                objects_list = []
                try:
                    cur.execute(
                        r"SELECT * FROM list where name LIKE '%{keyword}%'".format(
                            keyword=data['keyword']
                        )
                    )
                    mysql.get_db().commit()
                    results = cur.fetchall()
                    # print(results)
                    for row in results:
                        d = collections.OrderedDict()
                        d['list_id'] = row[0]
                        d['admin_id'] = row[1]
                        d['is_public'] = row[2]
                        d['list_name'] = row[3]
                        objects_list.append(copy.deepcopy(d))
                except:
                    cur.close()
                    print(traceback.print_exc())
                    return jsonencoder(0, "Selection failed. Please check.")
                cur.close()
                # print(objects_list)

                return jsonencoder(1, 'success', objects_list)
                
            elif data['type'] == MessageType.find_member:
                cur = mysql.get_db().cursor()
                # 验证登录
                try:
                    cur.execute(
                        "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".
                        format(email=data['email'], password=data['password']))
                except:
                    cur.close()
                    return jsonencoder(0, 'not existing user or wrong password')

                print(
                    "SELECT * FROM class_member where list_id = {list_id}".format(
                        list_id=data['list_id']
                    )
                )
                objects_list = []
                try:
                    cur.execute(
                        "SELECT * FROM user WHERE id IN (SELECT user_id FROM class_member where list_id = {list_id})".format(
                            list_id=data['list_id']
                        )
                    )
                    mysql.get_db().commit()
                    results = cur.fetchall()
                    print(results)
                    for row in results:
                        d = collections.OrderedDict()
                        d['id'] = row[0]
                        d['name'] = row[1]
                        d['email'] = row[2]
                        objects_list.append(copy.deepcopy(d))
                except:
                    cur.close()
                    print(traceback.print_exc())
                    return jsonencoder(0, "Selection failed. Please check.")
                cur.close()
                # return json.dumps(objects_list)
                return jsonencoder(1, 'success', data=objects_list)
            
            elif data['type'] == MessageType.transfer:
                cur = mysql.get_db().cursor()
                # 验证登录
                try:
                    cur.execute(
                        "SELECT * FROM pkutodo.user WHERE email='{email}' and password='{password}';".
                        format(email=data['email'], password=data['password']))
                except:
                    cur.close()
                    return jsonencoder(0, 'not existing user or wrong password')

                print(
                    "UPDATE list set admin_id = {target_user_id} where admin_id = {user_id} and list_id = {list_id}".format(
                        list_id=data['list_id'],
                        user_id=data['user_id'],
                        target_user_id=data['target_user_id']
                    )
                )
                try:
                    # 如果是admin才能对列表进行添加修改操作
                    cur.execute(
                        "SELECT admin_id from list where id={}".format(data['list_id']))
                    admin_id= cur.fetchall()[0][0]
                    if admin_id != data["user_id"]:
                        cur.close()
                        return jsonencoder(0, "No authority to change list")
                    
                    # 转移给的人必须也在这个班级里面
                    cur.execute(
                        "SELECT count(*) from class_member where list_id={list_id} and user_id={target_user_id}".format(
                            list_id=data['list_id'],
                            target_user_id=data['target_user_id']
                        )
                    )

                    if cur.fetchall()[0][0] != 1:
                        print("member not in the class")
                        return jsonencoder(0, "member not in the class")

                    cur.execute(
                        "UPDATE list set admin_id = {target_user_id} where admin_id = {user_id} and id = {list_id}".format(
                            list_id=data['list_id'],
                            user_id=data['user_id'],
                            target_user_id=data['target_user_id']
                        )
                    )
                    mysql.get_db().commit()
                except:
                    cur.close()
                    print(traceback.print_exc())
                    return jsonencoder(0, "Admin transfer failed. Please check.")
                cur.close()
                return jsonencoder(1, 'success')
            
            
                
            else:
                return jsonencoder(0, "wrong")
        except Exception as e:
            print(traceback.print_exc())
            return jsonencoder(0, "wrong type")
    else:
        return "Hello World"

@app.route("/filesubmit", methods=['post', 'get'])
def fileuploadpage():
    return send_from_directory("./", "fileupload.html")



@app.route('/fileupload', methods=['post','get'])
def fileupload():
    try:
        upload_path = './file'
        file = request.files['file']
        taskid = request.values.to_dict()['taskid']
        # taskid = flask.request.data['taskid']
        print(taskid, file.filename)
        if not file:
            return "no file specified"
        filename = taskid + '_' + file.filename
        extension = filename.split('.')[-1]
        print(filename)
        if extension.lower() in SUPPORT_FORMAT:
            file.save(os.path.join(upload_path, filename))
        else:
            return "not supported format"

        try:
            # 写入数据库
            cur = mysql.get_db().cursor()

            cur.execute(
                "INSERT INTO file(taskid, filepath, filename) VALUES({taskid}, '{filepath}', '{filename}')".format(taskid=taskid, filename=filename, filepath=os.path.join(upload_path, filename))
            )

            cur.close()
            return jsonencoder(1, "upload success")
        except Exception as e:
            print(e) # errors found when updating databases.
            return jsonencoder(0, e)
    except Exception as e:
        print(e)
        return jsonencoder(0, e)

@app.route('/filedoownload', methods=['post','get'])
def filedownload():
    pass 
    



# 监听地址为0.0.0.0,表示服务器的所有网卡
# 5000是监听端口
# debug=True表示启动debug模式。当代码有改动时,Flask会自动加载,无序重启！
app.run("0.0.0.0", 5888, debug=False)  # 启动Flask服务
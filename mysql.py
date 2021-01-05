#!/usr/bin/python3

import pymysql
 
# 打开数据库连接
db = pymysql.connect("localhost","root","12345678","pkutodo" )
 
# 使用cursor()方法获取操作游标 
cursor = db.cursor()
 
# SQL 查询语句
sql = "SELECT * FROM list"
try:
   # 执行SQL语句
   cursor.execute(sql)
   # 获取所有记录列表
   results = cursor.fetchall()
   for row in results:
      id = row[0]
       # 打印结果
      print ("id=%s" % \
             (id))
except:
   print ("Error: unable to fetch data")
 
# 关闭数据库连接
db.close()
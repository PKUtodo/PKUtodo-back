from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/index/')
def index():
    return render_template('index.html')

@app.route('/search/')
def search():
    # arguments
    condition = request.args.get('q')
    return '用户提交的查询参数是: {}'.format(condition)

# 默认的试图函数， 只能采用get请求
# 如果你想采用post请求，那么要写明
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return "hello"
    else:
        print(request.form)
        print(dir(request.values))
        username = request.form.get('username')
        password = request.form.get('password')
        print('username: {}, password: {}'.format(username, password))
        return 'name = {}, password = {}'.format(username, password)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9999)
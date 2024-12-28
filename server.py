import json
from multiprocessing import Process
import os
import signal
from flask import Flask
from flask_restful import Resource, Api, request
from flask_httpauth import HTTPBasicAuth
from job import StartJob
from lib import Libs, Lib, OO5List, Setting, TGBot
from telebot import apihelper
proxyHost = os.getenv('PROXY_HOST', '')
if proxyHost != '':
    apihelper.proxy = {'http': proxyHost, 'https': proxyHost}

LIBS = Libs()
o5List = OO5List()

app = Flask(__name__, static_folder="frontend")
api = Api(app=app)
auth = HTTPBasicAuth()

class Libs(Resource):
    def get(self):
        # 获取同步目录列表
        data = []
        list = LIBS.list()
        for item in list:
            data.append(item.getJson())
        return {'code': 200, 'msg': '', 'data': data}
    
    def post(self):
        # 添加同步目录
        data = request.get_json()
        rs, msg = LIBS.add(data)
        if rs is False:
            return {'code': 500, 'msg': msg, 'data': {}}
        return {'code': 200, 'msg': '', 'data': {}}

class Lib(Resource):
    def get(self, key: str):
        lib = LIBS.getLib(key)
        if lib is None:
            return {'code': 404, 'msg': '同步目录不存在', 'data': {}}
        return {'code': 200, 'msg': '', 'data': lib.getJson()}

    def delete(self, key: str):
        # 删除同步目录
        rs, msg = LIBS.deleteLib(key)
        if rs is False:
            return {'code': 500, 'msg': msg, 'data': {}}
        return {'code': 200, 'msg': '', 'data': {}}

    def put(self, key: str):
        # 修改同步目录
        data = request.get_json()
        rs, msg = LIBS.updateLib(key, data)
        if rs is False:
            return {'code': 500, 'msg': msg, 'data': {}}
        return {'code': 200, 'msg': '', 'data': {}}


class LibSync(Resource):
    def post(self, key: str):
        lib = LIBS.getLib(key)
        if lib is None:
            return {'code': 404, 'msg': '同步目录不存在', 'data': {}}
        if lib.extra.pid > 0:
            return {'code': 500, 'msg': '该目录正在同步中...', 'data': {}}
        p1 = Process(target=StartJob, kwargs={'key': key})
        p1.start()
        return {'code': 200, 'msg': '已启动任务', 'data': {}} 

class LibStop(Resource):
    def post(self, key: str):
        lib = LIBS.getLib(key)
        if lib is None:
            return {'code': 404, 'msg': '同步目录不存在', 'data': {}}
        if lib.extra.pid > 0:
            try:
                os.kill(lib.extra.pid, signal.SIGILL)
                lib.extra.status = 3
            except:
                lib.extra.status = 1
        lib.extra.pid = 0
        LIBS.saveExtra(lib)
        return {'code': 200, 'msg': '已停止', 'data': {}}

class LibLog(Resource):
    def get(self, key: str):
        logFile = os.path.abspath("./data/logs/%s.log" % key)
        if not os.path.exists(logFile):
            return {'code': 200, 'msg': '', 'data': ""}
        content = ""
        with open(logFile, mode='r', encoding='utf-8') as logfd:
            content = logfd.read()
        content = content.replace("\n", "<br />")
        return {'code': 200, 'msg': '', 'data': content}

class OO5List(Resource):
    def get(self):
        data = []
        list = o5List.getList()
        for item in list:
            data.append(item.getJson())
        return {'code': 200, 'msg': '', 'data': data}
    
    def post(self):
        data = request.get_json()
        rs, msg = o5List.add(data)
        if rs is False:
            return {'code': 500, 'msg': msg, 'data': {}}
        return {'code': 200, 'msg': '', 'data': {}}

class OO5(Resource):
    def get(self, key: str):
        oo5 = o5List.getLib(key)
        if oo5 is None:
            return {'code': 404, 'msg': '115账号不存在', 'data': {}}
        return {'code': 200, 'msg': '', 'data': oo5}

    def delete(self, key: str):
        # 删除同步目录
        rs, msg = o5List.delOO5(key)
        if rs is False:
            return {'code': 500, 'msg': msg, 'data': {}}
        return {'code': 200, 'msg': '', 'data': {}}

    def put(self, key: str):
        # 修改同步目录
        data = request.get_json()
        rs, msg = o5List.updateOO5(key, data)
        if rs is False:
            return {'code': 500, 'msg': msg, 'data': {}}
        return {'code': 200, 'msg': '', 'data': {}}

class SettingApi(Resource):
    def get(self):
        settings = Setting()
        return {'code': 200, 'msg': '', 'data': settings.__dict__}

    def post(self):
        data = request.get_json()
        settings = Setting()
        settings.username = data.get("username")
        settings.password = data.get("password")
        settings.telegram_bot_token = data.get("telegram_bot_token")
        settings.telegram_user_id = data.get("telegram_user_id")
        if settings.username == '' or settings.password == '':
            return {'code': 500, 'msg': "用户名密码不能为空", 'data': {}}
        settings.save()
        if settings.telegram_bot_token != "" and settings.telegram_user_id != "":
            # 发送测试消息
            bot = TGBot()
            rs, msg = bot.sendMsg("通知配置成功，稍后您将在此收到运行通知")
            if not rs:
                return {'code': 500, 'msg': '保存成功，但是Telegram通知配置出错：{0}'.format(msg), 'data': settings.__dict__}
        return {'code': 200, 'msg': '', 'data': settings.__dict__}

class DirApi(Resource):
    def post(self):
        """
        返回目录列表
        """
        data = request.get_json()
        base_dir = data.get('base_dir')
        if base_dir is None or base_dir == '':
            base_dir = '/'
        dirs = os.listdir(base_dir)
        result = []
        for dir in dirs:
            item = os.path.join(base_dir, dir)
            if os.path.isfile(item):
                # 如果是文件，则不用递归
                continue
            result.append(dir)
        return {'code': 200, 'msg': '', 'data': result}

        
api.add_resource(Libs, '/api/libs')
api.add_resource(Lib, '/api/lib/<key>')
api.add_resource(LibSync, '/api/lib/sync/<key>')
api.add_resource(LibStop, '/api/lib/stop/<key>')
api.add_resource(LibLog, '/api/lib/log/<key>')
api.add_resource(OO5List, '/api/oo5list')
api.add_resource(OO5, '/api/oo5/<key>')
api.add_resource(SettingApi, '/api/settings')
api.add_resource(DirApi, '/api/dir')

# 跨域支持
def after_request(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS, DELETE, PUT'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type,XFILENAME,XFILECATEGORY,XFILESIZE,x-requested-with,Authorization'
    return resp

app.after_request(after_request)

@auth.verify_password
def verify_password(username, password):
    setting = Setting()
    # 验证用户名和密码的逻辑
    if username == setting.username and password == setting.password:
        return True
    return False

@app.route('/')
@auth.login_required
def index():
    return app.send_static_file('index.html')

@app.route('/assets/<path:filename>')
def assets(filename):
    return app.send_static_file('assets/%s' % filename)

@app.route('/api/job')
def jobApi():
    path = request.args.get('path')
    if path is None or path == "":
        return returnJson({'code': 404, 'msg': '同步目录不存在', 'data': {}})
    lib = LIBS.getByPath(path)
    if lib is None:
        return returnJson({'code': 404, 'msg': '同步目录不存在', 'data': {}})
    if lib.extra.pid > 0:
        return returnJson({'code': 500, 'msg': '该目录正在同步中...', 'data': {}})
    p1 = Process(target=StartJob, kwargs={'key': lib.key})
    p1.start()
    return returnJson({'code': 200, 'msg': '已启动任务，可调用API查询状态：/api/lib/{0}'.format(lib.key), 'data': {}})

def returnJson(returnBody):
    returnJson = json.dumps(returnBody)
    return returnJson, 200, {"Content-Type":"application/json"}

def StartServer(host: str = '0.0.0.0'):
    # 启动一个线程，处理同步任务
    app.run(host, port=12123)

if __name__ == '__main__':
    StartServer(host='127.0.0.1')
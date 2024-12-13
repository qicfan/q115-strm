from multiprocessing import Process
import os, sys
import signal
from flask import Flask
from flask_restful import Resource, Api, request
from job import StarJob
from lib import Libs, Lib, OO5List
from watch import StartWatch

LIBS = Libs()
o5List = OO5List()

app = Flask(__name__, static_folder="frontend")
api = Api(app=app)

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
        p1 = Process(target=StarJob, kwargs={'key': key})
        p1.start()
        return {'code': 200, 'msg': '已启动任务', 'data': {}} 

class LibStop(Resource):
    def post(self, key: str):
        lib = LIBS.getLib(key)
        if lib is None:
            return {'code': 404, 'msg': '同步目录不存在', 'data': {}}
        if lib.extra.pid > 0:
            return {'code': 200, 'msg': '该同步任务已结束', 'data': {}}
        os.kill(lib.extra.pid, signal.SIGKILL)
        lib.extra.pid = 0
        lib.extra.status = 3
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

api.add_resource(Libs, '/api/libs')
api.add_resource(Lib, '/api/lib/<key>')
api.add_resource(LibSync, '/api/lib/sync/<key>')
api.add_resource(LibStop, '/api/lib/stop/<key>')
api.add_resource(LibLog, '/api/lib/log/<key>')
api.add_resource(OO5List, '/api/oo5list')
api.add_resource(OO5, '/api/oo5/<key>')

# 跨域支持
def after_request(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS, DELETE, PUT'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type,XFILENAME,XFILECATEGORY,XFILESIZE,x-requested-with,Authorization'
    return resp

watchProcess: Process | None = None
cronProcess: Process | None = None

def shutdown_server(sig, frame):
    if watchProcess is not None:
        watchProcess.terminate()
    sys.exit(0)

app.after_request(after_request)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/assets/<path:filename>')
def assets(filename):
    return app.send_static_file('assets/%s' % filename)

if __name__ == '__main__':
    if not os.path.exists('./data/logs'):
        os.makedirs('./data/logs')
    if not os.path.exists('./data/config'):
        os.makedirs('./data/config')
    signal.signal(signal.SIGINT, shutdown_server)
    signal.signal(signal.SIGTERM, shutdown_server)
    LIBS.initCron()
    watchProcess = Process(target=StartWatch)
    watchProcess.start()
    app.run(host="0.0.0.0", port=12123)
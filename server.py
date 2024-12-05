
# libs - 监控的媒体库
#   path - 115相对路径
#   name - 自定义名称
#   watch - 是否监控文件变更自动触发同步: 1-开启，2-关闭
#   status - 状态：1-正常，2-同步中，3-未完成（每次请求时会检查，如果同步中但是PID不存在则会改为3）
#   pid - 处于同步中时的进程ID，可以根据PID强行停止
#   created_at - 添加时间
#   last_sync_at - 最后一次同步时间
#   last_sync_result - 最后一次同步结果

# get /settings 查询配置
# post /settting 保存配置
# get /libs 媒体库列表
# post /libs 添加媒体库
# delete /lib/{key} 删除媒体库
# post /lib/sync 手动同步
# post /lib/stop 手动停止
import os, json
from flask import Flask
from flask_restful import Resource, Api, request

app = Flask(__name__)
app.config['STATIC_FOLDER'] = 'assets'
app.config['STATIC_URL_PATH'] = '/assets'

api = Api(app=app)

class Settings(Resource):
    def get(self):
        config = {}
        config_file = os.path.abspath("./config/config.json")
        with open(config_file, mode='r', encoding='utf-8') as fd_config:
            config = json.load(fd_config)
        return {'code': 200, 'msg': '', 'data': config}
    
    def post(self):
        post_config = request.get_json()
        return post_config

class Libs(Resource):
    def get(self):
        pass
    
    def post(self):
        pass

class Lib(Resource):
    def get(self, key: str):
        pass

    def delete(self, key: str):
        pass

    def put(self, key: str)
        pass

class LibSync(Resource):
    def post(self, key: str):
        pass

class LibStop(Resource):
    def post(self, key: str):
        pass

api.add_resource(Settings, '/settings')
api.add_resource(Libs, '/libs')
api.add_resource(Lib, '/lib/<key>')
api.add_resource(LibSync, '/lib/sync/<key>')
api.add_resource(LibStop, '/lib/stop/<key>')

if __name__ == '__main__':
    app.run()
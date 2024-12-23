import datetime, pytz
import json
import hashlib, os
from typing import List, Mapping
from crontab import CronTab
import telebot
from telebot import apihelper
from telebot import apihelper
proxyHost = os.getenv('PROXY_HOST', '')
if proxyHost != '':
    apihelper.proxy = {'http': proxyHost, 'https': proxyHost}
TABFILE = './data/config/cron.tab'



def GetNow():
    # 获取当前时间
    now = datetime.datetime.now()
    # 创建一个表示北京时区的对象
    beijing = pytz.timezone('Asia/Shanghai')
    # 将当前时间转换为北京时区
    now_beijing = now.astimezone(beijing)
    return now_beijing.strftime("%Y-%m-%d %H:%M:%S")


class LibExtra:
    pid: str # 正在运行的进程ID
    status: int # 运行状态: 1-正常，2-运行中，3-中断
    last_sync_at: str # 最后运行时间
    last_sync_result: Mapping[str, List[int]]

    def __init__(self, pid: int = 0, status: int = 1, last_sync_at: str = '', last_sync_result: Mapping[str, List[int]] = {'strm': [0,0], 'meta': [0,0],'delete': [0,0]}):
        self.pid = pid
        self.status = status
        self.last_sync_at = last_sync_at
        self.last_sync_result = last_sync_result

    def getJson(self):
        dict = self.__dict__
        return dict

class LibBase:
    key: str # 标识
    cloud_type: str # 网盘类型，分为：115, other
    name: str # 名称
    path: str # 路径
    type: str # strm类型，'本地路径' | 'WebDAV' | 'alist302'
    strm_root_path: str # strm根目录
    mount_path: str # alist挂载根文件夹，cd2留空
    alist_server: str # alist服务器地址，格式：http[s]://ip:port
    alist_115_path: str # alist中115路径，一般都是：115
    path_of_115: str # 115挂载根目录
    copy_meta_file: int # 元数据选项：1-关闭，2-复制，3-软链接
    copy_delay: int | float # 元数据复制间隔
    webdav_url: str # webdav服务器链接
    webdav_username: str # webdav服务器用户名
    webdav_password: str # webdav服务器密码
    sync_type: str # 同步类型，'定时' | '监控变更'
    cron_str: str # 定时同步规则
    id_of_115: str # 115账号标识
    strm_ext: list[str] # strm扩展名
    meta_ext: list[str] # 元数据扩展名

    def __init__(self, data: None | dict):
        if data is None:
            return
        self.key = data.get('key') if data.get('key') is not None else ''
        self.cloud_type = data.get('cloud_type') if data.get('cloud_type') is not None else '115' # 默认115
        self.name = data.get('name') if data.get('name') is not None else ''
        self.path = data.get('path') if data.get('path') is not None else ''
        self.type = data.get('type') if data.get('type') is not None else '本地路径'
        self.strm_root_path = data.get('strm_root_path') if data.get('strm_root_path') is not None else ''
        self.mount_path = data.get('mount_path') if data.get('mount_path') is not None else ''
        self.alist_server = data.get('alist_server') if data.get('alist_server') is not None else ''
        self.alist_115_path = data.get('alist_115_path') if data.get('alist_115_path') is not None else ''
        self.path_of_115 = data.get('path_of_115') if data.get('path_of_115') is not None else ''
        self.copy_meta_file = data.get('copy_meta_file') if data.get('copy_meta_file') is not None else '关闭'
        self.copy_delay = float(data.get('copy_delay')) if data.get('copy_delay') is not None else 1
        self.webdav_url = data.get('webdav_url') if data.get('webdav_url') is not None else ''
        self.webdav_username = data.get('webdav_username') if data.get('webdav_username') is not None else ''
        self.webdav_password = data.get('webdav_password') if data.get('webdav_password') is not None else ''
        self.sync_type = data.get('sync_type') if data.get('sync_type') is not None else '手动'
        self.cron_str = data.get('cron_str') if data.get('cron_str') is not None else ''
        self.id_of_115 = data.get('id_of_115') if data.get('id_of_115') is not None else ''
        self.strm_ext = data.get('strm_ext') if data.get('strm_ext') is not None else [
            '.mkv',
            '.mp4',
            '.ts',
            '.avi',
            '.mov',
            '.mpeg',
            '.mpg',
            '.wmv',
            '.3gp',
            '.m4v',
            '.flv',
            '.m2ts',
            '.f4v',
            '.tp',
        ]
        self.meta_ext = data.get('meta_ext') if data.get('meta_ext') is not None else [
            '.jpg',
            '.jpeg',
            '.png',
            '.webp',
            '.nfo',
            '.srt',
            '.ass',
            '.svg',
            '.sup',
            '.lrc',
        ]
        newStrmExt = []
        for ext in self.strm_ext:
            newStrmExt.append(ext.lower())
        newMetaExt = []
        for ext in self.meta_ext:
            newMetaExt.append(ext.lower())
        self.strm_ext = newStrmExt
        self.meta_ext = newMetaExt
        if self.key == '':
            self.makeKey()
            
    def makeKey(self):
        m = hashlib.md5()
        m.update(self.path.encode(encoding='UTF-8'))
        self.key = m.hexdigest()


class Lib(LibBase):
    extra: LibExtra

    def __init__(self, data: None | dict):
        super().__init__(data)
        hasExtra = False
        if data is not None:
            extra = data.get('extra')
            if extra is not None:
                hasExtra = True
                self.extra = LibExtra(
                    pid=data['extra']['pid'],
                    status=data['extra']['status'],
                    last_sync_at=data['extra']['last_sync_at'],
                    last_sync_result=data['extra']['last_sync_result']
                )
        if hasExtra == False:
            self.extra = LibExtra()


    def validate(self) -> tuple[bool, str]:
        # 验证路径是否存在
        # 验证STRM根目录是否存在
        if not os.path.exists(self.strm_root_path):
            return False, 'STRM根目录不存在，请检查文件系统中是否存在该目录：%s' % self.strm_root_path
        # 验证115挂载根目录是否存在
        if self.path_of_115 != '' and not os.path.exists(self.path_of_115):
            return False, '115挂载根目录不存在，请检查文件系统中是否存在该目录：%s' % self.path_of_115
        if self.cloud_type == 'other' and not os.path.exists(self.path):
            return False, '同步路径不存在，请检查文件系统中是否存在该目录：%s' % self.path
        return True, ''

    def cron(self):
        # 处理定时任务
        cron = CronTab(tabfile=TABFILE)
        iter = cron.find_comment(self.key)
        existsJob = None
        for i in iter:
            existsJob = i
        if self.sync_type == '定时':
            if existsJob is not None:
                cron.remove(existsJob)
                cron.write(filename=TABFILE)
            jobFile = os.path.abspath('./job.py')
            job = cron.new(comment="%s" % self.key, command="python3 %s -k %s" % (jobFile, self.key))
            job.setall(self.cron_str)
            cron.write(filename=TABFILE)
        else:
            if existsJob is not None:
                # 删除定时任务
                cron.remove(existsJob)
                cron.write(filename=TABFILE)
        return True

    def getJson(self):
        dict = self.__dict__
        if isinstance(self.extra, LibExtra):
            dict['extra'] = self.extra.getJson()
        else:
            dict['extra'] = self.extra
        return dict
        
    
def jsonHook(obj):
    return obj.getJson()

class Libs:
    libs_file: str = os.path.abspath("./data/config/libs.json")
    libList: Mapping[str, List[Lib]] # 同步目录列表

    def __init__(self):
        self.libList = {}
        self.loadFromFile()
    
    def loadFromFile(self):
        libs = {}
        if os.path.exists(self.libs_file):
            with open(self.libs_file, mode='r', encoding='utf-8') as fd_libs:
                jsonLibs = json.load(fd_libs)
            for k in jsonLibs:
                libs[k] = Lib(jsonLibs[k])
        self.libList = libs
        return True
    
    def list(self) -> List[Lib]:
        self.loadFromFile()
        l: list[Lib] = []
        for key in self.libList:
            l.append(self.libList.get(key))
        return l
    
    def save(self) -> bool:
        with open(self.libs_file, mode='w', encoding='utf-8') as fd_libs:
            json.dump(self.libList, fd_libs, default=jsonHook)
        return True
        
    def getLib(self, key: str) -> Lib | None:
        self.loadFromFile()
        return self.libList.get(key)
    
    def getByPath(self, path: str) -> Lib | None:
        self.loadFromFile()
        for key in self.libList:
            item = self.libList.get(key)
            if item.path == path:
                return item
        return None
    
    def add(self, data: dict) -> tuple[bool, str]:
        for k, v in self.libList.items():
            if v.path == data['path']:
                return False, '同步目录已存在'
            if v.name == data['name']:
                return False, '同步目录名称已存在'
        data['extra'] = {
            'pid': 0,
            'status': 1,
            'last_sync_at': '',
            'last_sync_result': {
                'strm': [0, 0],
                'meta': [0, 0],
                'delete': [0, 0]
            }
        }
        lib = Lib(data)
        rs, msg = lib.validate()
        if rs is False:
            return rs, msg
        self.libList[lib.key] = lib
        self.save()
        lib.cron()
        return True, ''

    def updateLib(self, key: str, data: dict) -> tuple[bool, str]:
        lib = self.getLib(key)
        if lib is None:
            return False, '同步目录不存在'
        del data['extra']
        for k in data:
            lib.__setattr__(k, data[k])
        self.libList[key] = lib
        self.save()
        lib.cron()
        return True, ''

    def saveExtra(self, lib: Lib):
        self.libList[lib.key] = lib
        self.save()
        pass

    def deleteLib(self, key: str) -> tuple[bool, str]:
        lib = self.getLib(key)
        lib.sync_type = '手动'
        lib.cron()
        del self.libList[key]
        self.save()
        return True, ''
    
    def initCron(self):
        # 每次启动服务时，检查定时任务是否存在，不存在的创建
        libs = self.list()
        for item in libs:
            item.cron()
        return True

    
class OO5:
    key: str
    name: str
    cookie: str
    status: int
    created_at: str
    updated_at: str

    def __init__(self, data: dict):
        self.name = data['name']
        self.cookie = data['cookie']
        self.status = data['status']
        self.created_at = data['created_at']
        self.updated_at = data['updated_at']
        self.key = data['key']
    
    def getJson(self):
        dict = self.__dict__
        return dict
    

class OO5List:
    oo5_files = os.path.abspath("./data/config/115.json")
    list: Mapping[str, OO5] # 115账号列表

    def __init__(self):
        self.list = {}
        self.loadFromFile()
    
    def loadFromFile(self):
        list = {}
        if os.path.exists(self.oo5_files):
            with open(self.oo5_files, mode='r', encoding='utf-8') as fd_oo5:
                jsonList = json.load(fd_oo5)
            for k in jsonList:
                list[k] = OO5(jsonList[k])
        self.list = list
        return True

    def save(self) -> bool:
        with open(self.oo5_files, mode='w', encoding='utf-8') as o:
            json.dump(self.list, o, default=jsonHook)
        return True
    
    def get(self, key: str) -> OO5 | None:
        self.loadFromFile()
        return self.list.get(key)
    
    def getByCookie(self, cookies: str) -> OO5 | None:
        self.loadFromFile()
    
    def getList(self) -> List[OO5]:
        self.loadFromFile()
        l: list[OO5] = []
        for key in self.list:
            l.append(self.list.get(key))
        return l
    
    def add(self, data: dict) -> tuple[bool, str]:
        self.loadFromFile()
        for key in self.list:
            if self.list[key].name == data['name'] or self.list[key].cookie == data['cookie']:
                return False, '名称或者cookie已存在'
        data['created_at'] = GetNow()
        data['updated_at'] = ''
        data['status'] = 0
        m = hashlib.md5()
        m.update(data['name'].encode(encoding='UTF-8'))
        data['key'] = m.hexdigest()
        oo5 = OO5(data)
        self.list[oo5.key] = oo5
        self.save()
        return True, ''
    
    def updateOO5(self, key: str, data: dict):
        self.loadFromFile()
        oo5 = self.get(key)
        if oo5 is None:
            return False, '115账号不存在'
        oo5.name = data['name']
        oo5.cookie = data['cookie']
        oo5.updated_at = GetNow()
        self.list[key] = oo5
        self.save()
        return True, ''

    def delOO5(self, key: str):
        self.loadFromFile()
        oo5 = self.get(key)
        if oo5 is None:
            return True, ''
        # 检查是否有在使用
        libs = Libs()
        libList = libs.list()
        for item in libList:
            if item.id_of_115 == key:
                return False, '该账号使用中'
        del self.list[key]
        self.save()
        return True, ''

class Setting:
    username: str = "admin"
    password: str = "admin"
    telegram_bot_token: str = ""
    telegram_user_id: str = ""

    def __init__(self):
        self.loadFromFile()

    def loadFromFile(self):
        if not os.path.exists("./data/config/setting.json"):
            return False
        try:
            with open("./data/config/setting.json", mode='r', encoding='utf-8') as fd:
                jsonSetting: dict = json.load(fd)
            self.username = jsonSetting.get("username")
            self.password = jsonSetting.get("password")
            self.telegram_bot_token = jsonSetting.get("telegram_bot_token")
            self.telegram_user_id = jsonSetting.get("telegram_user_id")
        except:
            return False
        return True
    
    def save(self) -> tuple[bool, str]:
        try:
            with open('./data/config/setting.json', mode='w', encoding='utf-8') as f:
                json.dump(self.__dict__, f)
        except Exception as e:
            return False, e
        return True, ""
    
class TGBot:
    bot = None | telebot.TeleBot

    def __init__(self):
        setting = Setting()
        if setting.telegram_bot_token != "":
            self.bot = telebot.TeleBot(setting.telegram_bot_token)

    def sendMsg(self, msg: str, parse_mode: str = "MarkdownV2") -> tuple[bool, str]:
        if self.bot is None:
            return True, "没有配置机器人"
        setting = Setting()
        if setting.telegram_user_id == "":
            return True, "没有配置用户ID"
        try:
            self.bot.send_message(setting.telegram_user_id, msg, parse_mode)
            return True, ""
        except Exception as e:
            return False, e



if __name__ == '__main__':
    # with open('./data/config/libs.json', mode='r', encoding='utf-8') as fd_libs:
    #     jsonLibs = json.load(fd_libs)
    # newLibs = {}
    # for item in jsonLibs:
    #     newLibs[item['key']] = item
    # with open('./data/config/libs.json', mode='w', encoding='utf-8') as fd_libs:
    #     json.dump(newLibs, fd_libs)
    pass
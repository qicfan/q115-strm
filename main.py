import json
from multiprocessing import Process
import signal
import os, sys

cronProcess: Process | None = None
watchProcess: Process | None = None

def stop(sig, frame):
    try:
        if watchProcess is not None:
            watchProcess.terminate()
    except:
        pass
    try:
        if cronProcess is not None:
            cronProcess.terminate()
    except:
        pass
    sys.exit(0)

signal.signal(signal.SIGINT, stop)
signal.signal(signal.SIGTERM, stop)
if not os.path.exists('./data/logs'):
    os.makedirs('./data/logs')
if not os.path.exists('./data/config'):
    os.makedirs('./data/config')
if not os.path.exists('./data/config/setting.json'):
    # 初始化settting.json
    setting = {"username": "admin", "password": "admin", "telegram_bot_token": "", "telegram_user_id": ""}
    with open('./data/config/setting.json', mode='w', encoding='utf-8') as f:
        json.dump(setting, f)

from cron import StartCron
from server import StartServer
from watch import StartWatch

if __name__ == '__main__':
    # 启动监控服务
    watchProcess = Process(target=StartWatch)
    watchProcess.start()
    cronProcess = Process(target=StartCron)
    cronProcess.start()
    # 启动web服务
    StartServer()
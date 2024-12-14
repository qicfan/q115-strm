import hashlib
import logging
from multiprocessing import Process
import signal
import os, sys
import time

from job import DetailedFormatter
from lib import TABFILE, Libs
from server import StartServer
from watch import StartWatch
from crontab import CronTab

LIBS = Libs()
cronProcess: Process | None = None
watchProcess: Process | None = None
cronSubProc: Process | None = None

def get_file_md5(file_path):
    """
    获取文件md5值
    :param file_path: 文件路径名
    :return: 文件md5值
    """
    with open(file_path, 'rb') as f:
        md5obj = hashlib.md5()
        md5obj.update(f.read())
        _hash = md5obj.hexdigest()
    return str(_hash).upper()

def stop(sig, frame):
    if watchProcess is not None:
        watchProcess.terminate()
    if cronProcess is not None:
        cronProcess.terminate()
    sys.exit(0)

def startCronSub():
    print('启动Crontab守护进程')
    tab = CronTab(tabfile=TABFILE)
    for result in tab.run_scheduler():
        print("Return code: {0}".format(result.returncode))
        print("Standard Out: {0}".format(result.stdout))
        print("Standard Err: {0}".format(result.stderr))

def StartCron():
    print("启动定时任务")
    cronSubProc = Process(target=startCronSub)
    cronSubProc.start()
    md5 = get_file_md5(TABFILE)
    print("记录cron文件的指纹：{0}".format(md5))
    while(True):
        newmd5 = get_file_md5(TABFILE)
        if md5 != newmd5:
            print("cron文件有变化，重新加载定时任务{0} : {1}".format(md5, newmd5))
            # 有变化，重启进程
            cronSubProc.terminate()
            cronSubProc = Process(target=startCronSub)
            cronSubProc.start()
            md5 = newmd5
        else:
            print("cron文件没有变化，等待10秒重试")
        time.sleep(10)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    
    if not os.path.exists('./data/logs'):
        os.makedirs('./data/logs')
    if not os.path.exists('./data/config'):
        os.makedirs('./data/config')
    if not os.path.exists('./data/config/cron.tab'):
        with open(TABFILE, mode='w', encoding='utf-8') as f:
            f.write('')
    # 启动监控服务
    watchProcess = Process(target=StartWatch)
    watchProcess.start()
    # 启动定时任务服务
    LIBS.initCron()
    cronProcess = Process(target=StartCron)
    cronProcess.start()
    # StartCron()
    # 启动web服务
    StartServer()
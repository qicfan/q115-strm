from multiprocessing import Process
import signal, sys
import time
from typing import Mapping
from watchdog.observers import Observer
from watchdog.events import *

from job import DetailedFormatter, StarJob
from lib import Lib, Libs

LIBS = Libs()
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logfile = os.path.abspath("./data/logs/watch.log")
file_handler = logging.FileHandler(filename=logfile, mode='a', encoding='utf-8')
file_handler.setFormatter(DetailedFormatter())
logger.addHandler(file_handler)

class FileEventHandler(FileSystemEventHandler):

    lib: Lib
    taskPool: list[float]

    def __init__(self, key):
        super().__init__()
        self.lib = LIBS.getLib(key)
        if self.lib is None:
            raise ValueError('同步目录不存在')
        self.taskPool = []

    def on_any_event(self, event):
        pass

    def on_moved(self, event):
        if event.is_directory:
            logger.info("directory moved from {0} to {1}".format(event.src_path,event.dest_path))
        else:
            logger.info("file moved from {0} to {1}".format(event.src_path,event.dest_path))
        self.taskPool.append(timestamp = time.time())

    def on_created(self, event):
        if event.is_directory:
            logger.info("directory created:{0}".format(event.src_path))
        else:
            logger.info("file created:{0}".format(event.src_path))
        self.taskPool.append(timestamp = time.time())

    def on_deleted(self, event):
        if event.is_directory:
            logger.info("directory deleted:{0}".format(event.src_path))
        else:
            logger.info("file deleted:{0}".format(event.src_path))
        self.taskPool.append(timestamp = time.time())

    def on_modified(self, event):
        if not event.is_directory:
            logger.info("file modified:{0}".format(event.src_path))


def watch(key: str):
    observer = Observer() # 定义监控类,多线程类 thread class
    def stop(sig, frame):
        observer.stop()
        sys.exit(0)
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    try:
        eventHandler = FileEventHandler(key)
        observer.schedule(eventHandler,os.path.join(eventHandler.lib.path_of_115, eventHandler.lib.path), recursive=True) # 指定监控路径/触发对应的监控事件类
        observer.start()# 将observer运行在同一个线程之内,不阻塞主进程运行,可以调度observer来停止该线程
        try:
            while True:
                # 取最后一次事件事件，如果间隔3分钟或以上，则触发一次任务，然后清空队列
                if len(eventHandler.taskPool) > 0:
                    lastTime = eventHandler.taskPool[len(eventHandler.taskPool) - 1]
                    currentTime = time.time()
                    if currentTime - lastTime >= 180:
                        eventHandler.taskPool = []
                        p1 = Process(target=StarJob, kwargs={'key': eventHandler.lib.key})
                        p1.start()
                        p1.join()
                time.sleep(3) # 监控频率（1s1次，根据自己的需求进行监控）
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    except:
        logger.info('同步目录[%s]不存在，无法启动监控任务' % key)
        pass

def StartWatch():
    # 每个同步目录启动一个子进程
    # 每隔1分钟读取新的同步目录列表
    #   如果目录删除或修改同步类型为非监控，则停止对应子进程
    #   如果新增目录，则启动新的子进程
    pool: Mapping[str, Process] = {}
    def stop(sig, frame):
        logger.info('收到停止进程信号，尝试终止所有子任务')
        for key in pool:
            pool[key].terminate()
            logger.info('任务：%s 已终止' % key)
        sys.exit(0)
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    logger.info('准备启动监控服务')
    while(True):
        libs = LIBS.list()
        if len(libs) == 0:
            logger.info('没有需要监控的目录，等待下次触发')
        else:
            for item in libs:
                # 检查是否存在进程
                p = pool.get(item.key)
                if item.sync_type != '监控变更':
                    if p is not None:
                        # 结束进程
                        logger.info('同步目录[%s]的同步方式变更为非监控，终止监控任务' % item.path)
                        p.terminate()
                        del pool[key]
                else:
                    if p is None:
                        # 启动新的子进程
                        p = Process(target=watch, kwargs={'key': item.key})
                        p.start()
                        pool[key] = p
                        logger.info('新增同步目录[%s]，已启动监控任务' % item.path)
            libList = LIBS.libList
            for key in pool:
                item = libList.get(key)
                if item is None:
                    # 同步目录已删除，终止任务
                    pool[key].terminate()
                    del pool[key]
                    logger.info('同步目录[%s]已删除，终止监控任务' % item.path)
        time.sleep(10)
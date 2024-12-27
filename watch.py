from queue import Queue
import shutil
import signal
import time
from typing import Mapping
from watchdog.observers import Observer
from watchdog.observers.api import ObservedWatch
from watchdog.events import *
import os, sys

from lib import Lib, Libs
from log import getLogger

LIBS = Libs()
logger = getLogger(name='watch', rotating=True, stream=True)
queue = Queue()
pool: Mapping[str, ObservedWatch] = {}
ob = Observer()

class FileEventHandler(FileSystemEventHandler):

    lib: Lib
    taskPool: list[float]

    def __init__(self, key):
        super().__init__()
        self.lib = LIBS.getLib(key)
        if self.lib is None:
            raise ValueError('同步目录不存在')
        self.taskPool = []
    
    def getStrmPath(self, path):
        # 返回目标位置路径
        if self.lib.cloud_type == '115':
            newPath: str = path.replace(self.lib.path_of_115, '')
        else:
            newPath: str = path.replace(self.lib.path, '')
        newPath = newPath.lstrip(os.sep)
        return os.path.join(self.lib.strm_root_path, newPath)

    def getPrePath(self, path: str):
        pathList = path.split(os.sep)
        pathList.pop()
        return os.sep.join(pathList)

    def on_any_event(self, event):
        pass

    def on_moved(self, event):
        srcStrmPath = self.getStrmPath(event.src_path)
        destStrmPath = self.getStrmPath(event.dest_path)
        if event.is_directory:
            # preStrmPath = self.getPrePath(destStrmPath)
            # if not os.path.exists(srcStrmPath):
            #     logger.error("{0}不存在，无法移动到{1}".format(srcStrmPath, destStrmPath))
            #     return False
            # if not os.path.exists(preStrmPath):
            #     logger.info("{0}不存在，创建该目录".format(preStrmPath))
            #     os.makedirs(preStrmPath)
            # if not os.path.exists(destStrmPath):
            #     shutil.move(srcStrmPath, destStrmPath)
            #     logger.info("移动：{0} => {1}".format(srcStrmPath, destStrmPath))
            logger.warning("不处理目录移动，因为需要修改STRM文件内的路径 {0} => {1}".format(srcStrmPath, destStrmPath))
            pass
        else:
            # 检查是否STRM文件
            filename, ext = os.path.splitext(srcStrmPath)
            destFilename, ext = os.path.splitext(destStrmPath)
            srcStrmFile = srcStrmPath
            destStrmFile = destStrmPath
            if ext in self.lib.strm_ext:
                srcStrmFile = "{0}.strm".format(filename)
                destStrmFile = "{0}.strm".format(destFilename)
                if not os.path.exists(srcStrmFile):
                    logger.error("{0}不存在，无法移动到{1}".format(srcStrmFile, destStrmFile))
                    return False
            destPath = os.path.dirname(destStrmFile)
            if not os.path.exists(destPath):
                os.makedirs(destPath)
                logger.info("创建目录：{0}".format(destPath))
            shutil.move(srcStrmFile, destStrmFile)
            logger.info("移动：{0} => {1}".format(srcStrmFile, destStrmFile))
        return True
        # self.taskPool.append(timestamp = time.time())

    def on_created(self, event):
        srcStrmFile = self.getStrmPath(event.src_path)
        if os.path.exists(srcStrmFile):
            logger.info("已存在：{0}".format(srcStrmFile))
            return False
        if event.is_directory:
            if not os.path.exists(srcStrmFile):
                os.makedirs(srcStrmFile)
                logger.info("创建目录：{0}".format(srcStrmFile))
        else:
            filename, ext = os.path.splitext(srcStrmFile)
            if ext in self.lib.strm_ext:
                strmFile = "{0}.strm".format(filename)
                # 只处理strm文件
                with open(strmFile, mode='w', encoding='utf-8') as f:
                    f.write(event.src_path)
                logger.info("STRM文件: {0} => {1}".format(strmFile, event.src_path))
            if ext in self.lib.meta_ext:
                # 处理元数据
                try:
                    if self.lib.copy_meta_file == '复制':
                        shutil.copy(event.src_path, srcStrmFile)
                        logger.info("元数据复制: {0} => {1}".format(event.src_path, srcStrmFile))
                    if self.lib.copy_meta_file == '软链接':
                        os.symlink(event.src_path, srcStrmFile)
                        logger.info("元数据软链: {0} => {1}".format(event.src_path, srcStrmFile))
                except Exception as e:
                    logger.error("元数据失败: {0} => {1} : {2}".format(event.src_path, srcStrmFile, e))

    def on_deleted(self, event):
        srcStrmFile = self.getStrmPath(event.src_path)
        if event.is_directory:
            if not os.path.exists(srcStrmFile):
                logger.info("不存在，跳过删除：{0}".format(srcStrmFile))
                return False
            shutil.rmtree(srcStrmFile)
            logger.info("删除目录: {0}".format(srcStrmFile))
        else:
            filename, ext = os.path.splitext(event.src_path)
            if ext in self.lib.strm_ext:
                # 尝试删除strm文件
                strmFile = "{0}.strm".format(filename)
                if os.path.exists(strmFile):
                    os.unlink(strmFile)
                    logger.info("删除STRM: {0}".format(strmFile))
            else:
                if os.path.exists(srcStrmFile):
                    os.unlink(srcStrmFile)
                    logger.info("删除其他文件: {0}".format(srcStrmFile))
                
        return True
        # self.taskPool.append(timestamp = time.time())

    def on_modified(self, event):
        pass

def watch(key: str) -> ObservedWatch | None:
    try:
        eventHandler = FileEventHandler(key)
        if eventHandler.lib.cloud_type == '115':
            watchObj = ob.schedule(eventHandler,os.path.join(eventHandler.lib.path_of_115, eventHandler.lib.path), recursive=True) # 指定监控路径/触发对应的监控事件类
        else:
            watchObj = ob.schedule(eventHandler,os.path.join(eventHandler.lib.path), recursive=True) # 指定监控路径/触发对应的监控事件类
        return watchObj
    except Exception as e:
        logger.info('同步目录[{0}]无法启动监控任务\n {1}'.format(key, e))
        return None

def StartWatch():
    global pool
    global ob
    def stop(sig, frame):
        ob.unschedule_all()
        ob.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    # 启动一个队列处理线程
    # fst = Thread(target=doFailedQueue)
    # fst.start()
    # logger.info('失败重试服务已启动')
    path_of_115 = ''
    isStart = False
    while(True):
        libs = LIBS.list()
        if len(libs) == 0:
            logger.info('没有需要监控的目录，等待10s')
            time.sleep(10)
            continue
        # logger.info("开始检测115挂载是否失效")
        # if path_of_115 != "":
        #     if not os.path.exists(path_of_115):
        #         # 挂载丢失，停止全部线程，等待重试
        #         logger.warning('115挂载丢失，将结束全部监控线程，等待30s重试')
        #         ob.unschedule_all()
        #         ob.stop()
        #         isStart = False
        #         pool = {}
        #         time.sleep(60)
        #     else:
        #         logger.info('115挂载正常')
        
        # 开始处理同步目录
        for item in libs:
            # if item.cloud_type == '115' and item.type == '本地路径' and path_of_115 == '':
            #     path_of_115 = os.path.join(item.path_of_115, item.path)
            #     logger.info("检测挂载路径是否失效的路径：%s" % path_of_115)
            # 检查是否存在进程
            try:
                p = pool.get(item.key)
                if item.sync_type != '监控变更' and p is not None:
                    # 结束进程
                    logger.info('同步目录[%s]的同步方式变更为非监控，终止监控任务' % item.path)
                    ob.unschedule(p)
                    del pool[item.key]
                    continue
                if item.sync_type == '监控变更' and p is None:
                    # 启动新的子进程
                    watchObj = watch(item.key)
                    if watchObj is not None:
                        pool[item.key] = watchObj
                        logger.info('新增同步目录[%s]监控任务' % item.path)
                    continue
            except Exception as e:
                logger.error("同步目录处理失败 [{0}] : {1}".format(item.path, e))
                continue
        # 开始查找已经删除的任务
        for key in pool:
            item = LIBS.getLib(key)
            if item is not None:
                continue
            # 同步目录已删除，终止任务
            try:
                watchObj = pool.get(key)
                ob.unschedule(watchObj)
            except Exception as e:
                logger.error("监控任务停止失败 [{0}] : {1}".format(item.path, e))
            del pool[key]
            logger.info('同步目录[%s]已删除，终止监控任务' % item.path)
        try:
            if isStart is False:
                ob.start()
                isStart = True
                logger.info("已启动全部监控任务")
            #logger.info('已启动所有监控任务，开始10s一次检测任务执行状态')
            time.sleep(10)
        except Exception as e:
            logger.error("监控任务停止: {1}".format(e))
            break

if __name__ == '__main__':
    StartWatch()
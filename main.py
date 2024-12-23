from multiprocessing import Process
import signal, sys, shutil
import time
from typing import Mapping
from watchdog.observers import Observer
from watchdog.events import *

from lib import Lib, Libs
from log import getLogger

LIBS = Libs()
logger = getLogger(name='watch', rotating=True, stream=True)

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
                if self.lib.copy_meta_file == '复制':
                    shutil.copy(event.src_path, srcStrmFile)
                    logger.info("元数据复制: {0} => {1}".format(event.src_path, srcStrmFile))
                if self.lib.copy_meta_file == '软链接':
                    os.symlink(event.src_path, srcStrmFile)
                    logger.info("元数据软链: {0} => {1}".format(event.src_path, srcStrmFile))
        # self.taskPool.append(timestamp = time.time())

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


def watch(key: str):
    observer = Observer() # 定义监控类,多线程类 thread class
    def stop(sig, frame):
        observer.stop()
        sys.exit(0)
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    try:
        eventHandler = FileEventHandler(key)
        if eventHandler.lib.cloud_type == '115':
            observer.schedule(eventHandler,os.path.join(eventHandler.lib.path_of_115, eventHandler.lib.path), recursive=True) # 指定监控路径/触发对应的监控事件类
        else:
            observer.schedule(eventHandler,os.path.join(eventHandler.lib.path), recursive=True) # 指定监控路径/触发对应的监控事件类
        observer.start()# 将observer运行在同一个线程之内,不阻塞主进程运行,可以调度observer来停止该线程
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    except Exception as e:
        logger.info('同步目录[{0}]无法启动监控任务\n {1}'.format(key, e))
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
            # logger.info('没有需要监控的目录，等待下次触发')
            time.sleep(10)
            continue
        for item in libs:
            # 检查是否存在进程
            p = pool.get(item.key)
            if item.sync_type != '监控变更':
                if p is not None:
                    # 结束进程
                    logger.info('同步目录[%s]的同步方式变更为非监控，终止监控任务' % item.path)
                    p.terminate()
                    del pool[item.key]
            else:
                if p is None:
                    # 启动新的子进程
                    p = Process(target=watch, kwargs={'key': item.key})
                    p.start()
                    pool[item.key] = p
                    logger.info('新增同步目录[%s]监控任务' % item.path)
        libList = LIBS.libList
        for key in pool:
            item = libList.get(key)
            if item is None:
                # 同步目录已删除，终止任务
                pool[key].terminate()
                del pool[key]
                logger.info('同步目录[%s]已删除，终止监控任务' % item.path)
        try:
            time.sleep(10)
        except:
            break

if __name__ == '__main__':
    StartWatch()
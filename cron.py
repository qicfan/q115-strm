
import hashlib
from multiprocessing import Process
import os
import time
from crontab import CronTab

from lib import TABFILE, Libs
from log import getLogger

cronSubProc: Process | None = None
logger = getLogger(name='cron', rotating=True, stream=True)

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

def startCronSub():
    logger.info('启动Crontab守护进程')
    tab = CronTab(tabfile=TABFILE)
    try:
        for result in tab.run_scheduler():
            logger.info("Return code: {0}".format(result.returncode))
            logger.info("Standard Out: {0}".format(result.stdout))
            logger.info("Standard Err: {0}".format(result.stderr))
    except:
        pass

def StartCron():
    if not os.path.exists(TABFILE):
        with open(TABFILE, mode='w', encoding='utf-8') as f:
            f.write('')
    LIBS = Libs()
    # 启动定时任务服务
    LIBS.initCron()
    logger.info("启动定时任务监控进程")
    cronSubProc = Process(target=startCronSub)
    cronSubProc.start()
    md5 = get_file_md5(TABFILE)
    logger.info("记录cron文件的指纹：{0}".format(md5))
    while(True):
        newmd5 = get_file_md5(TABFILE)
        if md5 != newmd5:
            logger.info("cron文件有变化，重新加载定时任务{0} : {1}".format(md5, newmd5))
            # 有变化，重启进程
            cronSubProc.terminate()
            cronSubProc = Process(target=startCronSub)
            cronSubProc.start()
            md5 = newmd5
        # else:
        #     print("cron文件没有变化，等待10秒重试")
        try:
            # logger.info('已启动所有定时任务，开始10s一次检测任务执行状态')
            time.sleep(10)
        except:
            break

if __name__ == '__main__':
    StartCron()

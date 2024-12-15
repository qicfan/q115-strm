from multiprocessing import Process
import signal
import os, sys

from cron import StartCron
from server import StartServer
from watch import StartWatch



cronProcess: Process | None = None
watchProcess: Process | None = None

def stop(sig, frame):
    if watchProcess is not None:
        watchProcess.terminate()
    if cronProcess is not None:
        cronProcess.terminate()
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    
    if not os.path.exists('./data/logs'):
        os.makedirs('./data/logs')
    if not os.path.exists('./data/config'):
        os.makedirs('./data/config')
    # 启动监控服务
    watchProcess = Process(target=StartWatch)
    watchProcess.start()
    cronProcess = Process(target=StartCron)
    cronProcess.start()
    # 启动web服务
    StartServer()
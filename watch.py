import sys
import time
import logging
from watchdog.observers import Observer # 监控
from watchdog.events import LoggingEventHandler # 触发事件

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    event_handler = LoggingEventHandler() # 监控处理事件的方法,这个类非常重要,可以根据自己的需要重写
    observer = Observer() # 定义监控类,多线程类 thread class
    observer.schedule(event_handler,'F:\\115', recursive=True) # 指定监控路径/触发对应的监控事件类
    observer.start()# 将observer运行在同一个线程之内,不阻塞主进程运行,可以调度observer来停止该线程
    try:
        while True:
            time.sleep(1) # 监控频率（1s1次，根据自己的需求进行监控）
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

import argparse
import shutil
import signal
import textwrap
import time
import urllib
import urllib.parse

from p115client import P115Client, tool
import telegramify_markdown
from lib import OO5, GetNow, Lib, Libs, OO5List, TGBot
import os, logging, sys
from telegramify_markdown import customize

from log import getLogger

LIBS = Libs()
o5List = OO5List()


class Job:
    key: str
    lib: Lib
    oo5Account: OO5
    logger: logging

    copyList: list[str]

    def __init__(self, key: str = None, logStream: bool = False):
        if key is None:
            return
        self.key = key
        self.lib = LIBS.getLib(key)
        if self.lib is None:
            raise ValueError('要执行的同步目录不存在，请刷新同步目录列表检查是否存在')
        self.logger = getLogger(name = self.lib.key, clear=True, stream=logStream)
        if self.lib.cloud_type == '115':
            self.oo5Account = o5List.get(self.lib.id_of_115)
            if self.oo5Account is None:
                self.logger.error('无法找到所选的115账号，请检查115账号列表中是否存在此项: %s' % self.lib.id_of_115)
                raise ValueError('无法找到所选的115账号，请检查115账号列表中是否存在此项')
        if self.lib.extra.pid > 0:
            self.logger.error('正在同步中，跳过本次执行')
            raise ValueError('正在同步中，跳过本次执行')

    def start(self):
        # 记录开始时间
        # 记录进程号
        self.lib.extra.last_sync_at = GetNow()
        self.lib.extra.pid = os.getpid()
        self.lib.extra.status = 2
        # 保存
        LIBS.saveExtra(self.lib)
        bot = TGBot()
        rs, msg = bot.sendMsg("{0} 开始同步".format(self.lib.name))
        if rs:
            lm = "成功发送开始同步通知"
            if msg != "":
                lm = "无法发送通知：{0}".format(msg)
            self.logger.info(lm)
        else:
            self.logger.warning("无法发送通知: {0}".format(msg))
        self.lib = LIBS.getLib(self.key)
        try:
            if self.lib.cloud_type == '115':
                self.work()
            else:
                self.workOther()
            self.lib.extra.status = 1
            customize.strict_markdown = False
            tgmesage = """
*{0}* 已完成同步

- *STRM文件*: 本次找到 {1} 个， 生成 {2} 个
- *元数据*: 本次找到 {3} 个, 成功 {4} 个
- *删除文件*: 本次找到 {5} 个，成功 {6} 个
"""
            markdown_text = textwrap.dedent(tgmesage.format(self.lib.name, self.lib.extra.last_sync_result['strm'][1], self.lib.extra.last_sync_result['strm'][0], self.lib.extra.last_sync_result['meta'][0], self.lib.extra.last_sync_result['meta'][0], self.lib.extra.last_sync_result['delete'][0], self.lib.extra.last_sync_result['delete'][0]))
            can_be_sent = telegramify_markdown.markdownify(markdown_text)
            rs, msg = bot.sendMsg(can_be_sent)
            if rs:
                lm = "成功发送同步完成通知"
                if msg != "":
                    lm = "无法发送通知：{0}".format(msg)
                self.logger.info(lm)
            else:
                self.logger.warning("无法发送通知: {0}".format(msg))
        except Exception as e:
            self.logger.error('%s' % e)
            self.lib.extra.status = 3
            rs, msg = bot.sendMsg("{0} 同步发生错误： \n {1}".format(self.lib.name, e))
            if rs:
                lm = "成功发送同步错误通知"
                if msg != "":
                    lm = "无法发送通知：{0}".format(msg)
                self.logger.info(lm)
            else:
                self.logger.warning("无法发送通知: {0}".format(msg))
        self.lib.extra.pid = 0
        LIBS.saveExtra(self.lib)
        return True
    
    def stop(self, sig, frame):
        self.lib.extra.status = 3
        self.lib.extra.pid = 0
        LIBS.saveExtra(self.lib)
        sys.exit(1)

    def workOther(self):
        copy_list = []
        src_tree_list = self.get_dest_tree_list(self.lib.path, self.lib.path, [])
        dest_tree_list = self.get_dest_tree_list(self.lib.strm_root_path, self.lib.strm_root_path, [])
        added = []
        for src_item in src_tree_list:
            if src_item in dest_tree_list:
                # 已存在，从dest中删除
                dest_tree_list.remove(src_item)
                continue
            filename, ext = os.path.splitext(src_item)
            if ext in self.lib.strm_ext:
                strm_file = filename + '.strm'
                if strm_file in dest_tree_list:
                    # 如果strm文件已存在，则从dest中删除
                    dest_tree_list.remove(strm_file)
                    continue
                else:
                    added.append(src_item)
                    continue
            if ext in self.lib.meta_ext:
                # 如果是元数据，则加入复制列表
                copy_list.append(src_item)
            
        # added是要添加的, dest_tree_list剩下的是要删除的， copy_list是要复制的元数据
        # 处理删除
        c = 0
        dt = len(dest_tree_list)
        ds = 0
        df = 0
        for delete_item in dest_tree_list:
            c += 1
            delete_real_dir = os.path.join(self.lib.strm_root_path, delete_item)
            if os.path.exists(delete_real_dir):
                # 只删除strm文件
                _, deleted_ext = os.path.splitext(delete_item)
                if deleted_ext != '.strm':
                    self.logger.error('[%d / %d] 错误：%s \n %s' % (c, dt, delete_item, '只会删除STRM文件'))
                    df += 1
                    continue
                try:
                    os.unlink(delete_real_dir)
                    self.logger.info('[%d / %d] 删除：%s' % (c, dt, delete_item))
                    ds += 1
                except OSError as e:
                    self.logger.error('[%d / %d] 错误：%s \n %s' % (c, dt, delete_item, e))
                    df += 1
            else:
                self.logger.error('[%d / %d] 错误：%s \n %s' % (c, dt, delete_item, '文件已经不存在'))
                df += 1
                continue

        # 处理添加
        c = 0
        at = len(added)
        asuc = 0
        af = 0
        for item in added:
            c += 1
            rs = self.strm(item)
            if rs == '':
                # 成功
                asuc += 1
                self.logger.info('[%d / %d] STRM：%s' % (c, at, item))
            else:
                af += 1
                self.logger.error('[%d / %d] 错误：%s \n %s' % (c, at, item, rs))
        # 处理元数据
        if self.lib.type == 'WebDAV':
            self.logger.info('webdav不处理元数据')
        else:
            if self.lib.copy_meta_file != '关闭':
                c = 0
                ct = len(copy_list)
                cs = 0
                cf = 0
                for item in copy_list:
                    c += 1
                    src_file = os.path.join(self.lib.path, item)
                    dest_file = os.path.join(self.lib.strm_root_path, item)
                    dirname = os.path.dirname(dest_file)
                    if not os.path.exists(dirname):
                        os.makedirs(dirname)
                    if not os.path.exists(src_file):
                        cf += 1
                        self.logger.error('[%d / %d] 元数据 - 源文件不存在：%s' % (c, ct, src_file))
                        continue
                    try:
                        if self.lib.copy_meta_file == '复制':
                            self.logger.info('[%d / %d] 元数据 - 复制：%s => %s' % (c, ct, src_file, dest_file))
                            shutil.copy(src_file, dest_file)
                            time.sleep(self.lib.copy_delay)
                        if self.lib.copy_meta_file == '软链接':
                            self.logger.info('[%d / %d] 元数据 - 软链：%s' % (c, ct, item))
                            os.symlink(src_file, dest_file)
                        cs += 1
                    except OSError as e:
                        self.logger.error('[%d / %d] 元数据 - 复制错误：%s \n %s' % (c, ct, item, e))
                        cf += 1
                self.logger.info('元数据结果：成功: {0}, 失败: {1}, 总共: {2}'.format(cs, cf, ct))
                self.lib.extra.last_sync_result['meta'] = [cs, ct]
        self.logger.info('删除结果：成功: {0}, 失败: {1}, 总共: {2}'.format(ds, df, dt))
        self.logger.info('STRM结果：成功: {0}, 失败: {1}, 总共: {2}'.format(asuc, af, at))
        self.lib.extra.last_sync_result['strm'] = [asuc, at]
        self.lib.extra.last_sync_result['delete'] = [ds, dt]

    def work(self):
        copy_list = []
        src_tree_list = self.get_src_tree_list()
        strm_base_dir = os.path.join(self.lib.strm_root_path, self.lib.path)
        dest_tree_list = self.get_dest_tree_list(self.lib.strm_root_path, strm_base_dir, [self.lib.path])
        added = []
        for src_item in src_tree_list:
            if src_item in dest_tree_list:
                # 已存在，从dest中删除
                dest_tree_list.remove(src_item)
                continue
            filename, ext = os.path.splitext(src_item)
            if ext in self.lib.strm_ext:
                strm_file = filename + '.strm'
                if strm_file in dest_tree_list:
                    # 如果strm文件已存在，则从dest中删除
                    dest_tree_list.remove(strm_file)
                    continue
                else:
                    added.append(src_item)
                    continue
            if ext in self.lib.meta_ext:
                # 如果是元数据，则加入复制列表
                copy_list.append(src_item)
            
        # added是要添加的, dest_tree_list剩下的是要删除的， copy_list是要复制的元数据
        # 处理删除
        c = 0
        dt = len(dest_tree_list)
        ds = 0
        df = 0
        for delete_item in dest_tree_list:
            c += 1
            delete_real_dir = os.path.join(self.lib.strm_root_path, delete_item)
            if os.path.exists(delete_real_dir):
                # 只删除strm文件
                _, deleted_ext = os.path.splitext(delete_item)
                if deleted_ext != '.strm':
                    self.logger.error('[%d / %d] 错误：%s \n %s' % (c, dt, delete_item, '只会删除STRM文件'))
                    df += 1
                    continue
                try:
                    os.unlink(delete_real_dir)
                    self.logger.info('[%d / %d] 删除：%s' % (c, dt, delete_item))
                    ds += 1
                except OSError as e:
                    self.logger.error('[%d / %d] 错误：%s \n %s' % (c, dt, delete_item, e))
                    df += 1
            else:
                self.logger.error('[%d / %d] 错误：%s \n %s' % (c, dt, delete_item, '文件已经不存在'))
                df += 1
                continue

        # 处理添加
        c = 0
        at = len(added)
        asuc = 0
        af = 0
        for item in added:
            c += 1
            rs = self.strm(item)
            if rs == '':
                # 成功
                asuc += 1
                self.logger.info('[%d / %d] STRM：%s' % (c, at, item))
            else:
                af += 1
                self.logger.error('[%d / %d] 错误：%s \n %s' % (c, at, item, rs))
        # 处理元数据
        if self.lib.type == 'WebDAV':
            self.logger.info('webdav不处理元数据')
        else:
            if self.lib.copy_meta_file != '关闭':
                c = 0
                ct = len(copy_list)
                cs = 0
                cf = 0
                for item in copy_list:
                    c += 1
                    src_file = os.path.join(self.lib.path_of_115, item)
                    dest_file = os.path.join(self.lib.strm_root_path, item)
                    dirname = os.path.dirname(dest_file)
                    if not os.path.exists(dirname):
                        os.makedirs(dirname)
                    if not os.path.exists(src_file):
                        cf += 1
                        self.logger.error('[%d / %d] 元数据 - 源文件不存在：%s' % (c, ct, src_file))
                        continue
                    try:
                        if self.lib.copy_meta_file == '复制':
                            self.logger.info('[%d / %d] 元数据 - 复制：%s' % (c, ct, item))
                            shutil.copy(src_file, dest_file)
                            time.sleep(self.lib.copy_delay)
                        if self.lib.copy_meta_file == '软链接':
                            self.logger.info('[%d / %d] 元数据 - 软链：%s' % (c, ct, item))
                            os.symlink(src_file, dest_file)
                        cs += 1
                    except OSError as e:
                        self.logger.error('[%d / %d] 元数据 - 复制错误：%s \n %s' % (c, ct, item, e))
                        cf += 1
                self.logger.info('元数据结果：成功: {0}, 失败: {1}, 总共: {2}'.format(cs, cf, ct))
                self.lib.extra.last_sync_result['meta'] = [cs, ct]
        self.logger.info('删除结果：成功: {0}, 失败: {1}, 总共: {2}'.format(ds, df, dt))
        self.logger.info('STRM结果：成功: {0}, 失败: {1}, 总共: {2}'.format(asuc, af, at))
        self.lib.extra.last_sync_result['strm'] = [asuc, at]
        self.lib.extra.last_sync_result['delete'] = [ds, dt]

    def get_src_tree_list(self):
        ### 解析115目录树，生成目录数组
        try:
            client = P115Client(self.oo5Account.cookie)
            it = tool.export_dir_parse_iter(client=client, export_file_ids=self.lib.path, target_pid=self.lib.path, parse_iter=tool.parse_export_dir_as_dict_iter, 
                                delete=True, async_=False, show_clock=True)
            i = 0
            path_index = {}
            src_tree_list = []
            for item in it:
                i += 1
                parent = path_index.get(item['parent_key'])
                if parent is None:
                    item['path'] = ''
                else:
                    if i == 2 and self.lib.path.endswith(item['name']):
                        item['path'] = self.lib.path
                    else:
                        item['path'] = os.path.join(parent['path'], item['name'].lstrip())
                path_index[item['key']] = item
                if item['path'] != '':
                    src_tree_list.append(item['path'])
            return src_tree_list
        except Exception as e:
            self.logger.error('生成目录树出错: %s' % e)
            raise e

    def get_dest_tree_list(self, base_dir: str, root_dir: str, dest_tree_list: list):
        ### 获取目标路径目录树，用于处理差异
        if not os.path.exists(root_dir):
            return dest_tree_list
        dirs = os.listdir(root_dir)
        for dir in dirs:
            if dir == '.' or dir == '..': continue
            item = os.path.join(root_dir, dir)
            # if self.lib.cloud_type == '115':
            dest_tree_list.append(item.replace(base_dir + os.sep, ''))
            # else:
            #     dest_tree_list.append(item)
            if os.path.isfile(item):
                # 如果是文件，则不用递归
                continue
            else:
                self.get_dest_tree_list(base_dir, item, dest_tree_list)
        return dest_tree_list

    def strm(self, path: str):
        try:
            path = path.replace('/', os.sep)
            dirname = os.path.dirname(path)
            real_dirname = os.path.join(self.lib.strm_root_path, dirname)
            if not os.path.exists(real_dirname):
                os.makedirs(real_dirname)
            filename, ext = os.path.splitext(path)
            # 生成STRM文件
            strm_file = filename + '.strm'
            strm_real_file = os.path.join(self.lib.strm_root_path, strm_file)
            strm_content = ''
            if self.lib.type == '本地路径':
                if self.lib.cloud_type == '115':
                    strm_content = os.path.join(self.lib.path_of_115, path)
                else:
                    strm_content = os.path.join(self.lib.path, path)
            else:
                path = path.replace(os.sep, '/')
                if self.lib.mount_path != '':
                    path = path.replace(self.lib.mount_path, '')
                    print("path replace mount: {0}".format(path))
                    if path.startswith('/'):
                        path.lstrip('/')
                pathList = path.split('/')
                newPath = []
                for p in pathList:
                    newPath.append(urllib.parse.quote(p))
                if self.lib.type == 'WebDAV':
                    url = self.lib.webdav_url
                    if not url.startswith('http'):
                        url = "http://{0}".format(url)
                    url = self.lib.webdav_url.replace('//', '//{0}:{1}@'.format(self.lib.webdav_username, self.lib.webdav_password))
                    if url.endswith('/'):
                        url = url.rstrip('/')
                    strm_content = '{0}/{1}'.format(url, '/'.join(newPath))
                else:
                    url = self.lib.alist_server
                    if url.endswith('/'):
                        url = url.rstrip('/')
                    alist_115_path = self.lib.alist_115_path.strip('/')
                    strm_content = '{0}/d/{1}/{2}'.format(url, alist_115_path, '/'.join(newPath))
            with open(strm_real_file, 'w', encoding='utf-8') as f:
                f.write(strm_content)
            return ''
        except OSError as e:
            return e
        
def StartJob(key: str, logStream: bool = False):
    job = Job(key, logStream)
    signal.signal(signal.SIGINT, job.stop)
    signal.signal(signal.SIGTERM, job.stop)
    job.start()

if __name__ == '__main__':
    key: str = ''
    parser = argparse.ArgumentParser(prog='115-STRM', description='将挂载的115网盘目录生成STRM', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-k', '--key', help='要处理的同步目录')
    args, unknown = parser.parse_known_args()
    if args.key != None:
        key = args.key
    if key == '':
        sys.exit(0)
    StartJob(key)

from p115client import P115Client, tool
import argparse, os, json, logging, shutil, time, sys
from pathlib import Path

_special_chars_map = {i: '\\' + chr(i) for i in b'()[]{}?*+|^$\\.'}
def re_escape(s: str) -> str:
    """用来对字符串进行转义，以将转义后的字符串用于构造正则表达式"""
    pattern = s.translate(_special_chars_map)
    return pattern


def get_real_path(path):
    rel_start = os.path.dirname(__file__)
    # 确保返回的是绝对路径（__file__可能引入相对路径）
    abs_path = os.path.abspath(os.path.join(rel_start, path))
    return abs_path

class DetailedFormatter(logging.Formatter):
    """如果日志记录包含异常信息，则将传递给异常的参数一起记录下来"""
    def __init__(self, fmt='%(asctime)s %(levelname)s: %(message)s',
                 datefmt='%Y-%m-%d %H:%M:%S', *args) -> None:
        super().__init__(fmt, datefmt, *args)

real_log_file = get_real_path('tree.log')
if os.path.exists(real_log_file):
    os.remove(real_log_file)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(filename=get_real_path('tree.log'), mode='a', encoding='utf-8')
file_handler.setLevel(logging.ERROR)
file_handler.setFormatter(DetailedFormatter())
root_logger.addHandler(file_handler)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(DetailedFormatter())
root_logger.addHandler(stream_handler)

logger = logging.getLogger(__name__)

config: dict | None = None
export_dir_path: str = ''
copy_meta_file: bool = False
cloud_type: str = 'local'

config_file = os.path.abspath("./config.json")
with open(config_file, mode='r', encoding='utf-8') as fd_config:
    config = json.load(fd_config)

parser = argparse.ArgumentParser(prog='115-STRM', description='将挂载的115网盘目录生成STRM', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-e', '--export_dir_path', help='要生成目录树的路径，相对路径，不能为空')
parser.add_argument('-t', '--type', help='使用本地挂载目录或者alist，可选值：local, alist')
parser.add_argument('-c', '--copy_meta_file', type=int, help='是否复制元数据，可选值：0, 1，0-不复制，1-复制')
args, unknown = parser.parse_known_args()
if args.copy_meta_file != None:
    copy_meta_file = args.copy_meta_file
if args.export_dir_path != None:
    export_dir_path = args.export_dir_path
if args.type != None:
    cloud_type = args.type
if cloud_type == 'local' and config['local']['root_dir'] == '':
    logger.error('使用本地挂载模式时，必须配置local.root_dir，当前为空，清修改config.json')
    sys.exit(1)
if cloud_type == 'alist' and (config['alist']['root_url'] == '' or config['alist']['username'] == '' or config['alist']['password'] == ''):
    logger.error('使用alist模式时，必须配置alist.root_url和用户名密码，当前为空，请修改config.json')
    sys.exit(1)

ed = export_dir_path.split('/')
edr = os.sep.join(ed)
dest_tree_list = []

def work():
    copy_list = []
    src_tree_list = get_src_tree_list()
    strm_base_dir = os.path.join(config['strm_root_dir'], edr)
    dest_tree_list = get_dest_tree_list(config['strm_root_dir'], strm_base_dir, [edr])
    added = []
    for src_item in src_tree_list:
        if src_item in dest_tree_list:
            # 已存在，从dest中删除
            dest_tree_list.remove(src_item)
            continue
        filename, ext = os.path.splitext(src_item)
        if ext in config['strm_ext']:
            strm_file = filename + '.strm'
            if strm_file in dest_tree_list:
                # 如果strm文件已存在，则从dest中删除
                dest_tree_list.remove(strm_file)
                continue
            else:
                added.append(src_item)
                continue
        if ext in config['meta_ext']:
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
        delete_real_dir = os.path.join(config['strm_root_dir'], delete_item)
        if os.path.exists(delete_real_dir):
            try:
                os.remove(delete_real_dir)
                logger.info('[%d / %d] 删除：%s' % (c, dt, delete_item))
                ds += 1
            except OSError as e:
                logger.error('[%d / %d] 错误：%s \n %s' % (c, dt, delete_item, e))
                df += 1
    # 处理添加
    c = 0
    at = len(added)
    asuc = 0
    af = 0
    for item in added:
        c += 1
        rs = strm(item)
        if rs == '':
            # 成功
            asuc += 1
            logger.info('[%d / %d] STRM：%s' % (c, at, item))
        else:
            af += 1
            logger.error('[%d / %d] 错误：%s \n %s' % (c, at, item, e))
    # 处理元数据
    if cloud_type == 'alist':
        logger.info('alist不处理元数据')
    else:
        if copy_meta_file == True :
            c = 0
            ct = len(copy_list)
            cs = 0
            cf = 0
            for item in copy_list:
                c += 1
                src_file = os.path.join(config['local']['root_dir'], item)
                dest_file = os.path.join(config['strm_root_dir'], item)
                if not os.path.exists(src_file):
                    cf += 1
                    logger.error('[%d / %d] 元数据 - 源文件不存在：%s' % (c, ct, src_file))
                    continue
                try:
                    logger.info('[%d / %d] 元数据 - 复制：%s' % (c, ct, item))
                    shutil.copy(src_file, dest_file)
                    cs += 1
                except OSError as e:
                    logger.error('[%d / %d] 元数据 - 复制错误：%s \n %s' % (c, ct, item, e))
                    cf += 1
                time.sleep(1)
            logger.info('元数据结果：成功: {0}, 失败: {1}, 总共: {2}'.format(cs, cf, ct))
    logger.info('删除结果：成功: {0}, 失败: {1}, 总共: {2}'.format(ds, df, dt))
    logger.info('STRM结果：成功: {0}, 失败: {1}, 总共: {2}'.format(asuc, af, at))
    

def get_src_tree_list():
    ### 解析115目录树，生成目录数组
    cookies = ''
    if os.path.exists('./115-cookies.txt'):
        with open('./115-cookies.txt', mode='r', encoding='utf-8') as f:
            cookies = f.read()
    if cookies == '' and config['115-cookies'] != '':
        cookies = config['115-cookies']
    if cookies == '':
        logger.error('请先配置155 cookies')
        sys.exit(1)
    client = P115Client(Path("../strm/115-cookies.txt").expanduser(), check_for_relogin=True)
    it = tool.export_dir_parse_iter(client=client, export_file_ids=export_dir_path, target_pid=export_dir_path, parse_iter=tool.parse_export_dir_as_dict_iter, 
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
            if i == 2 and edr.endswith(item['name']):
                item['path'] = edr
            else:
                item['path'] = os.path.join(parent['path'], item['name'])
        path_index[item['key']] = item
        if item['path'] != '':
            src_tree_list.append(item['path'])
    return src_tree_list

def get_dest_tree_list(base_dir: str, root_dir: str, dest_tree_list: list):
    ### 获取目标路径目录树，用于处理差异
    if not os.path.exists(root_dir):
        return dest_tree_list
    dirs = os.listdir(root_dir)
    for dir in dirs:
        if dir == '.' or dir == '..': continue
        item = os.path.join(root_dir, dir)
        dest_tree_list.append(item.replace(base_dir + os.sep, ''))
        if os.path.isfile(item):
            # 如果是文件，则不用递归
            continue
        else:
            get_dest_tree_list(base_dir, item, dest_tree_list)
    return dest_tree_list

def strm(path: str):
    try:
        dirname = os.path.dirname(path)
        real_dirname = os.path.join(config['strm_root_dir'], dirname)
        if not os.path.exists(real_dirname):
            os.makedirs(real_dirname)
        filename, ext = os.path.splitext(path)
        # 生成STRM文件
        strm_file = filename + '.strm'
        strm_real_file = os.path.join(config['strm_root_dir'], strm_file)
        strm_content = ''
        if type == 'local':
            strm_content = os.path.join(config['local']['root_dir'], path)
        else:
            url = config['alist']['root_url'].replace('http://', '')
            strm_content = 'http://{0}:{1}@{2}/{3}'.format(config['alist']['username'], config['alist']['password'], url, path.replace(os.sep, '/'))
        with open(strm_real_file, 'w', encoding='utf-8') as f:
            f.write(strm_content)
        return ''
    except OSError as e:
        return e
    
if __name__ == '__main__':
    bt = time.time()
    work()
    et = time.time()
    tt = (et-bt) / 1000
    logger.info('执行完成，总耗时：{:.3f}秒'.format(tt))
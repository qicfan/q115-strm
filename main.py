from p115client import P115Client, tool
import argparse, os, json, logging, shutil, time
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
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(DetailedFormatter())
root_logger.addHandler(file_handler)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(DetailedFormatter())
root_logger.addHandler(stream_handler)

logger = logging.getLogger(__name__)

config: dict | None = None
export_dir_path: str = ''
copy_meta_file: bool = True

config_file = os.path.abspath("./config.json")
with open(config_file, mode='r', encoding='utf-8') as fd_config:
    config = json.load(fd_config)

parser = argparse.ArgumentParser(prog='115-STRM', description='将挂载的115网盘目录生成STRM', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-e', '--export_dir_path', help='要生成目录树的路径，相对路径，不能为空')
parser.add_argument('-c', '--copy_meta_file', type=int, help='是否复制元数据，可选值：0, 1，0-不复制，1-复制')
args, unknown = parser.parse_known_args()
if args.copy_meta_file != None:
    copy_meta_file = args.copy_meta_file
if args.export_dir_path != None:
    export_dir_path = args.export_dir_path

client = P115Client(Path("./115-cookies.txt").expanduser(), check_for_relogin=True)

def work():
    global config
    global copy_meta_file
    global export_dir_path
    it = tool.export_dir_parse_iter(client=client, export_file_ids=export_dir_path, target_pid=export_dir_path, parse_iter=tool.parse_export_dir_as_dict_iter, 
                           delete=True, async_=False, show_clock=True)
    i = 0
    path_index = {}
    copy_list = []
    ed = export_dir_path.split('/')
    edr = os.sep.join(ed)
    cloud_base_dir = os.path.join(config['cloud_mount_root_dir'], edr)
    strm_base_dir = os.path.join(config['strm_root_dir'], edr)
    if not os.path.exists(strm_base_dir): 
        os.makedirs(strm_base_dir)
    for item in it:
        i += 1
        parent = path_index.get(item['parent_key'])
        if parent is None:
            item['path'] = ''
        else:
            if i == 2 and cloud_base_dir.endswith(item['name']):
                item['path'] = ''
            else:
                item['path'] = os.path.join(parent['path'], item['name'])
        item['create'] = False
        path_index[item['key']] = item
        if i == 1 or parent['name'] == '':
            continue
        if parent['create'] is False:
            # 处理父级，创建目录
            parent['create'] = True
            parent_dest_dir = os.path.join(strm_base_dir, parent['path'])
            if os.path.exists(parent_dest_dir):
                logger.info('目录 - 存在：' + parent_dest_dir)
            else:
                os.mkdir(parent_dest_dir)
                logger.info('目录 - 创建：' + parent_dest_dir)       
        filename, ext = os.path.splitext(item['path'])
        if ext in config['strm_ext']:
            # 需要生成strm
            try:
                content = os.path.join(cloud_base_dir, item['path'])
                strm_file = os.path.join(strm_base_dir, filename + '.strm')
                if os.path.exists(strm_file):
                    logger.info('文件 - 存在：' + strm_file)
                else:
                    with open(strm_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info('文件 - 生成strm：' + strm_file)
            except OSError as e:
                logger.info('文件 - 生成strm：{0} \n {1}'.format(strm_file, e))
        if ext in config['meta_ext']:
            copy_list.append(item['path'])
    c = 1
    t = len(copy_list)
    for copy_item in copy_list:
        src_file = os.path.join(cloud_base_dir, copy_item)
        dest_file = os.path.join(strm_base_dir, copy_item)
        try:
            shutil.copy(src_file, dest_file)
            logger.info('[%d / %d] 元数据 - 已复制：%s' % (c, t, copy_item))
        except OSError:
            pass
        c += 1
        time.sleep(1)

if __name__ == '__main__':
    work()
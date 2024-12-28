import argparse
import json
import os
import sys

if not os.path.exists('./data/logs'):
    os.makedirs('./data/logs')
if not os.path.exists('./data/config'):
    os.makedirs('./data/config')

from job import StartJob
from lib import OO5, Lib, Libs, OO5List
from rich import print as rprint
from rich.prompt import Prompt, Confirm, FloatPrompt
from rich.console import Console
from rich.table import Table

LIBS = Libs()
o5List = OO5List()

def listLib():
    libList = LIBS.list()
    if len(libList) == 0:
        rprint('[bold red]还没有添加任何同步目录[/]')
        return
    table = Table(title="同步目录列表")

    table.add_column("KEY", justify="left", style="cyan", no_wrap=True)
    table.add_column("网盘类型",)
    table.add_column("名称", style="magenta")
    table.add_column("目录树路径", justify="right", style="green")
    table.add_column("方式", justify="right", style="red")
    for lib in libList:
        table.add_row(lib.key, lib.cloud_type, lib.name, lib.path, lib.type)
    console = Console()
    console.print(table)

def run(key: str | None = None):
    if key != None:
        StartJob(key, logStream=True)
        return
    # 循环执行所有目录
    libs = LIBS.list()
    for lib in libs:
        StartJob(lib.key, logStream=True)

def add115():
    # 添加115账号
    oo5 = {}
    oo5['cookie'] = Prompt.ask("[green]cookie[/] 请输入115的cookie，您可以通过其他途径获取")
    if oo5['cookie'] == '':
        rprint("[bold red]cookie必须输入/]")
        return
    oo5['name'] = Prompt.ask("[green]name[/] 请输入该cookie的名字，好记就行，如：账号1")
    if oo5['name'] == '':
        rprint("[bold red]名字必须输入/]")
        return
    rs, msg = o5List.add(oo5)
    if not rs:
        rprint("添加失败: [bold red]{0}[/]".format(msg))
        return
    rprint("115账号{0}已添加".format(oo5['name']))
    rprint('如果cookie失效，您可以在[bold]./data/config/115.json[/]文件中修改对应的cookie')
    return

def create():
    tmpFile = './.input'
    def saveTmp():
        with open(tmpFile, mode='w', encoding='utf-8') as f:
            json.dump(lib.getJson(), f)
        pass
    def readTmp():
        if not os.path.exists(tmpFile):
            return {}
        with open(tmpFile, mode='r', encoding='utf-8') as f:
            dict = json.load(f)
        return dict
    isWin = sys.platform.startswith('win')
    tmp = readTmp()
    if tmp.get('path') is not None:
        rprint("已经将上一次输入的值设置为每一项的默认值，[bold]如果没有改动可以直接回车[/]，直到未完成的输入项")
    lib = Lib(tmp)
    # 选择网盘类型
    o5s: list[OO5] = o5List.getList()
    if len(o5s) == 0:
        rprint("[bold red]请先添加115账号，执行：q115strm.exe add115[/]")
        return
    # 生成选择项
    oo5Choices = []
    oo5Default = o5s[0].name
    for o in o5s:
        if lib.id_of_115 != '' and lib.id_of_115 == o.key:
            oo5Default = o.name
        oo5Choices.append(o.name)
    oo5Name =  Prompt.ask("[green]id_of_115[/] 请选择要使用的115账号", choices=oo5Choices, default=oo5Default)
    for o in o5s:
        if oo5Name == o.name:
            lib.id_of_115 = o.key
    lib.path = Prompt.ask("[green]path[/] 请输入要生成目录树的115路径，如：media/movie", default=lib.path)
    if lib.path == '':
        rprint("[bold red]路径必须输入[/]")
        return
    lib.path = lib.path.strip('/')
    saveTmp()
    lib.name = Prompt.ask("[green]name[/] 请输入该路径的名称，如：电影", default=lib.name if lib.name != '' else "默认目录")
    saveTmp()
    strm_root_path_example = '/115'
    if isWin:
        strm_root_path_example = 'F:\\115'
    lib.strm_root_path = Prompt.ask("[green]strm_root_path[/] 请输入存放STRM文件的根目录，如：%s" % strm_root_path_example, default=lib.strm_root_path)
    if lib.strm_root_path == '':
        rprint("[bold red]STRM文件的根目录必须输入/]")
        return
    lib.strm_root_path = lib.strm_root_path.rstrip(os.sep)
    if not os.path.exists(lib.strm_root_path):
        mk_strm_root_path = Confirm.ask("[bold red]{0}不存在[/]，是否创建该目录?".format(lib.strm_root_path), default=True)
        if mk_strm_root_path:
            os.makedirs(lib.strm_root_path)
        else:
            rprint("[bold red]请输入正确的strm根目录[/]")
            return
    saveTmp()
    lib.type = Prompt.ask("[green]type[/] 请选择STRM类型", choices=["本地路径", "WebDAV", "alist302"], default=lib.type)
    saveTmp()
    lib.mount_path = Prompt.ask("[green]mount_path[/] 如果使用Alist请输入Alist创建存储时输入的根文件夹ID对应的路径", default=lib.mount_path)
    lib.mount_path = lib.mount_path.strip('/')
    saveTmp()
    if lib.type == '本地路径':
        lib.path_of_115 = Prompt.ask("[green]path_of_115[/] 请输入挂载115的目录，例如CD2的/CloudNAS/115", default=lib.path_of_115)
        if (lib.path_of_115 == ''):
            rprint("[bold red]115挂载目录必须输入[/]")
            return
        if not os.path.exists(lib.path_of_115):
            rprint("[bold red]{0}不存在，请检查CD2或其他挂载服务是否正常启动，挂载目录是否输入正确[/]".format(lib.path_of_115))
            return
        lib.path_of_115 = lib.path_of_115.rstrip(os.sep)
        saveTmp()
        lib.copy_meta_file= Prompt.ask("[green]copy_meta_file[/] 是否复制元数据?", default=lib.copy_meta_file, choices=["关闭", "复制", "软连接"])
        if lib.copy_meta_file == '复制':
            lib.copy_delay = FloatPrompt.ask("[green]copy_delay[/] 每个元数据复制的间隔秒数，支持两位小数如：0.01, 默认1秒?", default=float(lib.copy_delay))
        saveTmp()
    if lib.type == 'WebDAV':
        lib.webdav_url = Prompt.ask("[green]webdav_url[/] 请输入webdav服务中的115挂载路径, 格式：http[s]//ip:port/[dav/115]", default=lib.webdav_url)
        if (lib.webdav_url == ''):
            rprint("[bold red]webdav服务的url必须输入[/]")
            return
        lib.webdav_url = lib.webdav_url.rstrip('/')
        saveTmp()
        lib.webdav_username = Prompt.ask("[green]webdav_username[/] 请输入webdav服务的登录用户名，只是用字母和数字不要包含特殊字符", default=lib.webdav_url)
        if (lib.webdav_username == ''):
            rprint("[bold red]webdav服务的登录用户名必须输入[/]")
            return
        saveTmp()
        lib.webdav_password = Prompt.ask("[green]webdav_password[/] 请输入webdav服务的登录密码，只是用字母和数字不要包含特殊字符", default=lib.webdav_url)
        if (lib.webdav_password == ''):
            rprint("[bold red]webdav服务的登录密码必须输入[/]")
            return
        saveTmp()
    if lib.type == 'alist302':
        lib.alist_server = Prompt.ask("[green]alist_server[/] 请输入alist地址, 格式：http[s]//ip:port", default=lib.alist_server)
        if (lib.alist_server == ''):
            rprint("[bold red]alist地址l必须输入[/]")
            return
        lib.alist_server = lib.alist_server.rstrip('/')
        saveTmp()
        lib.alist_115_path = Prompt.ask("[green]alist_115_path[/] 请输入alist存储中115的挂载路径", default=lib.alist_115_path)
        if (lib.alist_115_path == ''):
            rprint("[bold red]webdav服务的登录用户名必须输入[/]")
            return
        lib.alist_115_path = lib.alist_115_path.strip('/')
        saveTmp()
    strmExtStr = ';'.join(lib.strm_ext)
    newStrmExtStr = Prompt.ask("[green]strm_ext[/] 请输入要生成STRM的文件扩展名，分号分隔，可以直接复制默认值来修改", default=strmExtStr)
    strmExtList = newStrmExtStr.split(';')
    i = 0
    for ext in strmExtList:
        if not ext.startswith('.'):
            strmExtList[i] = ".{0}".format(ext).strip()
        i += 1
    lib.strm_ext = strmExtList
    saveTmp()
    if lib.copy_meta_file != '关闭':
        metaExtStr = ';'.join(lib.meta_ext)
        newMetaExtStr = Prompt.ask("[green]strm_ext[/] 请输入元数据的文件扩展名，分号分隔，可以直接复制默认值来修改", default=metaExtStr)
        metaExtList = newMetaExtStr.split(';')
        i = 0
        for ext in metaExtList:
            if not ext.startswith('.'):
                metaExtList[i] = ".{0}".format(ext).strip()
            i += 1
        lib.meta_ext = metaExtList
        saveTmp()
    lib.makeKey()
    rs, msg = LIBS.add(lib.getJson())
    if not rs:
        rprint("添加失败：[bold red]{0}[/]".format(msg))
        return
    rprint("已添加同步目录: %s" % lib.key)
    rprint("您也可以在 [bold]data/config/libs.json[/] 中手动修改需要的参数")
    if isWin:
        rprint("稍后可执行 .\\q115strm.exe run -k={0} 执行单个同步任务 或者 .\\q115strm.exe run 执行全部同步任务".format(lib.key))
    else:
        rprint("稍后可执行 ./q115strm run -k={0} 执行单个同步任务 或者 ./q115strm run 执行全部同步任务".format(lib.key))
    os.unlink('.input')
    
    
if __name__ == '__main__':
    action: str | None = None
    key: str | None = None
    parser = argparse.ArgumentParser(prog='115-STRM', description='将挂载的115网盘目录生成STRM', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('action', help='要执行的操作\nlist 列出所有已添加的同步目录\nadd115 添加115账号的cookie \ncreate 添加同步目录\nrun 执行同步任务')
    parser.add_argument('-k', '--key', help='要处理的同步目录')
    args, unknown = parser.parse_known_args()
    if args.action != None:
        action = args.action
    if args.key != None:
        key = args.key
    if action == '':
        sys.exit(0)
    if action == 'list':
        listLib()
    if action == 'create':
        create()
    if action == 'run':
        run(key)
    if action == 'add115':
        add115()
## 介绍
##### 基于[p115client](https://github.com/ChenyangGao/p115client)开发，通过生成115目录树来快速完成STRM文件创建，由于只有一次请求所以不会触发风控
##### 不建议复制元数据，目前写死了1秒复制一个文件，加上网络传输，可能要好几秒才能处理一个文件，如果第一次扫盘有上万个文件可能要持续好几个小时。可以配合刮削器（如TMM）对生成的STRM文件再次刮削

## 特性
- 使用115目录树，只有一次请求，不会风控，后续操作都不会跟115交互
- 支持两种使用模式
    - 本地挂载目录：主要是CD2，会将媒体文件的真实路径写入STRM文件，支持复制元数据
    - webdav：主要是alist，会讲媒体文件的webdav地址写入STRM文件，不支持复制元数据，如果alist存储选择了302，则支持直链播放
- 每次执行时会对比115和本地文件，如果115不存在会删除对应的本地文件或目录，保持媒体库一致
- 复制元数据时，每个文件间隔1秒，防止风控
- 目录树文件在使用完后会自动删除（请不要中途中断执行）

## 一、准备工作
### 获取Cookie
需要通过各种方法获取cookie，然后写入./15-cookies.txt文件h或者写入config.json的115-cookies字段
可以直接使用alist的115存储中添加的cookie

### 修改配置文件: config.json：
- 115-cookies: 将115的cookie放入这里，会优先使用115-cookies.txt文件
- strm_root_dir: 115网盘挂载根目录对应的strm文件存放目录，例如：/vol2/1000/网盘/115，媒体服务器的媒体库就选择这个目录下的内容
- strm_ext: 要生成strm文件的扩展名，默认包含音乐类型，如果只有电影，就手动删除对应扩展名如.wav、 .flac、 .mp3等
- meta_ext: 元数据扩展名
- local
    - root_dir: 115网盘挂载的本地根目录，如果使用local模式，需要设置这个参数，例如：/CloudNAS/115
- alist
    - root_url: alist webdav的115根目录，例如：http://192.168.31.2:5244/dav/115
    - username: alist用户名，例如：strm
    - password: alist密码（不要包含:和@，尽量简单，可以专门添加一个只读权限的用户），例如：123123

获取cookie的方法请自行搜索

## 二、可执行文件运行：
1. 下载对应平台的压缩包，并解压
2. 打开终端切换到项目目录执行命令，比如解压到了D盘q115-strm目录：
```console
cd D:\q115-strm
main.exe -t=local -e=Media -c=0
```

## 三、源码使用方法：
### 安装项目依赖
```console
pip install -r requirements.txt
```
或者
```console
poetry install
```
### 执行脚本
```console
python3 main.py -t=local -e=Media -c=0
```

## 四、参数解释：
-t 使用本地挂载目录或者alist，可选值：local, alist; 默认: local
> - alist使用webdav生成strm内容，可以支持302直链播放，但是无法复制元数据
> - local使用本地挂载目录（可以是CD2也可以是其他软件，只要能有本地真实目录即可），支持复制元数据

-e 要生成目录树的目录，相对路径，不能为空，例如：
- 单层：media
- 多层：media/movie/合集

-c 是否复制元数据到strm目录：0-不复制，1-复制; 默认：0
> 元数据包括nfo，封面图片，字幕等，支持的扩展名在config.json的meta_ext修改

## 五、TODO
- [x] STRM生成
- [x] 元数据复制
- [x] 支持源文件不存在时删除目标文件
- [x] 支持alist webdav
- [ ] docker支持 + 简单的web ui (v0.2版本)
- [ ] docker版本增加监控文件变更，自动生成STRM (v0.2版本)
- [ ] docker版本接入CD2的webhook，自动生成STRM (v0.2版本)

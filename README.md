## 介绍
#### 基于[p115client](https://github.com/ChenyangGao/p115client)开发，通过生成115目录树来快速完成STRM文件创建，由于只有一次请求所以不会触发风控，需要配合CD2挂载目录使用
#### 不建议复制元数据，目前写死了1秒复制一个文件，加上网络传输，可能要好几秒才能处理一个文件，如果第一次扫盘有上万个文件可能要持续好几个小时。可以配合刮削器（如TMM）对生成的STRM文件再次刮削
#### 暂无配合ALIST使用的计划（因为我不用ALIST，也懒得测试）


## 一、准备工作
### 修改配置文件: config.json：
- cloud_mount_root_dir: CD2里115网盘的挂载路径根目录， 例如：/CloudNAS/115，这个路径主要用来生成STRM文件的内容，以供媒体服务器可以正确播放。
- strm_root_dir: 115网盘挂载根目录对应的strm文件存放目录，例如：/vol2/1000/网盘/115，媒体服务器的媒体库就选择这个目录下的内容
- strm_ext: 要生成strm文件的扩展名，默认包含音乐类型，如果只有电影，就手动删除对应扩展名如.wav、 .flac、 .mp3等
- meta_ext: 元数据扩展名
### 获取Cookie
需要通过各种方法获取cookie，然后写入./15-cookies.txt文件中

获取cookie的方法请自行搜索

## 二、可执行文件运行：
1. 下载对应平台的压缩包，并解压
2. 打开终端切换到项目目录执行命令，比如解压到了D盘q115-strm目录：
```console
cd D:\q115-strm
main.exe -e=Media -c=0
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
python3 main.py -e=Media -c=0
```

## 四、参数解释：
-e 要生成目录树的目录，相对路径，不能为空，例如：
- 单层：media
- 多层：media/movie/合集

-c 是否复制元数据到strm目录：0-不复制，1-复制，元数据包括nfo，封面图片，字幕等，支持的扩展名在config.json的meta_ext修改

## 五、TODO
- [x] STRM生成
- [x] 元数据复制
- [ ] docker支持 + 简单的web ui (v0.2版本)
- [ ] docker版本增加监控文件变更，自动生成STRM (v0.2版本)
- [ ] docker版本接入CD2的webhook，自动生成STRM (v0.2版本)

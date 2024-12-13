### 电报交流群：[https://t.me/q115_strm](https://t.me/q115_strm)

## 介绍
##### 基于[p115client](https://github.com/ChenyangGao/p115client)开发，通过生成115目录树来快速完成STRM文件创建，由于只有一次请求所以不会触发风控

## 特性
- 使用115目录树，只有一次请求，不会风控，后续操作都不会跟115交互
- 支持两种使用模式
    - 本地挂载目录：主要是CD2，会将媒体文件的真实路径写入STRM文件，支持复制元数据
    - webdav：主要是alist，会讲媒体文件的webdav地址写入STRM文件，不支持复制元数据，如果alist存储选择了302，则支持直链播放
- 每次执行时会对比115和本地文件，如果115不存在会删除对应的本地文件或目录，保持媒体库一致
- 复制元数据时，每个文件间隔1秒，防止风控
- 元数据创建软链接，可以快速完成元数据同步，但是媒体服务器显示海报墙时受所用挂载服务qps影响，也有触发风控的风险
- 目录树文件在使用完后会自动删除（请不要中途中断执行）

## 一、准备工作
### 修改配置文件: config.json：
- strm_root_dir: 115网盘挂载根目录对应的strm文件存放目录，例如：/vol2/1000/网盘/115，媒体服务器的媒体库就选择这个目录下的内容
- strm_ext: 要生成strm文件的扩展名，默认包含音乐类型，如果只有电影，就手动删除对应扩展名如.wav、 .flac、 .mp3等
- meta_ext: 元数据扩展名
- local
    - root_dir: 115网盘挂载的本地根目录，如果使用local模式，需要设置这个参数，例如：/CloudNAS/115
- alist
    - root_url: alist webdav的115根目录，例如：http://192.168.31.2:5244/dav/115
    - username: alist用户名，例如：strm
    - password: alist密码（不要包含:和@，尽量简单，可以专门添加一个只读权限的用户），例如：123123

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

-c 是否复制元数据到strm目录：0-不复制，1-复制，2-软链接; 默认：0
> 元数据包括nfo，封面图片，字幕等，支持的扩展名在config.json的meta_ext修改

## 五、TODO
- [x] STRM生成
- [x] 元数据复制
- [x] 支持源文件不存在时删除目标文件
- [x] 支持webdav和本地挂载如CD2
- [x] 支持扫码登录（解决其他三方获取cookie可能失败的问题）
- [x] 元数据增加软链接处理方式
- [x] docker支持 + 简单的web ui (v0.2版本)
- [x] docker版本增加监控文件变更，自动生成STRM，CD2 only (v0.2版本)
- [x] docker版本定时同步 (v0.2版本)
- [x] docker版本支持添加多个同步目录，每个同步目录都可以单独设置类型(local,webdav)，strm_ext, meta_ext，以及使用不同的115账号(v0.2版本）
- [ ] docker版本监控服务使用队列来进行精细化操作，减少对115目录树的生成请求（v0.3版本）
- [ ] 可执行文件采用交互式命令行来创建配置文件（v0.3版本）
- [ ] 增加STRM文件整理功能：将STRM软链或者复制到其他文件夹以便刮削，因为STRM根目录是对115网盘的映射无法修改文件名等（V0.4版本）

## 六、DOCKER
   ```bash
   docker run -d \
     --name q115strm \
     -v /vol1/1000/docker/q115strm/data:/app/data \
     -v /vol1/1000/docker/clouddrive2/shared/115:/vol1/1000/docker/clouddrive2/shared/115 \
     -v /vol1/1000/视频/网盘/115:/115 \
     -p 12123:12123 \
     --restart unless-stopped \
     qicfan/115strm:latest
   ```

或者compose

```
services:
  115strm:
    image: qicfan/115strm
    container_name: q115strm
    ports:
        - target: 12123
          published: 12123
          protocol: tcp
    volumes:
      - /vol1/1000/docker/q115strm/data:/app/data # 运行日志和数据
      - /vol1/1000/docker/clouddrive2/shared/115:/vol1/1000/docker/clouddrive2/shared/115 # CD2挂载115的的绝对路径，必须完整映射到容器中，如果使用WebDAV则不需要这个映射
      - /vol1/1000/视频/网盘/115:/115 # 存放STRM文件的根目录

    restart: unless-stopped
```

### Docker 配置解释
- `-v /vol1/1000/docker/q115strm/data:/app/data`: 该目录用来存放程序运行的日志和数据，建议映射，后续重装可以直接恢复数据
- `-v  /vol1/1000/docker/clouddrive2/shared/115:/vol1/1000/docker/clouddrive2/shared/115`: CD2挂载115的的绝对路径，必须完整映射到容器中，如果使用WebDAV则不需要这个映射。
- `-v /vol1/1000/视频/网盘/115:/115` 存放STRM文件的根目录，必须存在这个映射
- `-p 12123:12123`: 映射12123端口，一个简易的web ui。
- `--restart unless-stopped`: 设置容器在退出时自动重启。
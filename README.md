# 项目待回归，拟接入115开放平台接口，实现脱离cd2或者alist的播放

## 介绍
##### 基于[p115client](https://github.com/ChenyangGao/p115client)开发，通过生成115目录树来快速完成STRM文件创建，由于只有一次请求所以不会触发风控
##### 默认用户名密码都是admin

## 注意事项
1. 同一个账号同一时间只能有一个生成目录树的操作，请不要添加多个相同账号的cookie
1. 115网盘中的目录名不能包含媒体文件扩展名，否则会被识别为文件而不是目录
    > 比如战狼电影：Media/Movie/战狼.FLAC.MP4/战狼.FLAC.MP4，这个目录会被识别为两个MP4文件
    - Media/Movie/战狼.FLAC.MP4
    - Media/Movie/战狼.FLAC.MP4/战狼.FLAC.MP4
    > 这是由于115目录树不包含文件元数据，只能通过是否有媒体文件扩展名来确定到底是文件还是目录
1. 如果文件很多，建议添加多个同步目录，这样处理速度更快
1. 如果同一账号的多个目录都使用定时同步方式，那么执行时间需要错开，间隔5分钟为佳
    - 目录1每天0点0分执行：0 0 * * *
    - 目录2每天0点5分执行：5 0 * * *
    - 目录3每天0点10分执行：10 0 * * *
1. 监控变更依赖于CD2的会员功能，请确保使用CD2并且开通了会员
1. alist302方式要求emby/jellyfin + emby2alist配合，否则无法直接播放
1. 如果配置电报通知并且服务器在国内，需要配置代理，docke添加环境变量PROXY_HOST=http://ip:port
1. 如果需要编程触发任务执行，请调用：http://ip:port/api/job/{path}，path参数指添加同步目录时的同步路径字段的值

## TODO
- [x] STRM生成
- [x] 元数据复制
- [x] 支持源文件不存在时删除目标文件
- [x] 支持CD2本地挂载，STRM内存放媒体文件的本地路径
- [x] 支持WebDAV，STRM内存放WebDAV Url，可供播放器直接播放
- [x] 支持Alist 302，STRM内存放Alist链接(http://ip:port/d/115/xxxxx.mkv) ，配合emby2alist插件，客户端可播放115真实链接节省服务器流量(v0.3.2版本)
- [x] 元数据增加软链接处理方式
- [x] docker支持 + 简单的web ui (v0.2版本)
- [x] docker版本增加监控文件变更，自动生成STRM，CD2 only (v0.2版本)
- [x] docker版本定时同步 (v0.2版本)
- [x] docker版本支持添加多个同步目录，每个同步目录都可以单独设置类型(local,webdav)，strm_ext, meta_ext，以及使用不同的115账号(v0.2版本)
- [x] docker版本监控服务使用队列来进行精细化操作，减少对115目录树的生成请求(v0.3版本)
- [x] 可执行文件采用交互式命令行来创建配置文件(v0.3.1版本)
- [x] 支持其他网盘的STRM生成，但是需要本地挂载软件如CD或RClone支持(v0.3.4版本)
- [x] Web UI支持简易HTTP AUTH (v0.4版本)
- [x] 支持发送电报通知 (v0.4版本)


## 一、可执行文件运行：
1. 下载对应平台的压缩包，并解压
2. 打开终端切换到项目目录执行命令，比如解压到了D盘q115-strm目录：
```console
cd D:\q115-strm
// 查看同步目录列表
q115strm.exe list
// 添加115账号
q115strm.exe add115
// 添加同步目录
q115strm.exe create
// 执行全部同步任务
q115strm.exe run
// 执行单个同步任务
q115strm.exe run -k=xxx
```

## 二、DOCKER
   ```bash
   docker run -d \
     --name q115strm \
     -e "TZ=Asia/Shanghai" \
     -v /vol1/1000/docker/q115strm/data:/app/data \
     -v /vol1/1000/docker/clouddrive2/shared/115:/vol1/1000/docker/clouddrive2/shared/115:shared \
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
    environment:
      - TZ=Asia/Shanghai
    ports:
      - target: 12123
        published: 12123
        protocol: tcp
    volumes:
      - /vol1/1000/docker/q115strm/data:/app/data # 运行日志和数据
      - /vol1/1000/docker/clouddrive2/shared/115:/vol1/1000/docker/clouddrive2/shared/115:shared # CD2挂载115的的绝对路径，必须完整映射到容器中，如果使用WebDAV则不需要这个映射
      - /vol1/1000/视频/网盘/115:/115 # 存放STRM文件的根目录

    restart: unless-stopped
```

#### Docker 配置解释
- `-v /vol1/1000/docker/q115strm/data:/app/data`: 该目录用来存放程序运行的日志和数据，建议映射，后续重装可以直接恢复数据
- `-v  /vol1/1000/docker/clouddrive2/shared/115:/vol1/1000/docker/clouddrive2/shared/115:shared`: CD2挂载115的的绝对路径，必须完整映射到容器中，如果使用WebDAV则不需要这个映射。
- `-v /vol1/1000/视频/网盘/115:/115` 存放STRM文件的根目录，必须存在这个映射
- `-p 12123:12123`: 映射12123端口，一个简易的web ui。
- `--restart unless-stopped` 设置容器在退出时自动重启。
- `-e "TZ=Asia/Shanghai"` 时区变量，可以根据所在地设置；会影响记录的任务执行时间，定时执行任务的时间
- `-e "PROXY_HOST=http://192.168.1.1:10808"` 

## 关键词解释：
- 同步路径：115网盘中的目录，跟alist无关，请到115网盘app或者浏览器中查看实际的目录，多个目录用 / 分隔，比如：Media/电影/华语电影
- AList根文件夹：Alist -> 管理 -> 存储 -> 115网盘 -> 编辑 -> 拉倒最下面找到根文件夹ID
  - 如果是0，则该字段留空
  - 如果不为0则输入该ID对应的文件夹路径，多个目录用 / 分隔，如：Media/电影
- 115挂载路径：Alist -> 管理 -> 存储 -> 115网盘 -> 编辑 -> 挂载路径
    > 挂载路径是什么就填什么，去掉开头和结尾的/(不去也行，程序已经做了处理)
- 元数据选项：如果网盘中存放了字幕文件、封面、nfo文件等，可以通过选择的操作来讲元数据同步到strm跟路径的对应文件夹内

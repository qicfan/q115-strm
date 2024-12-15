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

## 三、DOCKER
   ```bash
   docker run -d \
     --name q115strm \
     -e TZ="Asia/Shanghai"
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
      - 'TZ=Asia/Shanghai'
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
- `-e TZ="Asia/Shanghai"` 时区变量，可以根据所在地设置；会影响记录的任务执行时间，定时执行任务的时间 

## 四、TODO
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
- [x] docker版本监控服务使用队列来进行精细化操作，减少对115目录树的生成请求（v0.3版本）
- [ ] 可执行文件采用交互式命令行来创建配置文件（v0.3.1版本）
- [ ] 增加STRM文件整理功能：将STRM软链或者复制到其他文件夹以便刮削，因为STRM根目录是对115网盘的映射无法修改文件名等（V0.4版本）
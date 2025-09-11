## 注意事项
- 项目改名为QMediaSync，仓库迁移到了：[qicfan/qmediasync](https://github.com/qicfan/qmediasync)，后续版本都将发布在新仓库
- 电报群：[http://t.me/q115_strm](https://t.me/q115_strm)
- QQ群：1057459156

## 介绍
- **默认用户名 admin,密码 admin123**
  
- 基于 115 开放平台接口来同步生成 STRM、元数据下载、元数据上传，并且提供直链解析服务，不依赖其他项目。
- 原理：定时同步 115 的文件树和本地文件树对比：
  1. 本地存在网盘不存在则删除本地文件或上传到网盘（由设置决定，测试版本不会删除任何文件）
  2. 本地不存在网盘存在则创建本地文件（STRM 或元数据下载）
  3. 本地存在且网盘存在，则判断文件是否一致（文件 pick_code 是否相同），一致则不处理，不一致则更新
- 实测 3W 多文件大概 22T 的库全量同步可能需要30分钟左右（不算元数据下载上传的时间），增量需要30秒到5分钟之内，根据115接口返回速度波动。
- 定时任务设定不能小于 0.5 小时间隔
- 上传下载队列都放在内存中，如果停止服务会丢失，没完成的任务下次同步时会继续。
- 115开放平台接口的调用有全局限速，一般不会触发流量限制，如果发生流量限制（115返回请求已达上限），会全局暂停30s来规避。每个接口的调用都有三次重试基本可以保证不会出现调用错误；如果在生成目录树时发生接口调用错误则会跳过本次同步（防止出现误删本地文件）
- 内存占用目前观察不会超过500MB，实际占用取决于资源库的大小因为目录树放到了内存中，如果有上百万个文件，内存占用可能会很高，建议多分几个同步目录，减轻单次同步压力
- 直链的解析会做缓存，方便2小时内的重复请求（pick_code+useragent为key）

## 已知问题
- ~~infuse+emby无法播放，原因：infuse调用emby进行播放时，emby请求的UserAgent为空，实际播放的UserAgent未知，这时115对下载链接的校验无法通过（播放和请求的UserAgent必须相同），解决方法暂时没有，待后续仔细抓包看一下。~~

### 功能列表

- [x] 115 开放平台接入
- [x] STRM 生成
- [x] 元数据下载
- [x] ~~使用 CookieCloud 同步 115 网页 Cookie（后续可以调用 115 api）~~
- [x] 接入 Telegram 通知
- [x] 目录下新建隐藏文件.meta 记录原始信息（供以后使用）
- [x] ~~元数据新增同名的隐藏文件.name.meta 记录原始信息（供以后使用）~~
- [x] 同步时上传网盘不存在的元数据（STRM 设置开启）
- [x] 同步时删除网盘不存在的 STRM 文件（STRM 设置开启）
- [x] 同步时删除网盘不存在且本地为空的文件夹（STRM 设置开启）
- [x] 首页增加上传下载队列状态
- [ ] ~~增加上传下载任务列表(暂时不做，只有第一全量同步时有需求，后续增量基本显示不出来就搞完了)~~
- [x] 增加监控多个目录
- [x] 增加同步记录删除(v0.6)
- [x] 增加单个同步目录手动同步(v0.6)
- [x] 如果同步目录正在同步队列中，则跳过本次执行(v0.6)
- [x] 本地增加115下载链接代理，解决局域网设备播放时因为UA不同导致失败的问题，提供开启开关（如果有外网播放需求就关闭） (v0.7)


## 快速开始

### 使用 Docker Run

```bash
# 创建数据目录
mkdir -p {root_dir}/q115-strm/config/logs/libs
mkdir -p {root_dir}/q115-strm/config/libs


# 运行容器
docker run -d \
  --name q115-strm \
  -p 12333:12333 \
  -v $(pwd)/q115-strm/config:/app/config \
  -v /vol1/1000/网盘:/media \
  -e TZ=Asia/Shanghai \
  --restart unless-stopped \
  qicfan/115strm:latest
```

### 使用 Docker Compose

1. 创建 `docker-compose.yml` 文件（见下方示例）

```
services:
    q115-strm:
        image: qicfan/115strm:latest
        container_name: q115-strm
        restart: unless-stopped
        ports:
            - "12333:12333"
        volumes:
            - /vol1/1000/docker/q115-strm/config:/app/config
            - /vol2/1000/网盘:/media
        environment:
            - TZ=Asia/Shanghai

networks:
    default:
        name: q115-strm
```

2. 运行以下命令：

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 目录映射说明

| 容器内路径    | 宿主机路径                           | 说明                     |
| ------------- | ------------------------------------ | ------------------------ |
| `/app/config` | `/vol1/1000/docker/q115-strm/config` | 配置文、数据、日志目录   |
| `/media`      | `/vol1/1000/网盘`                    | 存放 STRM 和元数据的目录 |

## 环境变量

| 变量名 | 默认值          | 说明     |
| ------ | --------------- | -------- |
| `TZ`   | `Asia/Shanghai` | 时区设置 |

## 端口说明

- **12333**: Web 服务端口

## 版本标签

- `latest` - 最新发布版本
- `v1.0.0` - 具体版本号（对应 GitHub Release）

## 首次使用

1. 启动容器后访问: http://your-ip:12333
2. 默认登录信息需要查看日志或配置文件
3. 登录后进行 115 账号配置

## 数据备份

重要数据位于 `/vol1/1000/docker/q115-strm/config` 目录，请定期备份：

```bash
# 备份数据
cp -r /vol1/1000/docker/q115-strm/config /vol1/1000/docker/q115-strm/config-backup-$(date +%Y%m%d)
```

## 故障排查

### 查看日志

```bash
# 查看容器日志
docker logs q115-strm

# 查看应用日志
docker exec q115-strm ls -la /app/config/logs/
```

### 重启服务

```bash
# 重启容器
docker restart q115-strm

# 或使用docker-compose
docker-compose restart
```

### 更新镜像

```bash
# 停止并删除旧容器
docker stop q115-strm && docker rm q115-strm

# 拉取最新镜像
docker pull qicfan/115strm:latest

# 重新启动
docker run -d \
  --name q115-strm \
  -p 12333:12333 \
  -v $(pwd)/q115-strm/config:/app/config \
  -v $(pwd)/q115-strm/data:/app/data \
  -v $(pwd)/q115-strm/logs:/app/config/logs \
  -e TZ=Asia/Shanghai \
  --restart unless-stopped \
  qicfan/115strm:latest
```


<p align="center">
  <img width="200" height="200" alt="支付宝打赏" src="https://github.com/user-attachments/assets/fc3519f2-f8d2-47b1-b7a4-5abf6d4e6e65" />
  <img width="200" height="200" alt="微信打赏" src="https://github.com/user-attachments/assets/0c9c9f6c-e52c-49a3-8ade-c2443d169685" />
</p>
<p align="center">**如果觉得好用，就请作者喝杯咖啡**</p>
































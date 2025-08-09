## 介绍

- 基于 115 开放平台接口来同步生成 STRM 和下载元数据，并且提供直链解析服务，不依赖其他项目。
- 原理：定时同步 115 的文件树根本地文件树对比：
- 1. 本地存在网盘不存在则删除本地文件
- 2. 本地不存在网盘存在则创建本地文件（STRM 或元数据下载）
- 3. 本地存在且网盘存在，则判断文件是否一致（文件 pick_code 是否相同），一致则不处理，不一致则更新
- 实测 3W 多文件大概 22T 的库需要 5 分钟左右完成目录树生成和对比，首次下载元数据需要的时间不定，可能在 1-2 个小时左右。
- 定时任务设定不能小于 1 小时间隔

- 默认用户名 admin,密码 admin123

### 功能列表

- [x] 115 开放平台接入
- [x] STRM 生成
- [x] 元数据下载
- [ ] 根据 STRM 文件秒传文件（将 STRM 里的内容发给其他人，其他人可以直接秒传给自己）
- [ ] 接入资源库
- [ ] emby 302（待定，优先级低）
- [ ] 影片整理（待定， 优先级最低）
- [ ] 分享转存（待定，115 开放平台无法实现，需要 115 api）

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

- 讨论电报群：[http://](https://t.me/q115_strm)

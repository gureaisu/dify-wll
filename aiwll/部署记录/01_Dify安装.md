# Dify 安装

安装日期：2026-09-27

## 环境
- Windows 10 Pro，内存 32GB，Docker 29.8.0，Docker Compose v5.5.1
- 本机内网 IP：192.168.50.204
- 安装前确认 port 80/443 没被占用

## 步骤
1. 下载 Dify 最新正式版 1.17.1 到 `C:\WorkDir\dify`：

       git clone --depth 1 --branch 1.17.1 https://github.com/langgenius/dify.git C:\WorkDir\dify

2. 创建环境变量文件：`docker\.env.example` → 复制成 `docker\.env`
3. 在 `.env` 里给 `SECRET_KEY` 填入随机值（留空也会自动产生）
4. 启动（在 `C:\WorkDir\dify\docker`）：

       docker compose up -d

   第一次会下载数 GB 的镜像；启动后共 16 个容器（api、worker、web、nginx、db_postgres、redis、weaviate、plugin_daemon、sandbox 等）
5. 等 API 就绪（约 30 秒，数据库迁移），浏览器打开 http://localhost/install 创建管理员账号（名称 admin）

## 设置摘要
- 对外 port：80（`EXPOSE_NGINX_PORT`）、443
- 向量数据库：weaviate（默认）
- 数据保存在 `C:\WorkDir\dify\docker\volumes\`，重启不会丢失

## 常用指令（在 `C:\WorkDir\dify\docker`）

    docker compose up -d          # 启动
    docker compose down           # 停止（保留数据）
    docker compose ps             # 查看状态
    docker logs -f docker-api-1   # 看 API 日志

Docker Desktop 没设开机自动启动的话，重开机后要先打开 Docker Desktop。

下一步：[[02_Dify应用设置]]

# 对外聊天网页

让任何人用 `http://<对外IP>:8080` 使用暖心家庭教育助手。
nginx 容器负责提供 `index.html`，并把两个 Dify Service API 路径代理过去。API Key 只存在服务器端，浏览器看不到。

```
浏览器 ──:8080──> aiwll-web（nginx）──> index.html
                     ├─ /api/chat-messages ─> Dify api:5001/v1/chat-messages
                     ├─ /api/parameters    ─> Dify api:5001/v1/parameters
                     └─ 其他路径一律 404（Dify 后台不对外）
```

开场白、推荐问题、回答内容都来自 Dify 的应用设置和知识库，网页本身不写死任何教育内容。

## 启动
先确认 Dify 已经在运行（`C:\WorkDir\dify\docker`）。

1. 拷贝 `.env.example` 成 `.env`，填入 API Key：Dify → 暖心家庭教育助手 → 访问 API → API 密钥。`.env` 不会进版本控制。
2. 启动：

       docker compose up -d

3. 本机测试：http://localhost:8080

修改 `index.html` 会立即生效（刷新页面即可）。修改 `nginx.conf.template` 或 `.env` 之后，要运行 `docker compose restart`。

## 让互联网上的人连进来
1. **Windows 防火墙**：用“系统管理员”身分开 PowerShell，运行：

       New-NetFirewallRule -DisplayName "AIWLL web 8080" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow

2. **路由器 port forwarding**：外部 TCP `8080` 转发到 `192.168.50.204:8080`。
   - **不要**转发 80 port，那是 Dify 后台。
   - 建议在路由器把这台电脑的 IP 设成固定（DHCP 保留）。
3. **分享网址**：`http://<对外IP>:8080`。
   - 可以在 https://api.ipify.org 查到目前的对外 IP。
   - 家用网络的对外 IP 可能会变动；需要固定网址时，可以用路由器的 DDNS 功能。
4. **测试**：用手机移动网络（关掉 Wi-Fi）开这个网址。

## 费用与防滥用
- **一定要在 OpenAI 设置每月预算上限**：https://platform.openai.com/settings/organization/limits
- nginx 限流：全站每分钟 20 则对话，超过会回 429，网页显示“使用人数较多，请稍后再试”。
  - Docker Desktop 会把所有访客的来源 IP 都变成同一个网关 IP，所以没办法做到“每个 IP”各自限流。详见 `nginx.conf.template` 的注解。
- 输入限制 500 字、请求大小上限 16KB；只开放两个 API 路径。
- 目前是 http，没有加密。长期公开使用时，建议改用 HTTPS（例如 Cloudflare Tunnel）。

## 常用指令
    docker compose logs -f      # 看连接纪录
    docker compose restart      # 修改设置后重启
    docker compose down         # 停止对外服务

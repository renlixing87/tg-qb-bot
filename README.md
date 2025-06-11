# qBittorrent Telegram Bot

一个通过 Telegram 机器人远程管理 qBittorrent 的 Docker 应用。支持发送磁力链接、种子文件，轻松管理你的下载任务。

## 功能特性

- 🤖 通过 Telegram 机器人与 qBittorrent 交互
- 🧲 支持磁力链接添加下载任务
- 📁 支持种子文件上传下载
- 🔐 用户授权验证，确保安全使用
- 🐳 Docker 容器化部署，简单易用
- 🔄 自动重启，保证服务稳定运行

## 快速开始

### 前置要求

- Docker 和 Docker Compose
- 运行中的 qBittorrent 实例（启用 Web UI）
- Telegram 机器人 Token

### 1. 创建 Telegram 机器人

1. 在 Telegram 中找到 [@BotFather](https://t.me/botfather)
2. 发送 `/newbot` 创建新机器人
3. 按提示设置机器人名称和用户名
4. 获取机器人 Token（格式类似：`1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 2. 获取用户 ID

1. 在 Telegram 中找到 [@userinfobot](https://t.me/userinfobot)
2. 发送任意消息获取你的用户 ID

### 3. 部署应用

1. 修改 `docker-compose.yml` 中的环境变量：
```yaml
services:
  qb-tg-bot:
    build: .
    container_name: qb-tg-bot
    image: savextube/qb-tg-bot:v0.1
    environment:
      # Telegram Bot 配置
      - TG_BOT_TOKEN=你的机器人Token           # 必需：从 @BotFather 获取
      - TG_AUTHORIZED_USERS=你的用户ID  # 可选：授权用户ID列表，用逗号分隔
      # qBittorrent 连接配置
      - QB_HOST=192.168.1.100        # qBittorrent 主机地址
      - QB_PORT=8080                 # qBittorrent Web UI 端口
      - QB_USERNAME=admin            # qBittorrent 用户名
      - QB_PASSWORD=你的密码          # qBittorrent 密码
    restart: unless-stopped
```

## 环境变量说明

| 变量名 | 必需 | 描述 | 示例 |
|--------|------|------|------|
| `TG_BOT_TOKEN` | ✅ | Telegram 机器人 Token | `1234567890:ABCdef...` |
| `TG_AUTHORIZED_USERS` | ❌ | 授权用户ID列表，用逗号分隔 | `123456789,987654321` |
| `QB_HOST` | ✅ | qBittorrent 主机地址 | `192.168.1.100` |
| `QB_PORT` | ✅ | qBittorrent Web UI 端口 | `8080` |
| `QB_USERNAME` | ✅ | qBittorrent 用户名 | `admin` |
| `QB_PASSWORD` | ✅ | qBittorrent 密码 | `your_password` |

## 使用方法

1. 在 Telegram 中找到你的机器人
2. 发送 `/start` 开始使用
3. 直接发送磁力链接或上传种子文件
4. 机器人会自动将下载任务添加到 qBittorrent

### 支持的消息类型

- **磁力链接**：直接发送以 `magnet:` 开头的链接
- **种子文件**：上传 `.torrent` 文件
- **命令**：
  - `/start` - 开始使用
  - `/help` - 查看帮助信息

## qBittorrent 配置

确保你的 qBittorrent 实例：

1. 启用了 Web UI
2. 设置了用户名和密码
3. 网络可达（如果使用 Docker，确保网络配置正确）

## 安全注意事项

- 🔒 建议使用 `TG_AUTHORIZED_USERS` 限制授权用户
- 🔐 不要在公共仓库中暴露真实的 Token 和密码
- 🌐 如果暴露到公网，请确保 qBittorrent 使用强密码

## 故障排除

### 常见问题

1. **机器人无响应**
   - 检查 `TG_BOT_TOKEN` 是否正确
   - 确认机器人已启动（`docker logs qb-tg-bot`）

2. **无法连接 qBittorrent**
   - 检查 `QB_HOST` 和 `QB_PORT` 配置
   - 确认 qBittorrent Web UI 可访问
   - 验证用户名密码是否正确

3. **权限拒绝**
   - 检查用户 ID 是否在 `TG_AUTHORIZED_USERS` 中
   - 确认用户 ID 获取正确

### 查看日志

```bash
docker logs qb-tg-bot
```

## 贡献

欢迎提交 Issues 和 Pull Requests！

## 许可证

MIT License

## 联系方式

如有问题或建议，请通过 Issues 联系。

---

⭐ 如果这个项目对你有帮助，请给个 Star！

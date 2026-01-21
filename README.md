# FRP Manager

FRP 内网穿透管理工具，支持服务端/客户端两用，YAML 配置，systemd 管理，自动下载。

## 快速开始

```bash
uv sync                       # 安装依赖
uv run frp-ctl client-up      # 启动客户端（自动下载二进制）
uv run frp-ctl ps             # 查看状态
```

## 命令

| 命令 | 说明 |
|------|------|
| `frp-ctl client-up` | 启动客户端 |
| `frp-ctl client-down` | 停止客户端 |
| `frp-ctl client-restart` | 重启客户端 |
| `frp-ctl client-remove` | 卸载客户端服务 |
| `frp-ctl server-up` | 启动服务端 |
| `frp-ctl server-down` | 停止服务端 |
| `frp-ctl server-restart` | 重启服务端 |
| `frp-ctl server-remove` | 卸载服务端服务 |
| `frp-ctl ps` | 查看所有状态 |
| `frp-ctl info` | 显示系统和配置信息 |
| `frp-ctl download` | 手动下载 frp 二进制 |
| `frp-ctl config -m client/server` | 显示生成的 TOML |

## 配置

编辑 `configs/` 下的 YAML 文件：

| 文件 | 说明 |
|------|------|
| `common.yaml` | 公共配置（服务器、认证、下载代理） |
| `client.yaml` | 客户端代理列表 |
| `server.yaml` | 服务端配置 |

### 下载代理配置

编辑 `configs/common.yaml`：

```yaml
download:
  version: "0.52.0"
  proxy: "http://127.0.0.1:1082"
```

### 添加代理服务

编辑 `configs/client.yaml`：

```yaml
proxies:
  - name: "my-service"
    type: "tcp"
    local_port: 8080
    remote_port: 8080
```

## systemd 服务

启动后自动创建 systemd 服务：
- ✅ 开机自启
- ✅ 崩溃自动重启
- ✅ `journalctl` 统一日志

```bash
sudo journalctl -u frp-client -f   # 客户端日志
sudo journalctl -u frp-server -f   # 服务端日志
```

## 目录结构

```
frpc/
├── configs/              # YAML 配置
├── src/frp_manager/      # Python 源码
├── bin/                  # frp 二进制（自动下载）
└── .runtime/             # 生成的 TOML 配置
```

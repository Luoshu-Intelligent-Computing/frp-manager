"""FRP Manager - 配置管理模块"""

from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).parent.parent.parent / "configs"


def load_yaml(path: Path) -> dict[str, Any]:
    """加载 YAML 配置文件"""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config(mode: str) -> dict[str, Any]:
    """加载配置，合并 common + server/client"""
    common = load_yaml(CONFIG_DIR / "common.yaml")
    specific = load_yaml(CONFIG_DIR / f"{mode}.yaml")
    return {**common, **specific}


def generate_client_toml(config: dict[str, Any]) -> str:
    """生成 frpc.toml 配置"""
    server = config.get("server", {})
    auth = config.get("auth", {})
    transport = config.get("transport", {})
    log = config.get("log", {})
    proxies = config.get("proxies", [])

    lines = [
        f'serverAddr = "{server.get("addr", "127.0.0.1")}"',
        f'serverPort = {server.get("port", 7000)}',
        "",
        f'auth.method = "{auth.get("method", "token")}"',
        f'auth.token = "{auth.get("token", "")}"',
        "",
        f'transport.tls.enable = {str(transport.get("tls_enable", True)).lower()}',
        f'transport.poolCount = {transport.get("pool_count", 5)}',
        "",
        f'log.level = "{log.get("level", "info")}"',
        f'log.maxDays = {log.get("max_days", 3)}',
        "",
    ]

    for proxy in proxies:
        lines.extend([
            "[[proxies]]",
            f'name = "{proxy["name"]}"',
            f'type = "{proxy.get("type", "tcp")}"',
            f'localIP = "{proxy.get("local_ip", "127.0.0.1")}"',
            f'localPort = {proxy["local_port"]}',
            f'remotePort = {proxy["remote_port"]}',
            "",
        ])

    return "\n".join(lines)


def generate_server_toml(config: dict[str, Any]) -> str:
    """生成 frps.toml 配置"""
    bind = config.get("bind", {})
    auth = config.get("auth", {})
    transport = config.get("transport", {})
    log = config.get("log", {})
    dashboard = config.get("dashboard", {})
    allow_ports = config.get("allow_ports", [])

    lines = [
        f'bindAddr = "{bind.get("addr", "0.0.0.0")}"',
        f'bindPort = {bind.get("port", 7000)}',
        "",
        f'auth.method = "{auth.get("method", "token")}"',
        f'auth.token = "{auth.get("token", "")}"',
        "",
        f'transport.tls.force = {str(transport.get("tls_enable", True)).lower()}',
        "",
        f'log.level = "{log.get("level", "info")}"',
        f'log.maxDays = {log.get("max_days", 3)}',
        "",
    ]

    if dashboard.get("enable"):
        lines.extend([
            f'webServer.addr = "{dashboard.get("addr", "0.0.0.0")}"',
            f'webServer.port = {dashboard.get("port", 7500)}',
            f'webServer.user = "{dashboard.get("user", "admin")}"',
            f'webServer.password = "{dashboard.get("password", "admin")}"',
            "",
        ])

    if allow_ports:
        port_ranges = ",".join(
            f'{p["start"]}-{p["end"]}' for p in allow_ports
        )
        lines.append(f'allowPorts = [{{ start = {allow_ports[0]["start"]}, end = {allow_ports[0]["end"]} }}]')

    return "\n".join(lines)


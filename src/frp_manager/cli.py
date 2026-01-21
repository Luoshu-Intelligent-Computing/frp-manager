"""FRP Manager - CLI 入口"""

import click

from .config import generate_client_toml, generate_server_toml, load_config
from .download import ensure_binary, download_frp, get_system_info
from .process import (
    get_service_name,
    is_running,
    start,
    status,
    stop,
    uninstall,
)


def _ensure_binary(config: dict) -> bool:
    """确保二进制文件存在"""
    dl = config.get("download", {})
    version = dl.get("version", "0.52.0")
    proxy = dl.get("proxy", "")
    mirror = dl.get("mirror", "")

    ok, msg = ensure_binary(version, proxy, mirror)
    if not ok:
        click.echo(f"❌ {msg}")
        return False
    return True


def _start(mode: str):
    """启动服务的通用逻辑"""
    config = load_config(mode)

    # 确保二进制存在
    if not _ensure_binary(config):
        return

    toml = generate_client_toml(config) if mode == "client" else generate_server_toml(config)

    ok, msg = start(mode, toml)
    icon = "✅" if ok else "⚠️"
    click.echo(f"{icon} {msg}")

    if ok:
        service = get_service_name(mode)
        click.echo(f"📋 日志: sudo journalctl -u {service} -f")


def _stop(mode: str):
    """停止服务的通用逻辑"""
    ok, msg = stop(mode)
    icon = "✅" if ok else "⚠️"
    click.echo(f"{icon} {msg}")


def _restart(mode: str):
    """重启服务的通用逻辑"""
    config = load_config(mode)
    toml = generate_client_toml(config) if mode == "client" else generate_server_toml(config)

    if is_running(mode):
        stop(mode)

    ok, msg = start(mode, toml)
    icon = "✅" if ok else "⚠️"
    click.echo(f"{icon} {msg}")


def _remove(mode: str):
    """卸载服务的通用逻辑"""
    ok, msg = uninstall(mode)
    icon = "✅" if ok else "⚠️"
    click.echo(f"{icon} {msg}")


@click.group()
def cli():
    """FRP 管理工具 - 支持服务端/客户端 (systemd)

    \b
    快捷命令:
      frp-ctl client-up      启动客户端
      frp-ctl server-up      启动服务端
    """
    pass


# ============ 客户端快捷命令 ============

@cli.command("client-up")
def client_up():
    """启动客户端"""
    _start("client")


@cli.command("client-down")
def client_down():
    """停止客户端"""
    _stop("client")


@cli.command("client-restart")
def client_restart():
    """重启客户端"""
    _restart("client")


@cli.command("client-remove")
def client_remove():
    """卸载客户端服务"""
    _remove("client")


# ============ 服务端快捷命令 ============

@cli.command("server-up")
def server_up():
    """启动服务端"""
    _start("server")


@cli.command("server-down")
def server_down():
    """停止服务端"""
    _stop("server")


@cli.command("server-restart")
def server_restart():
    """重启服务端"""
    _restart("server")


@cli.command("server-remove")
def server_remove():
    """卸载服务端服务"""
    _remove("server")


# ============ 通用命令 ============

@cli.command()
@click.option("-m", "--mode", type=click.Choice(["client", "server", "all"]), default="all", help="查看模式")
def ps(mode: str):
    """查看运行状态"""
    modes = ["client", "server"] if mode == "all" else [mode]

    for m in modes:
        s = status(m)
        service = s["service"]
        if s["running"]:
            click.echo(f"🟢 {service}: 运行中")
        elif s["installed"]:
            click.echo(f"🟡 {service}: 已安装但未运行")
        else:
            click.echo(f"⚫ {service}: 未安装")


@cli.command()
@click.option("-m", "--mode", type=click.Choice(["client", "server"]), default="client", help="运行模式")
def config(mode: str):
    """显示生成的 TOML 配置"""
    cfg = load_config(mode)
    toml = generate_client_toml(cfg) if mode == "client" else generate_server_toml(cfg)
    click.echo(toml)


@cli.command()
def download():
    """下载 frp 二进制文件"""
    config = load_config("client")
    dl = config.get("download", {})
    version = dl.get("version", "0.52.0")
    proxy = dl.get("proxy", "")
    mirror = dl.get("mirror", "")

    os_name, arch = get_system_info()
    click.echo(f"🖥️  系统: {os_name}/{arch}")

    ok, msg = download_frp(version, proxy, mirror)
    icon = "✅" if ok else "❌"
    click.echo(f"{icon} {msg}")


@cli.command()
def info():
    """显示系统和配置信息"""
    os_name, arch = get_system_info()
    config = load_config("client")
    dl = config.get("download", {})

    click.echo(f"🖥️  系统: {os_name}/{arch}")
    click.echo(f"📦 frp 版本: {dl.get('version', '0.52.0')}")
    click.echo(f"🌐 代理: {dl.get('proxy', '无')}")

    from .download import is_binary_exists
    if is_binary_exists():
        click.echo("✅ 二进制文件: 已安装")
    else:
        click.echo("❌ 二进制文件: 未安装")


def main():
    cli()


if __name__ == "__main__":
    main()


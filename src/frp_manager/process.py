"""FRP Manager - 进程管理模块 (systemd)"""

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
BIN_DIR = PROJECT_ROOT / "bin"
RUNTIME_DIR = PROJECT_ROOT / ".runtime"

SERVICE_TEMPLATE = """[Unit]
Description=FRP {mode_upper} - {description}
After=network.target

[Service]
Type=simple
ExecStart={binary} -c {config}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""


def get_service_name(mode: str) -> str:
    """获取 systemd 服务名"""
    return f"frp-{mode}"


def get_binary(mode: str) -> Path:
    """获取 frp 二进制文件路径"""
    name = "frpc" if mode == "client" else "frps"
    return BIN_DIR / name


def get_config_file(mode: str) -> Path:
    """获取生成的 TOML 配置路径"""
    RUNTIME_DIR.mkdir(exist_ok=True)
    return RUNTIME_DIR / f"frp{mode[0]}.toml"


def run_systemctl(cmd: str, service: str, sudo: bool = True) -> tuple[bool, str]:
    """执行 systemctl 命令"""
    args = ["sudo", "systemctl", cmd, service] if sudo else ["systemctl", cmd, service]
    try:
        result = subprocess.run(args, capture_output=True, text=True)
        return result.returncode == 0, result.stdout or result.stderr
    except Exception as e:
        return False, str(e)


def is_running(mode: str) -> bool:
    """检查服务是否运行中"""
    service = get_service_name(mode)
    ok, _ = run_systemctl("is-active", service, sudo=False)
    return ok


def is_installed(mode: str) -> bool:
    """检查服务是否已安装"""
    service_file = Path(f"/etc/systemd/system/{get_service_name(mode)}.service")
    return service_file.exists()


def install(mode: str, config_toml: str) -> tuple[bool, str]:
    """安装 systemd 服务"""
    service = get_service_name(mode)
    service_file = Path(f"/etc/systemd/system/{service}.service")

    binary = get_binary(mode)
    if not binary.exists():
        return False, f"二进制文件不存在: {binary}"

    # 写入配置文件
    config_file = get_config_file(mode)
    config_file.write_text(config_toml)

    # 生成 service 文件
    desc = "内网穿透客户端" if mode == "client" else "内网穿透服务端"
    service_content = SERVICE_TEMPLATE.format(
        mode_upper=mode.upper(),
        description=desc,
        binary=binary.absolute(),
        config=config_file.absolute(),
    )

    # 写入 service 文件（需要 sudo）
    try:
        subprocess.run(
            ["sudo", "tee", str(service_file)],
            input=service_content.encode(),
            capture_output=True,
            check=True,
        )
        run_systemctl("daemon-reload", "")
        return True, f"服务已安装: {service_file}"
    except subprocess.CalledProcessError as e:
        return False, f"安装失败: {e}"


def uninstall(mode: str) -> tuple[bool, str]:
    """卸载 systemd 服务"""
    service = get_service_name(mode)
    service_file = Path(f"/etc/systemd/system/{service}.service")

    if not service_file.exists():
        return False, f"服务未安装"

    # 先停止服务
    stop(mode)
    run_systemctl("disable", service)

    try:
        subprocess.run(["sudo", "rm", str(service_file)], check=True)
        run_systemctl("daemon-reload", "")
        return True, f"服务已卸载"
    except subprocess.CalledProcessError as e:
        return False, f"卸载失败: {e}"


def start(mode: str, config_toml: str) -> tuple[bool, str]:
    """启动服务"""
    service = get_service_name(mode)

    # 如果未安装，先安装
    if not is_installed(mode):
        ok, msg = install(mode, config_toml)
        if not ok:
            return False, msg
        run_systemctl("enable", service)
    else:
        # 更新配置
        get_config_file(mode).write_text(config_toml)

    if is_running(mode):
        return False, f"{service} 已在运行中"

    ok, msg = run_systemctl("start", service)
    return ok, f"{service} 已启动" if ok else f"启动失败: {msg}"


def stop(mode: str) -> tuple[bool, str]:
    """停止服务"""
    service = get_service_name(mode)

    if not is_running(mode):
        return False, f"{service} 未运行"

    ok, msg = run_systemctl("stop", service)
    return ok, f"{service} 已停止" if ok else f"停止失败: {msg}"


def status(mode: str) -> dict:
    """获取服务状态"""
    service = get_service_name(mode)
    running = is_running(mode)
    installed = is_installed(mode)

    return {
        "mode": mode,
        "service": service,
        "installed": installed,
        "running": running,
        "config": str(get_config_file(mode)) if installed else None,
    }


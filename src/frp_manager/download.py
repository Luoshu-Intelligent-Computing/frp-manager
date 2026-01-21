"""FRP Manager - 下载模块"""

import platform
import tarfile
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
BIN_DIR = PROJECT_ROOT / "bin"

GITHUB_URL = "https://github.com/fatedier/frp/releases/download/v{version}/frp_{version}_{os}_{arch}.tar.gz"

ARCH_MAP = {
    "x86_64": "amd64",
    "aarch64": "arm64",
    "armv7l": "arm",
    "armv6l": "arm",
}


def get_system_info() -> tuple[str, str]:
    """获取系统信息"""
    os_name = platform.system().lower()
    arch = platform.machine()
    return os_name, ARCH_MAP.get(arch, arch)


def get_download_url(version: str, mirror: str = "") -> str:
    """获取下载 URL"""
    os_name, arch = get_system_info()
    if mirror:
        return f"{mirror}/frp_{version}_{os_name}_{arch}.tar.gz"
    return GITHUB_URL.format(version=version, os=os_name, arch=arch)


def is_binary_exists() -> bool:
    """检查二进制文件是否存在"""
    frpc = BIN_DIR / "frpc"
    frps = BIN_DIR / "frps"
    return frpc.exists() and frps.exists()


def download_frp(version: str, proxy: str = "", mirror: str = "") -> tuple[bool, str]:
    """下载并解压 frp"""
    url = get_download_url(version, mirror)
    os_name, arch = get_system_info()
    
    print(f"📦 下载 frp v{version} ({os_name}/{arch})")
    print(f"   URL: {url}")
    
    BIN_DIR.mkdir(exist_ok=True)
    tar_path = BIN_DIR / "frp.tar.gz"
    
    try:
        # 设置代理
        if proxy:
            print(f"   代理: {proxy}")
            proxy_handler = urllib.request.ProxyHandler({
                "http": proxy,
                "https": proxy,
            })
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)
        
        # 下载
        urllib.request.urlretrieve(url, tar_path)
        
        # 解压
        print("📂 解压中...")
        with tarfile.open(tar_path, "r:gz") as tar:
            # 获取顶层目录名
            top_dir = tar.getnames()[0].split("/")[0]
            tar.extractall(BIN_DIR)
        
        # 移动文件到 bin 目录
        extract_dir = BIN_DIR / top_dir
        for item in ["frpc", "frps", "LICENSE"]:
            src = extract_dir / item
            dst = BIN_DIR / item
            if src.exists():
                if dst.exists():
                    dst.unlink()
                src.rename(dst)
        
        # 清理
        tar_path.unlink()
        import shutil
        shutil.rmtree(extract_dir, ignore_errors=True)
        
        # 设置执行权限
        (BIN_DIR / "frpc").chmod(0o755)
        (BIN_DIR / "frps").chmod(0o755)
        
        return True, f"frp v{version} 下载完成"
    
    except Exception as e:
        return False, f"下载失败: {e}"


def ensure_binary(version: str, proxy: str = "", mirror: str = "") -> tuple[bool, str]:
    """确保二进制文件存在，不存在则下载"""
    if is_binary_exists():
        return True, "二进制文件已存在"
    return download_frp(version, proxy, mirror)


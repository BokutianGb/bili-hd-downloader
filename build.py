# -*- coding: utf-8 -*-
"""一键打包脚本(在 Python 内调用 PyInstaller,避免控制台中文编码问题)"""
import subprocess
import sys
from pathlib import Path

APP_NAME = "B站最高画质下载器"
PYI_NAME = "BiliHDDownloader"  # PyInstaller 内部名用英文,避免控制台编码损坏中文
HERE = Path(__file__).parent


def main():
    py = sys.executable
    dist_exe = HERE / "dist" / (APP_NAME + ".exe")
    # 清掉旧产物(包括乱码文件)
    for f in (HERE / "dist").glob("*.exe"):
        if f.name != APP_NAME + ".exe":
            f.unlink(missing_ok=True)
    print("[1/2] PyInstaller 打包中(约1-3分钟)...")
    cmd = [
        py, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", PYI_NAME,
        str(HERE / "main.py"),
    ]
    proc = subprocess.run(cmd, cwd=str(HERE))
    if proc.returncode != 0:
        print("[错误] 打包失败")
        sys.exit(1)
    # 重命名为中文名(文件系统级 Unicode 重命名,可靠)
    src = HERE / "dist" / (PYI_NAME + ".exe")
    if src.exists():
        src.replace(dist_exe)
    print("[2/2] 打包完成:", dist_exe)
    print("      %.1f MB" % (dist_exe.stat().st_size / 1048576))
    print("      该 exe 不含 cookies.txt / yt-dlp / ffmpeg,首次运行自动准备")


if __name__ == "__main__":
    main()

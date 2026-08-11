# -*- coding: utf-8 -*-
"""制作发布 zip: 只包含 exe + 使用说明, 严格排除敏感/运行时文件(测试后删除)"""
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
EXE = HERE / "dist" / "B站最高画质下载器.exe"
GUIDE = HERE / "使用说明.txt"
OUT = HERE / "dist" / "BiliHDDownloader_v1.0.zip"

FORBIDDEN = {"cookies.txt", "edge_bilibili_cookies.txt", "tools", "downloads"}


def check_no_sensitive():
    """防御性检查: 发布包内容清单里绝不能出现敏感/运行时文件"""
    for name in FORBIDDEN:
        if (HERE / name).exists():
            raise SystemExit("发现敏感/运行时文件未清理: %s" % name)


def main():
    check_no_sensitive()
    if not EXE.exists():
        raise SystemExit("未找到 exe, 请先运行 build.py")
    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(EXE, EXE.name)
        z.write(GUIDE, GUIDE.name)
    print("发布包已生成:", OUT)
    print("内容:")
    with zipfile.ZipFile(OUT) as z:
        for info in z.infolist():
            print("  %s  (%.2f MB)" % (info.filename, info.file_size / 1048576))
    print("已确认不含: cookies.txt / tools / downloads 等敏感与运行时文件")


if __name__ == "__main__":
    main()

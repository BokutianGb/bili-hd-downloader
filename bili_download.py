# -*- coding: utf-8 -*-
"""B 站视频下载(最高画质)与下载后 ffprobe 验参

要点:
  - yt-dlp / ffmpeg 不进 exe,首次运行自动从 GitHub 下载到 tools/ 目录,保持可更新
  - 下载参数按画质档位选择,默认 bv*+ba/b(视频流+音频流,自动最高)
  - 下载完成后自动用 ffprobe -count_frames 逐帧数,输出真实帧率/帧数/编码
"""
import json
import os
import shutil
import subprocess
import time
import urllib.request
import zipfile
from pathlib import Path

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-win64-gpl.zip"

QUALITY_PRESETS = {
    "max": (
        "最高画质(大会员可4K/8K/杜比)",
        ["-f", "bv*+ba/b"],
    ),
    "h264": (
        "最高画质·优先H.264(播放器兼容性最好)",
        ["-f", "bv*+ba/b", "-S", "codec:h264"],
    ),
    "1080p": (
        "1080P·H.264(最兼容,无需大会员)",
        ["-f", "bv*[height<=1080]+ba/b", "-S", "codec:h264"],
    ),
}

VIDEO_SUFFIXES = (".mp4", ".mkv", ".webm", ".flv")


class Tools:
    """管理 tools/ 下的 yt-dlp.exe / ffmpeg.exe / ffprobe.exe,缺啥自动下载啥"""

    def __init__(self, base_dir, log=print):
        self.tools_dir = Path(base_dir) / "tools"
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        self.log = log
        self.ytdlp = self.tools_dir / "yt-dlp.exe"
        self.ffmpeg = self.tools_dir / "ffmpeg.exe"
        self.ffprobe = self.tools_dir / "ffprobe.exe"

    def ensure(self):
        """确保工具齐全,返回 True 表示全部就绪"""
        missing = []
        if not self.ytdlp.exists():
            missing.append("yt-dlp")
        if not self.ffmpeg.exists() or not self.ffprobe.exists():
            # 系统 PATH 里有 ffmpeg/ffprobe 就不用下载
            if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
                missing.append("ffmpeg")
        if not missing:
            return True
        for name in missing:
            if not self._download_tool(name):
                return False
        return True

    def _download_tool(self, name):
        if name == "yt-dlp":
            self.log("首次运行:自动下载 yt-dlp(视频解析引擎,约20MB)...")
            return self._download_with_progress(YTDLP_URL, self.ytdlp)
        if name == "ffmpeg":
            self.log("首次运行:自动下载 ffmpeg(音视频合并工具,约40MB)...")
            zip_path = self.tools_dir / "ffmpeg.zip"
            if not self._download_with_progress(FFMPEG_URL, zip_path):
                return False
            try:
                with zipfile.ZipFile(zip_path) as z:
                    for member in z.namelist():
                        if member.endswith("bin/ffmpeg.exe"):
                            self._extract_member(z, member, self.ffmpeg)
                        elif member.endswith("bin/ffprobe.exe"):
                            self._extract_member(z, member, self.ffprobe)
                zip_path.unlink(missing_ok=True)
                self.log("✓ ffmpeg 就绪")
                return True
            except Exception as e:
                self.log("解压 ffmpeg 失败:%s" % e)
                return False
        return False

    @staticmethod
    def _extract_member(zf, member, dest):
        with zf.open(member) as src, open(dest, "wb") as dst:
            shutil.copyfileobj(src, dst)

    def _download_with_progress(self, url, dest):
        tmp = str(dest) + ".part"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                total = int(resp.headers.get("Content-Length", 0) or 0)
                done = 0
                last_pct = -1
                with open(tmp, "wb") as f:
                    while True:
                        chunk = resp.read(1 << 20)
                        if not chunk:
                            break
                        f.write(chunk)
                        done += len(chunk)
                        if total:
                            pct = done * 100 // total
                            if pct != last_pct and pct % 10 == 0:
                                self.log("  下载中... %d%% (%dMB/%dMB)"
                                         % (pct, done // 1048576, total // 1048576))
                                last_pct = pct
            os.replace(tmp, dest)
            self.log("  ✓ %s 下载完成" % Path(dest).name)
            return True
        except Exception as e:
            self.log("下载失败:%s" % e)
            self.log("请手动下载后放入 tools 目录:")
            self.log("  yt-dlp : %s" % YTDLP_URL)
            self.log("  ffmpeg : %s" % FFMPEG_URL)
            return False


def build_command(url, out_dir, cookie_path, quality_key, tools):
    """组装 yt-dlp 命令行参数(返回 list)"""
    fmt_args = QUALITY_PRESETS[quality_key][1]
    cmd = [str(tools.ytdlp)]
    cmd += fmt_args
    cmd += [
        "--newline",
        "--windows-filenames",
        "--no-mtime",
        "--merge-output-format", "mp4",
        "-o", os.path.join(out_dir, "%(title)s.%(ext)s"),
    ]
    if cookie_path and Path(cookie_path).exists():
        cmd += ["--cookies", str(cookie_path)]
    if tools.ffmpeg.exists():
        cmd += ["--ffmpeg-location", str(tools.tools_dir)]
    cmd.append(url)
    return cmd


def download_video(url, out_dir, cookie_path, quality_key, tools, log=print):
    """执行下载,逐行转发 yt-dlp 输出到 log;返回 (退出码, 输出行列表)"""
    cmd = build_command(url, out_dir, cookie_path, quality_key, tools)
    log("运行: %s" % " ".join(cmd[:8] + ["..."]))
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=CREATE_NO_WINDOW,
    )
    lines = []
    for line in proc.stdout:
        line = line.rstrip()
        lines.append(line)
        log(line)
    proc.wait()
    return proc.returncode, lines


def find_newest_file(out_dir):
    """下载完成后找最新的视频文件,用于验参"""
    files = [
        p for p in Path(out_dir).iterdir()
        if p.is_file() and p.suffix.lower() in VIDEO_SUFFIXES
    ]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def probe_video(video_path, tools, log=print):
    """用 ffprobe -count_frames 逐帧数,输出真实参数(帧率/帧数/编码/时长)"""
    ffprobe = tools.ffprobe if tools.ffprobe.exists() else shutil.which("ffprobe")
    if not ffprobe:
        log("(未找到 ffprobe,跳过验参)")
        return None
    cmd = [
        str(ffprobe), "-v", "error", "-count_frames",
        "-show_entries",
        "stream=index,codec_type,codec_name,profile,width,height,pix_fmt,"
        "sample_rate,r_frame_rate,avg_frame_rate,nb_read_frames",
        "-show_entries", "format=duration,size",
        "-of", "json", str(video_path),
    ]
    try:
        out = subprocess.check_output(
            cmd, text=True, encoding="utf-8", errors="replace",
            creationflags=CREATE_NO_WINDOW,
        )
        data = json.loads(out)
        fmt = data.get("format", {})
        try:
            duration = float(fmt.get("duration", 0))
        except (TypeError, ValueError):
            duration = 0.0
        size = int(fmt.get("size", 0) or 0)
        log("时长: %.2f 秒 | 大小: %.1f MB" % (duration, size / 1048576))
        for s in data.get("streams", []):
            ctype = s.get("codec_type", "?")
            if ctype == "video":
                log("视频流: %s(%s) %sx%s %s"
                    % (s.get("codec_name", "?"), s.get("profile", ""),
                       s.get("width", "?"), s.get("height", "?"), s.get("pix_fmt", "?")))
                log("  帧率声明: %s | 实测平均: %s | 真实帧数: %s"
                    % (s.get("r_frame_rate", "?"), s.get("avg_frame_rate", "?"),
                       s.get("nb_read_frames", "?")))
            elif ctype == "audio":
                log("音频流: %s %sHz" % (s.get("codec_name", "?"), s.get("sample_rate", "?")))
        return data
    except Exception as e:
        log("验参失败:%s" % e)
        return None


def cookie_age_days(cookie_path):
    """cookie 文件距今多少天,用于提示是否过期(粗判断)"""
    if not Path(cookie_path).exists():
        return None
    age = time.time() - Path(cookie_path).stat().st_mtime
    return age / 86400

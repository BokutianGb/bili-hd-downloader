# -*- coding: utf-8 -*-
"""B站最高画质下载器 - GUI 入口

用法:
  双击运行 exe(或 python main.py)
  --selfcheck 参数用于自动测试 UI 构建,不进入主循环
"""
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

APP_NAME = "B站最高画质下载器"
APP_VERSION = "1.0"


def app_base_dir():
    """exe 模式下返回 exe 所在目录;源码模式下返回项目目录"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


BASE_DIR = app_base_dir()
COOKIE_PATH = BASE_DIR / "cookies.txt"
DEFAULT_OUT = BASE_DIR / "downloads"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("%s v%s" % (APP_NAME, APP_VERSION))
        self.geometry("860x660")
        self.minsize(760, 560)
        self.msg_queue = queue.Queue()
        self.busy = False
        self._build_ui()
        self.after(100, self._drain_queue)
        self.after(200, self._refresh_cookie_status)
        self.log("欢迎使用 %s v%s" % (APP_NAME, APP_VERSION))
        self.log("使用步骤: ①抓取Cookie → ②粘贴链接 → ③选画质 → ④选目录 → ⑤开始下载")
        self.log("首次运行会自动下载 yt-dlp/ffmpeg 工具(需联网,几十MB),请耐心等待")

    # ---------- 界面 ----------
    def _build_ui(self):
        frm = ttk.Frame(self, padding=10)
        frm.pack(fill="both", expand=True)
        pad = {"padx": 10, "pady": 5}

        row1 = ttk.Frame(frm)
        row1.pack(fill="x", **pad)
        self.cookie_status = tk.StringVar(value="正在检查 Cookie 状态...")
        self.cookie_status_label = ttk.Label(row1, textvariable=self.cookie_status)
        self.cookie_status_label.pack(side="left")
        ttk.Button(row1, text="① 抓取/更新登录Cookie(首次必做)",
                   command=self.on_grab_cookie).pack(side="right")

        row2 = ttk.Frame(frm)
        row2.pack(fill="x", **pad)
        ttk.Label(row2, text="② 视频链接:").pack(side="left")
        self.url_var = tk.StringVar()
        entry = ttk.Entry(row2, textvariable=self.url_var)
        entry.pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(row2, text="粘贴", command=self._paste_url).pack(side="right")

        row3 = ttk.Frame(frm)
        row3.pack(fill="x", **pad)
        ttk.Label(row3, text="③ 画质档位:").pack(side="left")
        self.quality_var = tk.StringVar(value="max")
        for key, (label, _args) in _presets():
            ttk.Radiobutton(row3, text=label, value=key,
                            variable=self.quality_var).pack(side="left", padx=6)

        row4 = ttk.Frame(frm)
        row4.pack(fill="x", **pad)
        ttk.Label(row4, text="④ 保存到:").pack(side="left")
        self.out_var = tk.StringVar(value=str(DEFAULT_OUT))
        ttk.Entry(row4, textvariable=self.out_var).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(row4, text="浏览", command=self._choose_dir).pack(side="left")

        self.dl_btn = ttk.Button(frm, text="⑤ 开始下载", command=self.on_download)
        self.dl_btn.pack(fill="x", **pad)

        ttk.Label(frm, text="运行日志(下载完成后自动验参):").pack(anchor="w", padx=10)
        log_frame = ttk.Frame(frm)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(2, 10))
        self.log_text = tk.Text(log_frame, height=14, state="disabled", wrap="word")
        sb = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

    def _paste_url(self):
        try:
            self.url_var.set(self.clipboard_get().strip())
        except tk.TclError:
            self.log("剪贴板为空或不可读")

    def _choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.out_var.get() or str(DEFAULT_OUT))
        if d:
            self.out_var.set(d)

    def _set_busy_ui(self, busy):
        self.busy = busy
        state = "disabled" if busy else "normal"
        for w in (self.dl_btn,):
            w.configure(state=state)
        self.log("---- 任务结束 ----" if not busy else "")

    # ---------- 日志(线程安全:子线程只入队,主线程渲染) ----------
    def log(self, text):
        self.msg_queue.put(text)

    def _drain_queue(self):
        try:
            while True:
                text = self.msg_queue.get_nowait()
                self.log_text.configure(state="normal")
                self.log_text.insert("end", text + "\n")
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(100, self._drain_queue)

    # ---------- Cookie ----------
    def _refresh_cookie_status(self):
        import bili_download
        if COOKIE_PATH.exists():
            mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(COOKIE_PATH.stat().st_mtime))
            age = bili_download.cookie_age_days(COOKIE_PATH)
            warn = " (已超过30天,建议重新抓取)" if (age or 0) > 30 else ""
            self.cookie_status.set("✓ Cookie 已就绪(生成于 %s%s)" % (mtime, warn))
            self.cookie_status_label.configure(foreground="#1a7f37")
        else:
            self.cookie_status.set("✗ 尚未获取 Cookie(不登录最高只能下 480P)")
            self.cookie_status_label.configure(foreground="#c62828")

    def on_grab_cookie(self):
        if self.busy:
            return
        self.busy = True
        self.log("---- 开始抓取 Cookie ----")
        threading.Thread(target=self._grab_worker, daemon=True).start()

    def _grab_worker(self):
        import bili_cookie
        try:
            def need_login():
                self.log("如未登录,请在弹出的 Edge 窗口里扫码/登录 B 站,登录后自动抓取...")
            ok, msg = bili_cookie.grab_bili_cookie(str(COOKIE_PATH), log=self.log,
                                                   need_login=need_login)
            self.log(msg)
            if ok and "SESSDATA" in msg:
                self.log("✓ 抓取成功,可以开始下载了(以后无需重复抓取,直到过期)")
        except Exception as e:
            self.log("抓取 Cookie 异常:%s" % e)
        finally:
            self.busy = False
            self.after(0, self._refresh_cookie_status)

    # ---------- 下载 ----------
    def on_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("提示", "请先粘贴 B 站视频链接(第②步)")
            return
        if not url.startswith(("http://", "https://")):
            messagebox.showwarning("提示", "链接格式不对\n请粘贴完整网址,如:\nhttps://www.bilibili.com/video/BVxxxxxxxx")
            return
        if self.busy:
            return
        self.busy = True
        self.log("---- 开始下载 ----")
        threading.Thread(target=self._download_worker, args=(url,), daemon=True).start()

    def _download_worker(self, url):
        import bili_download
        try:
            tools = bili_download.Tools(BASE_DIR, self.log)
            if not tools.ensure():
                self.log("工具准备失败,无法下载(见上方提示)")
                return
            quality = self.quality_var.get()
            out_dir = self.out_var.get().strip() or str(DEFAULT_OUT)
            Path(out_dir).mkdir(parents=True, exist_ok=True)
            self.log("画质档位: %s" % bili_download.QUALITY_PRESETS[quality][0])
            if not COOKIE_PATH.exists():
                self.log("! 警告: 未抓取 Cookie,下载质量会被限制在 480P 以下")
            rc, _lines = bili_download.download_video(url, out_dir, str(COOKIE_PATH),
                                                      quality, tools, self.log)
            if rc != 0:
                self.log("✗ 下载失败(退出码 %d)。常见原因: yt-dlp 版本过旧或 B 站接口变更" % rc)
                self.log("  解决: 删除 tools 目录后重新打开本程序,会自动下载最新 yt-dlp")
                return
            newest = bili_download.find_newest_file(out_dir)
            if newest:
                self.log("")
                self.log("=== 下载完成,验参如下 ===")
                bili_download.probe_video(newest, tools, self.log)
                self.after(0, lambda: messagebox.showinfo(
                    "下载完成", "文件已保存:\n%s\n\n%s\n大小 %.1f MB"
                    % (newest, newest.name, newest.stat().st_size / 1048576)))
            else:
                self.after(0, lambda: messagebox.showinfo("完成", "下载完成,但未找到输出文件"))
        except Exception as e:
            self.log("发生错误:%s" % e)
        finally:
            self.busy = False
            self.after(0, self._set_busy_ui, False)


def _presets():
    import bili_download
    return list(bili_download.QUALITY_PRESETS.items())


def run_selfcheck():
    """自动测试:构建 UI 后立即销毁,用于打包前验证"""
    app = App()
    app.update_idletasks()
    app.update()
    app.destroy()
    print("SELFCHECK OK")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        run_selfcheck()
        sys.exit(0)
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            from tkinter import messagebox
            messagebox.showerror(APP_NAME, "启动失败:\n%s" % e)
        except Exception:
            pass

# B站最高画质下载器 (BiliHDDownloader)

一个开箱即用的 Windows 图形化 B 站视频下载器。粘贴链接 → 点下载 → 自动以**当前账号能看到的最高画质**下载,下载完成后**自动验参**(真实帧率/帧数/编码/时长,逐帧数出来的,不是信元数据)。

## 为什么做这个

B 站网页上的"最高画质"不是打开就能下的:
- 1080P+ 需要**登录**(cookie)
- 4K/8K/杜比需要**大会员**
- 视频流和音频流是**分开的**,必须用 ffmpeg 合并
- 网页里的视频地址带**过期签名**,直接复制 URL 无效

本工具把这些全部自动化:自己抓 cookie、自己选流、自己合并、自己验证。

## 快速开始(3 步)

1. **下载**:去 [Releases](https://github.com/你的用户名/bili-hd-downloader/releases) 下载 `BiliHDDownloader_v1.0.zip`,解压到任意文件夹
2. **双击** `B站最高画质下载器.exe`
   - 首次运行会自动下载 yt-dlp 和 ffmpeg 工具(需要联网,共约 60MB,显示进度)
3. 按界面顺序操作:
   - **① 抓取/更新登录Cookie**(首次必做):会自动打开一个 Edge 窗口进入 B 站,扫码登录一次,自动抓取完成。之后约半年不用再抓
   - **② 粘贴视频链接**
   - **③ 选择画质档位**
   - **④ 选择保存位置**
   - **⑤ 开始下载**

下载完成后自动弹出验参结果,例如:

```
时长: 90.18 秒 | 大小: 150.2 MB
视频流: h264(High) 1920x1080 yuv420p
  帧率声明: 50/1 | 实测平均: 49.93 | 真实帧数: 4503
音频流: aac 48000Hz
```

## 画质档位说明

| 档位 | 能下到什么 | 适合谁 |
|---|---|---|
| 最高画质 | 大会员:4K/8K/杜比;登录:1080P+;未登录:480P | 追求画质,自带播放器能解 HEVC/AV1 |
| 最高·优先H.264 | 同分辨率下优先选 H.264 编码 | 文件要喂给剪辑/老播放器 |
| 1080P·H.264 | 锁 1080P 且用 H.264 | 最兼容,无需大会员 |

## 常见问题 (FAQ)

| 问题 | 解决 |
|---|---|
| 首次打开提示下载工具失败 | 网络连不上 GitHub,把提示里的两个链接手动下载后放进 `tools` 文件夹即可 |
| 下载报错/退出码非 0 | 删除 `tools` 文件夹,重新打开 exe(会自动下载最新 yt-dlp) |
| 明明登录了却下不到 1080P+ | 重新点 ① 抓取 Cookie(SESSDATA 过期了,约半年有效期) |
| 杀毒软件报毒 | PyInstaller 打包的 exe 常见误报,加入白名单即可;源码全公开可自行打包(见下) |
| 下载的文件打不开 | 换"优先H.264"档位重下 |

## 安全性说明

- **你的登录 Cookie 只存在你自己电脑上**(`exe 同目录/cookies.txt`),不会上传、不会进安装包、不会进 GitHub
- 本工具**只下载视频**,不上传任何东西
- 下载内容请遵守 B 站用户协议与相关法律法规,仅供个人学习研究

## 从源码自己打包

```bat
git clone https://github.com/你的用户名/bili-hd-downloader.git
cd bili-hd-downloader
build.bat        # 产物: dist\B站最高画质下载器.exe
```

或手动:

```bat
conda activate volleyball
pip install -r requirements.txt
pyinstaller --noconfirm --clean --onefile --windowed --name "B站最高画质下载器" main.py
```

## 技术原理(给好奇的人)

- **抓 Cookie**:以 `--remote-debugging-port=9222` 启动独立 Edge → CDP 协议 `Network.getAllCookies` 轮询 → 等到 `SESSDATA` 出现 → 写成 Netscape 格式供 yt-dlp 使用
- **选流**:yt-dlp `-f bv*+ba/b`,自动挑最高清晰度视频流 + 最佳音频流,ffmpeg 合并为 mp4
- **验参**:`ffprobe -count_frames` 逐帧数,输出**真实**帧数;对比 `r_frame_rate`(容器声明)与 `avg_frame_rate`(帧数÷时长)可判断视频是否为恒定帧率(CFR),两者不一致即为 VFR
- **工具自更新**:yt-dlp/ffmpeg 不冻结进 exe,首次运行自动下载到 `tools/`,B 站接口变更时删掉 `tools/` 重开即更新

## 免责声明

本项目仅供技术学习与个人研究。请勿用于商业用途,请勿下载传播受版权保护的内容。使用者需自行承担相关责任。

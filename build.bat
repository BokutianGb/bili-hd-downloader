@echo off
chcp 65001 >nul
rem ================================================
rem  B站最高画质下载器 - 一键打包脚本
rem  用法: 双击运行, 产物在 dist\B站最高画质下载器.exe
rem  前提: 已安装 Anaconda/Miniconda, 且存在 volleyball 环境
rem ================================================
echo [1/2] 激活环境...
call conda activate volleyball || goto :envfail

echo [2/2] 安装依赖 + 打包...
python -m pip install -r requirements.txt -q || goto :fail
python build.py || goto :fail

echo.
echo ================================================
echo  打包完成: dist\B站最高画质下载器.exe
echo  注意: 该 exe 不含你的 cookies.txt / yt-dlp / ffmpeg
echo        首次运行时会自动下载工具并现场抓取 Cookie
echo ================================================
pause
exit /b 0

:envfail
echo [错误] 未找到 conda, 请先安装 Anaconda/Miniconda
pause
exit /b 1

:fail
echo [错误] 打包失败, 请检查上方报错信息
pause
exit /b 1

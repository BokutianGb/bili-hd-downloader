# 上传到 GitHub(公开仓库)操作手册

> 本地工作已全部完成:git 仓库已初始化并提交,发布包已生成。
> 以下是"任何时候想上传"时照着做的步骤,全部可在 PowerShell 中执行。

## 上传前安全核对(必做,10 秒)

```powershell
cd D:\ending\bili_hd_downloader
git status --short
git ls-files | Select-String "cookie|tools|dist|downloads"
```

- 第一条应只显示源码文件(`.py` / `.md` / `.txt` / `.bat`)
- 第二条应为空 —— 有任何输出说明有敏感/运行时文件被误纳入,先修 .gitignore

## 第 1 步:登录 GitHub(只需一次,弹出浏览器授权)

```powershell
D:\bianchengruanjian\gh\bin\gh.exe auth login
```

- 选择 `GitHub.com` → `HTTPS` → 浏览器授权即可
- 如果想正式安装 gh CLI(以后不用全路径):`winget install GitHub.cli`(需管理员)

## 第 2 步:创建公开仓库并推送代码

```powershell
cd D:\ending\bili_hd_downloader
D:\bianchengruanjian\gh\bin\gh.exe repo create bili-hd-downloader --public --source . --push
```

## 第 3 步:上传发布包(让别人能直接下载 exe)

```powershell
D:\bianchengruanjian\gh\bin\gh.exe release create v1.0 "dist\BiliHDDownloader_v1.0.zip" `
  --title "v1.0 首个发布" `
  --notes "B站最高画质下载器 v1.0:双击exe → ①抓Cookie → ②粘贴链接 → ⑤下载,下载后自动验参。详见使用说明.txt"
```

也可以直接在 GitHub 网页打开仓库的 Releases 页面上传 zip。

## 第 4 步(可选):更新 README 里的仓库链接

README.md 中有一处占位链接:
`https://github.com/你的用户名/bili-hd-downloader`
上传后把它改成实际地址,再 `git add README.md; git commit -m "更新仓库链接"; git push`。

## 以后更新版本时的完整流程

```powershell
# 1. 修改代码后打包
cd D:\ending\bili_hd_downloader
python build.py                 # 重新生成 exe
python make_release.py          # 重新生成发布 zip

# 2. 提交代码
git add -A
git commit -m "更新说明"
git push

# 3. 发布新版本
D:\bianchengruanjian\gh\bin\gh.exe release create v1.1 "dist\BiliHDDownloader_v1.1.zip" --title "v1.1" --notes "更新内容"
```

## 常见问题

| 问题 | 解决 |
|---|---|
| `gh auth login` 没反应 | 检查浏览器是否弹出授权页;没有就重跑一次 |
| push 提示权限不足 | 重新登录:先 `gh auth logout`,再 `gh auth login` |
| 不小心把 cookies.txt 提交了 | 立即删除远程仓库里的文件并吊销 B 站登录(改密码/退出登录),再更新 .gitignore |

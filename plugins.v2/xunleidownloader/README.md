# 迅雷磁力下载插件

## 简介

迅雷磁力下载（XunleiDownloader）是 MoviePilot 的一个插件，支持通过 Web 面板配置参数，将磁力链接推送到迅雷 Docker 容器，实现远程离线下载。

- 支持通过 Web 面板一键推送磁力链接到迅雷 Docker
- 支持多条磁力链接批量推送
- 支持通过命令下载磁力链接

---

## 使用说明

1. 部署并启动 [cnk3x/xunlei Docker 项目](https://github.com/cnk3x/xunlei)。
2. 登录迅雷 Docker 后台，F12 抓包获取Authorization\file_id参数。
3. 在 MoviePilot 插件面板中填写上述参数，保存。
4. 通过以下方式下载磁力链接，保存到迅雷默认保存路径：
   - 在插件配置页面输入磁力链接
   - 使用`/xl`命令，如：`/xl magnet:?xt=urn:btih:xxxxx`

---

## 常见问题

1. **如何获取 Authorization\file_id？**
   - 登录迅雷 Docker 后台，按 F12 打开开发者工具，切换到 Network，迅雷网页右上角点击“新增任务”，抓取链接 "https://ip:port/webman/3rdparty/pan-xunlei-com/index.cgi/drive/v1/files?space=xxxxx"，查看请求即可获取。

## 抓包说明
1. 找到链接形如 https://ip:port/webman/3rdparty/pan-xunlei-com/index.cgi/drive/v1/files?space=xxxxx
![GitHub图标](https://raw.githubusercontent.com/liqman/MoviePilot-Plugins/refs/heads/main/images/F12_1.png)
2. 复制图中的参数的值到插件面板
![GitHub图标](https://raw.githubusercontent.com/liqman/MoviePilot-Plugins/refs/heads/main/images/F12_2.png)
![GitHub图标](https://raw.githubusercontent.com/liqman/MoviePilot-Plugins/refs/heads/main/images/F12_3.png)
---

## 致谢

- 本插件基于 [cnk3x/xunlei](https://github.com/cnk3x/xunlei) Docker 项目实现。
- 感谢 MoviePilot 社区的支持与贡献。

---

## License

MIT 

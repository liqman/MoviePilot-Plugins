# 迅雷磁力下载插件

## 简介

迅雷磁力下载（XunleiDownloader）是 MoviePilot 的一个插件，支持通过 Web 面板配置参数，将磁力链接推送到迅雷 Docker 容器，实现远程离线下载。

- 支持通过 Web 面板一键推送磁力链接到迅雷 Docker
- 支持多条磁力链接批量推送

---

## 使用说明

1. 部署并启动 [cnk3x/xunlei Docker 项目](https://github.com/cnk3x/xunlei)。
2. 登录迅雷 Docker 后台，F12 抓包获取 pan-auth、Authorization、Cookie 等参数。
3. 在 MoviePilot 插件面板中填写上述参数，保存。
4. 在"磁力链接"输入框粘贴磁力链接，保存即可自动推送到迅雷默认下载目录下载。

---

## 抓包说明
1. 找到链接形如 http://ip:port/webman/3rdparty/pan-xunlei-com/index.cgi/device/info/watch?space=xxx
![GitHub图标](https://raw.githubusercontent.com/liqman/MoviePilot-Plugins/refs/heads/main/images/F12_1.png)
2. 复制图中的三个参数的值到插件面板
![GitHub图标](https://raw.githubusercontent.com/liqman/MoviePilot-Plugins/refs/heads/main/images/F12_2.png)

## 常见问题

1. **如何获取 pan-auth、Authorization、Cookie？**
   - 登录迅雷 Docker 后台，按 F12 打开开发者工具，切换到 Network，找到任意请求，查看请求头即可获取。

---

## 致谢

- 本插件基于 [cnk3x/xunlei](https://github.com/cnk3x/xunlei) Docker 项目实现。
- 感谢 MoviePilot 社区的支持与贡献。

---

## License

MIT 

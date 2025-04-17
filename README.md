# 磁力链接下载插件

这是MoviePilot的磁力链接下载插件，可以通过磁力链接下载文件。

## 功能特点

- 支持qBittorrent和Transmission下载器
- 支持配置自定义保存路径
- 支持通过命令下载磁力链接

## 使用方法

1. 在插件管理页面启用此插件
2. 配置下载器和保存路径
3. 通过以下方式下载磁力链接：
   - 在插件配置页面输入磁力链接
   - 使用`/magnet`命令，如：`/magnet magnet:?xt=urn:btih:xxxxx`
   - 直接发送包含磁力链接的消息

## 配置说明

- **下载器**：选择使用的下载工具，支持qBittorrent和Transmission
- **暂停下载**：是否在添加下载后暂停任务
- **自定义保存路径**：手动指定下载保存路径（优先级高于MoviePilot保存路径）
- **磁力链接**：要下载的磁力链接，一行一个，格式：`magnet:?xt=urn:btih:xxx`

## Todo

- 支持自动识别消息中的磁力链接
- 支持解析磁力链接中的名称和哈希值

## 注意事项

- 磁力链接必须以`magnet:?xt=urn:btih:`开头
- 确保下载器已正确配置并可用

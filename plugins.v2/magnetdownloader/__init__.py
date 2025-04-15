from app.core.event import eventmanager, Event
from app.modules.qbittorrent import Qbittorrent
from app.modules.transmission import Transmission
from app.plugins import _PluginBase
from typing import Any, List, Dict, Tuple, Optional
from app.log import logger
from app.schemas.types import SystemConfigKey, EventType
from app.utils.string import StringUtils
from app.schemas import TransferInfo
from pathlib import Path


class MagnetDownloader(_PluginBase):
    # 插件名称
    plugin_name = "磁力链接下载"
    # 插件描述
    plugin_desc = "下载磁力链接(magnet)，支持qBittorrent和Transmission下载器。"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/liqman/MoviePilot-Plugins/refs/heads/main/icons/download.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "liqman"
    # 作者主页
    author_url = "https://github.com/liqman/MoviePilot-Plugins"
    # 插件配置项ID前缀
    plugin_config_prefix = "magnetdownloader_"
    # 加载顺序
    plugin_order = 29
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _downloader = None
    _is_paused = False
    _enabled = False
    _save_path = None
    _mp_path = None
    _category = None
    _tag = None
    _magnet_links = None
    qb = None
    tr = None

    def init_plugin(self, config: dict = None):
        """
        插件初始化
        """
        self.qb = Qbittorrent()
        self.tr = Transmission()

        if config:
            self._enabled = config.get("enabled")
            self._downloader = config.get("downloader")
            self._is_paused = config.get("is_paused")
            self._save_path = config.get("save_path")
            self._mp_path = config.get("mp_path")
            self._category = config.get("category")
            self._tag = config.get("tag")
            self._magnet_links = config.get("magnet_links")
            
            # 如果配置了磁力链接，尝试批量下载
            if self._magnet_links:
                self.batch_download_magnets(self._magnet_links)

            self.update_config({
                "downloader": self._downloader,
                "enabled": self._enabled,
                "save_path": self._save_path,
                "mp_path": self._mp_path,
                "category": self._category,
                "tag": self._tag,
                "is_paused": self._is_paused,
                "magnet_links": ""  # 清空已处理的链接
            })

    def batch_download_magnets(self, magnet_links_text: str):
        """
        批量下载磁力链接
        """
        if not magnet_links_text:
            return
            
        # 按行分割多个链接
        magnet_links = magnet_links_text.strip().split('\n')
        success_count = 0
        failed_count = 0
        
        for magnet_link in magnet_links:
            if not magnet_link.strip():
                continue
                
            # 下载单个磁力链接
            _, result = self.download_magnet(magnet_link.strip())
            if "失败" not in result:
                success_count += 1
            else:
                failed_count += 1
                
        # 记录日志
        if success_count > 0:
            logger.info(f"批量添加磁力链接任务完成，成功：{success_count}，失败：{failed_count}")

    def download_magnet(self, magnet_url: str) -> Tuple[str, str]:
        """
        下载磁力链接
        """
        # 验证磁力链接格式
        if not StringUtils.is_magnet_url(magnet_url):
            logger.error(f"无效的磁力链接格式：{magnet_url}")
            return None, "无效的磁力链接格式"

        download_path = self._save_path or self._mp_path
        
        # 添加下载任务
        if str(self._downloader) == "qb":
            # qBittorrent下载
            torrent = self.qb.add_torrent(
                content=magnet_url,
                download_dir=download_path,
                category=self._category,
                tags=[self._tag] if self._tag else None,
                is_paused=self._is_paused
            )
        else:
            # Transmission下载
            torrent = self.tr.add_torrent(
                content=magnet_url,
                download_dir=download_path,
                is_paused=self._is_paused,
                labels=[self._tag] if self._tag else None
            )

        if torrent:
            logger.info(f"磁力链接添加下载成功：{magnet_url} 保存位置：{download_path}")
            return "磁力链接", f"添加下载成功，保存位置：{download_path}"
        else:
            logger.error(f"磁力链接添加下载失败：{magnet_url}")
            return "磁力链接", "添加下载失败"

    @eventmanager.register(EventType.PluginAction)
    def download_magnet_action(self, event: Event = None):
        """
        响应插件动作事件
        """
        if not event:
            return
            
        event_data = event.event_data
        if not event_data or event_data.get("action") != "download_magnet":
            return
            
        args = event_data.get("args")
        if not args:
            logger.error(f"缺少参数：{event_data}")
            return

        # 执行磁力链接下载
        _, result = self.download_magnet(args)
        if "失败" in result:
            self.post_message(channel=event.event_data.get("channel"),
                              title="添加磁力链接下载失败",
                              userid=event.event_data.get("user"))
        else:
            self.post_message(channel=event.event_data.get("channel"),
                              title=f"磁力链接 {result}",
                              userid=event.event_data.get("user"))

    def get_state(self) -> bool:
        """
        获取插件状态
        """
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """
        注册命令
        """
        return [
            {
                "cmd": "/magnet",
                "event": EventType.PluginAction,
                "desc": "磁力链接下载",
                "category": "",
                "data": {
                    "action": "download_magnet"
                }
            }
        ]

    def get_api(self) -> List[Dict[str, Any]]:
        """
        注册API
        """
        pass

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面
        """
        dir_conf: List[dict] = self.systemconfig.get(SystemConfigKey.DownloadDirectories)
        dir_conf = [{'title': d.get('name'), 'value': d.get('path')} for d in dir_conf]
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enabled',
                                            'label': '启用插件',
                                        }
                                    }
                                ]
                            },
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 3
                                },
                                'content': [
                                    {
                                        'component': 'VSelect',
                                        'props': {
                                            'model': 'downloader',
                                            'label': '下载器',
                                            'items': [
                                                {'title': 'qBittorrent', 'value': 'qb'},
                                                {'title': 'Transmission', 'value': 'tr'}
                                            ]
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 3
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'is_paused',
                                            'label': '暂停下载',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSelect',
                                        'props': {
                                            'model': 'save_path',
                                            'label': '保存目录',
                                            'items': dir_conf
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'category',
                                            'label': '分类',
                                            'placeholder': '可选，用于qBittorrent'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'tag',
                                            'label': '标签',
                                            'placeholder': '可选，用于下载器分类'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'magnet_links',
                                            'label': '批量添加磁力链接',
                                            'placeholder': '每行一个磁力链接，格式：magnet:?xt=urn:btih:...',
                                            'rows': 5,
                                            'hint': '输入多个磁力链接，每行一个，保存配置后会自动添加到下载器',
                                            'persistent-hint': True
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                },
                                'content': [
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'info',
                                            'variant': 'tonal',
                                            'text': '磁力链接格式必须以magnet:?xt=urn:开头。自定义保存路径优先级高于MoviePilot保存路径。'
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            "downloader": "qb",
            "is_paused": False,
            "save_path": None,
            "mp_path": None,
            "category": None,
            "tag": None,
            "magnet_links": ""
        }

    def get_page(self) -> List[dict]:
        """
        拼装插件详情页面
        """
        return []

    def stop_service(self):
        """
        停止服务
        """
        pass 

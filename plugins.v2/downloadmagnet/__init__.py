from typing import Any, List, Dict, Tuple, Optional
import logging

from app.core.event import eventmanager, Event
from app.plugins import _PluginBase
from app.schemas.types import EventType
from app.log import logger
from app.modules.qbittorrent import Qbittorrent
from app.modules.transmission import Transmission
from app.utils.string import StringUtils
from app.schemas import TransferInfo
from app.core.context import Context
from app.core.config import settings
from app.schemas.types import SystemConfigKey

from magnetdownloadplugin.magnet_helper import MagnetHelper

class MagnetDownloadPlugin(_PluginBase):
    # 插件名称
    plugin_name = "磁力链接下载"
    # 插件描述
    plugin_desc = "通过磁力链接下载文件"
    # 插件图标
    plugin_icon = "magnet.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "ChatGPT"
    # 作者主页
    author_url = "https://chat.openai.com"
    # 插件配置项ID前缀
    plugin_config_prefix = "magnetdownloadplugin_"
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
    _magnet_links = None
    qb = None
    tr = None

    def init_plugin(self, config: dict = None):
        """
        初始化插件
        """
        self.qb = Qbittorrent()
        self.tr = Transmission()

        if config:
            self._enabled = config.get("enabled")
            self._downloader = config.get("downloader")
            self._is_paused = config.get("is_paused")
            self._save_path = config.get("save_path")
            self._mp_path = config.get("mp_path")
            self._magnet_links = config.get("magnet_links")

            # 下载磁力链接
            if self._magnet_links:
                for magnet_link in str(self._magnet_links).split("\n"):
                    if magnet_link.strip():
                        self.__download_magnet(magnet_link.strip())

            self.update_config({
                "downloader": self._downloader,
                "enabled": self._enabled,
                "save_path": self._save_path,
                "mp_path": self._mp_path,
                "is_paused": self._is_paused
            })

    def __download_magnet(self, magnet_link: str):
        """
        下载磁力链接
        :param magnet_link: 磁力链接
        :return: 下载结果信息
        """
        # 验证磁力链接格式
        if not MagnetHelper.is_magnet_link(magnet_link):
            logger.error(f"无效的磁力链接格式：{magnet_link}")
            return None

        # 获取磁力链接信息
        magnet_info = MagnetHelper.get_magnet_info(magnet_link)
        magnet_hash = magnet_info.get("hash", "")
        magnet_name = magnet_info.get("name", "")

        # 添加下载任务
        if str(self._downloader) == "qb":
            torrent = self.qb.add_torrent(
                content=magnet_link,
                is_paused=self._is_paused,
                download_dir=self._save_path or self._mp_path
            )
        else:
            torrent = self.tr.add_torrent(
                content=magnet_link,
                is_paused=self._is_paused,
                download_dir=self._save_path or self._mp_path
            )

        if torrent:
            name_info = f"[{magnet_name}]" if magnet_name else ""
            logger.info(f"磁力链接{name_info}添加下载成功: {magnet_link} 保存位置: {self._save_path or self._mp_path}")
            return f"磁力链接{name_info}添加下载成功, 保存位置: {self._save_path or self._mp_path}"
        else:
            logger.error(f"磁力链接添加下载失败: {magnet_link} 保存位置: {self._save_path or self._mp_path}")
            return f"磁力链接添加下载失败, 保存位置: {self._save_path or self._mp_path}"

    @eventmanager.register(EventType.PluginAction)
    def handle_magnet_download(self, event: Event = None):
        """
        处理磁力链接下载事件
        """
        if event:
            event_data = event.event_data
            if not event_data or event_data.get("action") != "download_magnet":
                return
            args = event_data.get("args")
            if not args:
                logger.error(f"缺少参数：{event_data}")
                return

            result = self.__download_magnet(args)
            if not result:
                self.post_message(channel=event.event_data.get("channel"),
                                  title="添加磁力链接下载失败",
                                  userid=event.event_data.get("user"))
            else:
                self.post_message(channel=event.event_data.get("channel"),
                                  title=result,
                                  userid=event.event_data.get("user"))

    @eventmanager.register(EventType.PluginMessage)
    def on_plugin_message(self, event: Event = None):
        """
        处理插件消息
        """
        if not event:
            return
        
        event_data = event.event_data
        if not event_data:
            return
            
        # 检查消息文本是否包含磁力链接
        message = event_data.get("text", "")
        if not message or not self._enabled:
            return
            
        # 检查是否是磁力链接
        if MagnetHelper.is_magnet_link(message):
            # 添加下载
            result = self.__download_magnet(message)
            if result:
                self.post_message(channel=event.event_data.get("channel"),
                                 title=result,
                                 userid=event.event_data.get("user"))

    def get_state(self) -> bool:
        """
        获取插件状态
        """
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """
        注册插件命令
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
        注册插件API
        """
        pass

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        插件配置页面
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
                                        'component': 'VSelect',
                                        'props': {
                                            'model': 'is_paused',
                                            'label': '暂停下载',
                                            'items': [
                                                {'title': '开启', 'value': True},
                                                {'title': '不开启', 'value': False}
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
                                        'component': 'VSelect',
                                        'props': {
                                            'model': 'mp_path',
                                            'label': 'MoviePilot保存路径',
                                            'items': dir_conf
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
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'save_path',
                                            'label': '自定义保存路径'
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
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'magnet_links',
                                            'rows': '3',
                                            'label': '磁力链接',
                                            'placeholder': '磁力链接，一行一个，格式：magnet:?xt=urn:btih:...'
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
                                            'text': '自定义保存路径优先级高于MoviePilot保存路径。'
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
                                            'text': '保存路径为下载器保存路径，磁力链接一行一个，格式：magnet:?xt=urn:btih:...'
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "downloader": "qb",
            "is_paused": False,
            "enabled": False,
            "save_path": "",
            "mp_path": "",
            "magnet_links": ""
        }

    def get_page(self) -> List[dict]:
        """
        插件详情页面
        """
        pass

    def stop_service(self):
        """
        退出插件
        """
        pass 

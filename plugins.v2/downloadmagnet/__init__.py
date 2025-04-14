from typing import Any, List, Dict, Tuple, Optional

from app.modules.qbittorrent.qbittorrent import Qbittorrent
from app.core.event import eventmanager, Event
from app.db.site_oper import SiteOper
from app.plugins import _PluginBase
from app.log import logger
from app.schemas.types import EventType
from app.utils.string import StringUtils
from app.schemas import ServiceInfo
from app.helper.downloader import DownloaderHelper
from app.helper.directory import DirectoryHelper


class DownloadMagnet(_PluginBase):
    # 插件名称
    plugin_name = "添加磁力链接下载"
    # 插件描述
    plugin_desc = "选择下载器，添加磁力任务。"
    # 插件图标
    plugin_icon = "download.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "liqman"
    # 作者主页
    author_url = "https://github.com/liqman/MoviePilot-Plugins"
    # 插件配置项ID前缀
    plugin_config_prefix = "downloadmagnet_"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _is_paused = False
    _enabled = False
    _save_path = None
    _mp_path = None
    _downloader = None
    torrent_helper = None
    downloader_helper = None
    directory_helper = None

    def init_plugin(self, config: dict = None):
        self.downloader_helper = DownloaderHelper()
        self.directory_helper = DirectoryHelper()

        if config:
            self._enabled = config.get("enabled")
            self._is_paused = config.get("is_paused")
            self._save_path = config.get("save_path")
            self._mp_path = config.get("mp_path")
            self._torrent_urls = config.get("torrent_urls")
            self._downloader = config.get("downloader")

            # 下载种子
            if self._torrent_urls:
                for magnet_link in str(self._torrent_urls).split("\n"):
                    logger.info(f"读取下载链接成功 {magnet_link}")
                    self.__download_magnet(magnet_link)

            self.update_config({
                "downloader": self._downloader,
                "save_path": self._save_path,
                "enabled": self._enabled,
                "mp_path": self._mp_path,
                "is_paused": self._is_paused
            })

    def __download_magnet(self, magnet_link: str):
        """
        下载磁力链接
        """
        try:
            Qbittorrent.add_torrent(content=magnet_link,
                                             download_dir=self._save_path,
                                             is_paused=self._is_paused)
        except Exception as e
            log.info(e)

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        return [
            {
                "cmd": "/dm",
                "event": EventType.PluginAction,
                "desc": "磁力下载",
                "category": "",
                "data": {
                    "action": "download_magnet"
                }
            }
        ]

    def get_api(self) -> List[Dict[str, Any]]:
        pass

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
        """
        dir_conf = [{'title': d.name, 'value': d.download_path} for d in
                    self.directory_helper.get_local_download_dirs()]
        downloader_options = [{"title": config.name, "value": config.name} for config in
                              self.downloader_helper.get_configs().values()]
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
                                            'items': downloader_options
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
                                            'label': '暂停种子',
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
                                            'model': 'torrent_urls',
                                            'rows': '3',
                                            'label': '种子链接',
                                            'placeholder': '种子链接，一行一个'
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
                                            'text': '保存路径为下载器保存路径，种子链接一行一个。'
                                                    '添加的种子链接需站点已在站点管理维护或公共站点。'
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
            "torrent_urls": ""
        }

    def get_page(self) -> List[dict]:
        pass

    def stop_service(self):
        """
        退出插件
        """
        pass

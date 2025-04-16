from app.core.event import eventmanager, Event
from app.modules.qbittorrent import Qbittorrent
from app.modules.transmission import Transmission
from app.plugins import _PluginBase
from typing import Any, List, Dict, Tuple
from app.log import logger
from app.schemas.types import EventType
from app.utils.string import StringUtils

class MagnetDownloader(_PluginBase):
    plugin_name = "磁力链接下载"
    plugin_desc = "通过磁力链接添加下载任务，支持qbittorrent和transmission。"
    plugin_icon = "magnet.png"
    plugin_version = "1.0"
    plugin_author = "liqman"
    author_url = "https://github.com/liqman/MoviePilot-Plugins/"
    plugin_config_prefix = "magnetdownloader_"
    plugin_order = 30
    auth_level = 1

    _downloader = None
    _is_paused = False
    _enabled = False
    _save_path = None
    _magnet_url = None
    qb = None
    tr = None

    def init_plugin(self, config: dict = None):
        self.qb = Qbittorrent()
        self.tr = Transmission()
        if config:
            self._enabled = config.get("enabled")
            self._downloader = config.get("downloader")
            self._is_paused = config.get("is_paused")
            self._save_path = config.get("save_path")
            self._magnet_url = config.get("magnet_url")
            # 自动下载
            if self._magnet_url:
                for magnet_url in str(self._magnet_url).split("\n"):
                    self.__download_magnet(magnet_url)
            self.update_config({
                "downloader": self._downloader,
                "enabled": self._enabled,
                "save_path": self._save_path,
                "is_paused": self._is_paused
            })

    def __download_magnet(self, magnet_url: str):
        """
        下载磁力链接
        """
        if not StringUtils.is_magnet_url(magnet_url):
            logger.error(f"无效的磁力链接：{magnet_url}")
            return False, "无效的磁力链接"
        if str(self._downloader) == "qb":
            result = self.qb.add_torrent(content=magnet_url,
                                         is_paused=self._is_paused,
                                         download_dir=self._save_path)
        else:
            result = self.tr.add_torrent(content=magnet_url,
                                         is_paused=self._is_paused,
                                         download_dir=self._save_path)
        if result:
            logger.info(f"磁力链接添加下载成功 {magnet_url} 保存位置 {self._save_path}")
            return True, f"磁力链接添加下载成功, 保存位置 {self._save_path}"
        else:
            logger.error(f"磁力链接添加下载失败 {magnet_url} 保存位置 {self._save_path}")
            return False, f"磁力链接添加下载失败, 保存位置 {self._save_path}"

    @eventmanager.register(EventType.PluginAction)
    def remote_sync_one(self, event: Event = None):
        if event:
            event_data = event.event_data
            if not event_data or event_data.get("action") != "magnet_download":
                return
            args = event_data.get("args")
            if not args:
                logger.error(f"缺少参数：{event_data}")
                return
            success, result = self.__download_magnet(args)
            if not success:
                self.post_message(channel=event.event_data.get("channel"),
                                  title="磁力链接下载失败",
                                  userid=event.event_data.get("user"))
            else:
                self.post_message(channel=event.event_data.get("channel"),
                                  title=f"{result}",
                                  userid=event.event_data.get("user"))

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        return [
            {
                "cmd": "/magnet",
                "event": EventType.PluginAction,
                "desc": "磁力链接下载",
                "category": "",
                "data": {
                    "action": "magnet_download"
                }
            }
        ]

    def get_api(self) -> List[Dict[str, Any]]:
        # 可扩展API，如有需要
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        dir_conf: List[dict] = self.systemconfig.get("DownloadDirectories")
        dir_conf = [{'title': d.get('name'), 'value': d.get('path')} for d in dir_conf] if dir_conf else []
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
                                                {'title': 'qb', 'value': 'qb'},
                                                {'title': 'tr', 'value': 'tr'}
                                            ]
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
                                            'label': '保存路径',
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
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'is_paused',
                                            'label': '添加后暂停',
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
                                            'model': 'magnet_url',
                                            'label': '磁力链接（支持多行，每行一个）',
                                            'placeholder': 'magnet:?xt=urn:btih:...'
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
            "save_path": "",
            "is_paused": False,
            "magnet_url": ""
        }

    def get_page(self) -> List[dict]:
        # 可扩展详情页
        return []

    def stop_service(self):
        # 可扩展停止逻辑
        pass 

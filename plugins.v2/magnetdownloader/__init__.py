from app.core.event import eventmanager, Event
from app.modules.qbittorrent import Qbittorrent
from app.modules.transmission import Transmission
from app.plugins import _PluginBase
from typing import Any, List, Dict, Tuple
from app.log import logger
from app.schemas.types import EventType
from app.utils.string import StringUtils
from urllib.parse import urlparse, quote
import requests
import time

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
    _downloader_url = None
    _downloader_username = None
    _downloader_password = None
    _upload_limit = None
    _use_default_tracker = True
    _tracker_list = ""
    _category = None
    qb = None
    tr = None

    def init_plugin(self, config: dict = None):
        # 参考 model.py，实例化下载器时不传参数
        self.qb = Qbittorrent()
        self.tr = Transmission()
        if config:
            self._enabled = config.get("enabled")
            self._downloader = config.get("downloader")
            self._is_paused = config.get("is_paused")
            self._save_path = config.get("save_path")
            self._magnet_url = config.get("magnet_url")
            self._downloader_url = config.get("downloader_url")
            self._downloader_username = config.get("downloader_username")
            self._downloader_password = config.get("downloader_password")
            self._upload_limit = config.get("upload_limit")
            self._use_default_tracker = config.get("use_default_tracker", True)
            self._tracker_list = config.get("tracker_list", "")
            self._category = config.get("category")
            # 自动下载
            if self._magnet_url:
                for magnet_url in str(self._magnet_url).split("\n"):
                    self.__download_magnet(magnet_url)
            self.update_config({
                "downloader": self._downloader,
                "enabled": self._enabled,
                "save_path": self._save_path,
                "is_paused": self._is_paused,
                "downloader_url": self._downloader_url,
                "downloader_username": self._downloader_username,
                "downloader_password": self._downloader_password,
                "upload_limit": self._upload_limit,
                "use_default_tracker": self._use_default_tracker,
                "tracker_list": self._tracker_list,
                "category": self._category
            })

    @staticmethod
    def is_magnet_url(url: str) -> bool:
        return isinstance(url, str) and url.strip().startswith("magnet:?")

    @staticmethod
    def parse_host_port(url):
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port
        if not port:
            port = 80 if parsed.scheme == 'http' else 443
        return host, port

    @staticmethod
    def append_trackers_to_magnet(magnet_url, tracker_list):
        for tracker in tracker_list:
            magnet_url += "&tr=" + quote(tracker, safe='')
        return magnet_url

    def __download_magnet(self, magnet_url: str):
        """
        下载磁力链接
        """
        if not self.is_magnet_url(magnet_url):
            logger.error(f"无效的磁力链接：{magnet_url}")
            return False, "无效的磁力链接"
        # 处理tracker
        custom_tracker_list = [line.strip() for line in getattr(self, '_tracker_list', '').splitlines() if line.strip()]
        recommend_tracker_list = []
        if getattr(self, '_use_default_tracker', True):
            try:
                resp = requests.get("https://raw.githubusercontent.com/ngosang/trackerslist/refs/heads/master/trackers_best.txt", timeout=10)
                # logger.info(f'请求推荐tracker状态: {resp.status_code}, ok: {resp.ok}')
                if resp.ok:
                    recommend_tracker_list = [line.strip() for line in resp.text.splitlines() if line.strip()]
                    logger.info(f'获取到推荐tracker数量: {len(recommend_tracker_list)}')
                else:
                    logger.error(f'获取推荐tracker失败，状态码: {resp.status_code}')
            except Exception as e:
                logger.error(f"获取默认tracker失败: {e}")
        # 合并，自定义在前，推荐在后，去重
        all_trackers = custom_tracker_list + recommend_tracker_list
        tracker_list = []
        for t in all_trackers:
            if t not in tracker_list:
                tracker_list.append(t)
        #logger.info(f'最终拼接到磁力链接的tracker: {tracker_list}')
        # 拼接tracker到磁力链接
        if tracker_list:
            magnet_url = self.append_trackers_to_magnet(magnet_url, tracker_list)
        # 处理上传限速（KB/s -> B/s）
        upload_limit = self._upload_limit
        if upload_limit:
            try:
                upload_limit = int(float(upload_limit) * 1024)
            except Exception:
                upload_limit = None
        try:
            if str(self._downloader) == "qb":
                # logger.info(f'Qbittorrent配置: url={repr(self._downloader_url)}, username={repr(self._downloader_username)}, password={repr(self._downloader_password)}')
                host, port = self.parse_host_port(self._downloader_url)
                qb = Qbittorrent(host=host, port=port, username=self._downloader_username, password=self._downloader_password)
                result = qb.add_torrent(content=magnet_url,
                                        is_paused=self._is_paused,
                                        download_dir=self._save_path,
                                        upload_limit=upload_limit,
                                        category=self._category)
            else:
                host, port = self.parse_host_port(self._downloader_url)
                tr = Transmission(host=host, port=port, username=self._downloader_username, password=self._downloader_password)
                labels = [self._category] if self._category else None
                result = tr.add_torrent(content=magnet_url,
                                        is_paused=self._is_paused,
                                        download_dir=self._save_path,
                                        labels=labels)
            logger.info(f'add_torrent result: {result}')
        except Exception as e:
            logger.error(f'add_torrent exception: {e}')
            return False, f'添加下载异常: {e}'
        if result:
            logger.info(f"磁力链接添加下载成功, 保存位置 {self._save_path}")
            return True, f"磁力链接添加下载成功, 保存位置 {self._save_path}"
        else:
            logger.error(f"磁力链接添加下载失败, 保存位置 {self._save_path}")
            return False, f"磁力链接添加下载失败, 保存位置 {self._save_path}"

    @eventmanager.register(EventType.PluginAction)
    def remote_sync_one(self, event: Event = None):
        if event:
            event_data = event.event_data
            if not event_data or event_data.get("action") != "magnet_download":
                return
            args = event_data.get("args")
            if not args:
                # 兼容命令行 arg_str
                args = event_data.get("arg_str")
            if not args:
                logger.error(f"缺少参数：{event_data}")
                return
            success, result = self.__download_magnet(args)
            if not success:
                self.post_message(channel=event.event_data.get("channel"),
                                  title="磁力链接下载失败, 请确认磁力链接有效性！",
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
                "cmd": "/dm",
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
                    # 启用插件开关单独一行，放最上面
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 4},
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
                    # 第一行：下载器、下载器URL、下载器用户名、下载器密码
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 3},
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
                                'props': {'cols': 12, 'md': 3},
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'downloader_url',
                                            'label': '下载器URL',
                                            'placeholder': 'http://127.0.0.1:8080/ 或 http://127.0.0.1:9091/transmission/rpc'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 3},
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'downloader_username',
                                            'label': '下载器用户名',
                                            'placeholder': 'admin'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 3},
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'downloader_password',
                                            'label': '下载器密码',
                                            'type': 'password',
                                            'placeholder': 'password'
                                        }
                                    }
                                ]
                            },
                        ]
                    },
                    # 第二行：保存路径、种子分类、种子上传限速、添加后暂停
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 3},
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'save_path',
                                            'label': '保存路径',
                                            'placeholder': '/downloads/path'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 3},
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'category',
                                            'label': '种子分类',
                                            'placeholder': '如：movie, tv, anime'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 3},
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'upload_limit',
                                            'label': '种子上传限速(KB/s)',
                                            'type': 'number',
                                            'placeholder': '0为不限速'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 3},
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
                    # 磁力链接输入框
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12},
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
                    },
                    # tracker list 相关
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 2},
                                'content': [
                                    {
                                        'component': 'VCheckbox',
                                        'props': {
                                            'model': 'use_default_tracker',
                                            'label': '使用推荐Tracker列表',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 10},
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'tracker_list',
                                            'label': '自定义Tracker列表（每行一个）',
                                            'placeholder': 'http://tracker.example/announce',
                                            'v-if': '!use_default_tracker'
                                        }
                                    }
                                ]
                            },
                        ]
                    },
                ]
            }
        ], {
            "enabled": False,
            "downloader": "qb",
            "save_path": "",
            "is_paused": False,
            "magnet_url": "",
            "category": "",
            "downloader_url": "",
            "downloader_username": "",
            "downloader_password": "",
            "upload_limit": "",
            "use_default_tracker": True,
            "tracker_list": ""
        }

    def get_page(self) -> List[dict]:
        # 可扩展详情页
        return []

    def stop_service(self):
        # 可扩展停止逻辑
        pass 

from app.plugins import _PluginBase
from typing import Any, List, Dict, Tuple, Optional
import requests
import urllib.parse
import json

class XunleiDownloader(_PluginBase):
    plugin_name = "迅雷磁力下载"
    plugin_desc = "通过迅雷添加磁力任务。"
    plugin_icon = "https://raw.githubusercontent.com/liqman/MoviePilot-Plugins/refs/heads/main/icons/xunlei.png"
    plugin_version = "1.0"
    plugin_author = "liqman"
    author_url = "https://github.com/liqman"
    plugin_config_prefix = "xunleidownloader_"
    plugin_order = 31
    auth_level = 1

    _enabled = False
    _BASE_URL = ''
    _PAN_AUTH = ''
    _Authorization = ''
    _COOKIE_STR = ''
    _magnet_url = ''

    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled", False)
            self._BASE_URL = config.get("BASE_URL", "")
            self._PAN_AUTH = config.get("PAN_AUTH", "")
            self._Authorization = config.get("Authorization", "")
            self._COOKIE_STR = config.get("COOKIE_STR", "")
            self._magnet_url = config.get("magnet_url", "")
            # 自动下载
            if self._magnet_url:
                for magnet_url in str(self._magnet_url).split("\n"):
                    self.download_magnet(magnet_url)
                self._magnet_url = ''  # 清空磁力链接
            self.update_config({
                "enabled": self._enabled,
                "BASE_URL": self._BASE_URL,
                "PAN_AUTH": self._PAN_AUTH,
                "Authorization": self._Authorization,
                "COOKIE_STR": self._COOKIE_STR,
                "magnet_url": self._magnet_url
            })

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        return [
            {
                "cmd": "/xunlei",
                "event": None,
                "desc": "迅雷磁力下载",
                "category": "",
                "data": {
                    "action": "xunlei_download"
                }
            }
        ]

    def get_api(self) -> List[Dict[str, Any]]:
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        form_content = [
            # 启用插件开关
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
            # 迅雷Docker地址和Authorization同一行
            {
                'component': 'VRow',
                'content': [
                    {
                        'component': 'VCol',
                        'props': {'cols': 12, 'md': 6},
                        'content': [
                            {
                                'component': 'VTextField',
                                'props': {
                                    'model': 'BASE_URL',
                                    'label': '迅雷Docker地址',
                                    'placeholder': '如：http://192.168.1.200:4321, 最后不要加/'
                                }
                            }
                        ]
                    },
                    {
                        'component': 'VCol',
                        'props': {'cols': 12, 'md': 6},
                        'content': [
                            {
                                'component': 'VTextField',
                                'props': {
                                    'model': 'Authorization',
                                    'label': 'Authorization值',
                                    'placeholder': 'Basic ...'
                                }
                            }
                        ]
                    },
                ]
            },
            # pan-auth单独一行
            {
                'component': 'VRow',
                'content': [
                    {
                        'component': 'VCol',
                        'props': {'cols': 12},
                        'content': [
                            {
                                'component': 'VTextField',
                                'props': {
                                    'model': 'PAN_AUTH',
                                    'label': 'pan-auth值',
                                    'placeholder': 'pan-auth令牌'
                                }
                            }
                        ]
                    }
                ]
            },
            # Cookie字符串单独一行
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
                                    'model': 'COOKIE_STR',
                                    'label': 'Cookie字符串',
                                    'placeholder': 'my_vms=...; PHPSID=...; ...'
                                }
                            }
                        ]
                    }
                ]
            },
            # 磁力链接单独一行
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
            # 插入VAlert（去除下载路径相关提示）
            {
                'component': 'VRow',
                'content': [
                    {
                        'component': 'VCol',
                        'props': {'cols': 12},
                        'content': [
                            {
                                "component": "VAlert",
                                "props": {
                                    "type": "info",
                                    "variant": "tonal",
                                    "text": "登录迅雷Docker后台F12抓取下列所需参数, 方法详见 https://github.com/liqman/MoviePilot-Plugins/blob/main/plugins.v2/xunleidownloader/README.md"
                                },
                            },{
                                "component": "VAlert",
                                "props": {
                                    "type": "info",
                                    "variant": "tonal",
                                    "text": "迅雷Docker地址 : 格式为 http://192.168.1.200:4321 , 不要保留最后的/"
                                },
                            },{
                                "component": "VAlert",
                                "props": {
                                    "type": "info",
                                    "variant": "tonal",
                                    "text": "可使用 /xunlei 进行命令交互, 如 /xunlei 磁力链接"
                                },
                            }
                        ]
                    }
                ]
            },
        ]
        form_data = {
            'enabled': self._enabled,
            'BASE_URL': self._BASE_URL,
            'PAN_AUTH': self._PAN_AUTH,
            'Authorization': self._Authorization,
            'COOKIE_STR': self._COOKIE_STR,
            'magnet_url': self._magnet_url
        }
        return form_content, form_data

    def get_page(self) -> List[dict]:
        pass
    
    def stop_service(self):
        pass

    def _get_headers(self):
        return {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Authorization': self._Authorization,
            'Connection': 'keep-alive',
            'Origin': self._BASE_URL,
            'Referer': f'{self._BASE_URL}/webman/3rdparty/pan-xunlei-com/index.cgi/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0',
            'content-type': 'application/json',
            'device-space': '',
            'pan-auth': self._PAN_AUTH,
        }

    def _get_cookies(self):
        return dict(item.split('=') for item in self._COOKIE_STR.split('; ') if '=' in item)

    def get_device_info(self):
        base_url = f'{self._BASE_URL}/webman/3rdparty/pan-xunlei-com/index.cgi/device/info/watch'
        params = {
            'space': '',
            'pan_auth': self._PAN_AUTH,
            'device_space': ''
        }
        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        response = requests.post(
            url,
            headers=self._get_headers(),
            cookies=self._get_cookies(),
            json={},
            verify=False
        )
        return response

    def get_folders(self, space=''):
        base_url = f'{self._BASE_URL}/webman/3rdparty/pan-xunlei-com/index.cgi/drive/v1/files'
        params = {
            'space': space,
            'limit': '200',
            'parent_id': '',
            'filters': '{"kind":{"eq":"drive#folder"}}',
            'page_token': '',
            'with': ['withCategoryDiskMountPath', 'withCategoryDownloadPath'],
            'pan_auth': self._PAN_AUTH,
            'device_space': ''
        }
        url = f"{base_url}?{urllib.parse.urlencode(params, doseq=True)}"
        response = requests.get(
            url,
            headers=self._get_headers(),
            cookies=self._get_cookies(),
            verify=False
        )
        return response

    def xunlei_request(self, magnet_url):
        url = f'{self._BASE_URL}/webman/3rdparty/pan-xunlei-com/index.cgi/drive/v1/resource/list'
        params = {
            'pan_auth': self._PAN_AUTH,
            'device_space': ''
        }
        data = {
            "page_size": 1000,
            "urls": magnet_url
        }
        response = requests.post(
            url,
            params=params,
            headers=self._get_headers(),
            cookies=self._get_cookies(),
            json=data,
            verify=False
        )
        return response

    def create_xunlei_task(self, target, magnet_url, downloads_id, file_name, file_size, total_file_count):
        url = f'{self._BASE_URL}/webman/3rdparty/pan-xunlei-com/index.cgi/drive/v1/task'
        params = {
            'pan_auth': self._PAN_AUTH,
            'device_space': ''
        }
        data = {
            "type": "user#download-url",
            "name": file_name,
            "file_name": file_name,
            "file_size": file_size,
            "space": target,
            "params": {
                "target": target,
                "url": magnet_url,
                "total_file_count": total_file_count,
                "parent_folder_id": downloads_id,
                "sub_file_index": "0,3",
                "mime_type": "",
                "file_id": ""
            }
        }
        response = requests.post(
            url,
            params=params,
            headers=self._get_headers(),
            cookies=self._get_cookies(),
            json=data,
            verify=False
        )
        return response

    def download_magnet(self, magnet_url: str):
        # 1. 获取设备信息
        device_info_response = self.get_device_info()
        if not device_info_response.ok:
            return False, f"获取设备信息失败: {device_info_response.text}"
        device_info = device_info_response.json()
        target = device_info.get('target', '')
        if not target:
            return False, "未获取到target值"
        # 2. 获取文件夹列表
        folders_response = self.get_folders(space=target)
        if not folders_response.ok:
            return False, f"获取文件夹失败: {folders_response.text}"
        folders_data = folders_response.json()
        downloads_id = None
        for folder in folders_data.get('files', []):
            if folder.get('params', {}).get('category_name') == "默认下载目录":
                downloads_id = folder.get('id')
                break
        if not downloads_id:
            return False, "未找到downloads文件夹，无法创建下载任务"
        # 3. 获取资源列表
        resource_response = self.xunlei_request(magnet_url)
        if not resource_response.ok:
            return False, f"获取资源失败: {resource_response.text}"
        resource_data = resource_response.json()
        if not resource_data.get('list', {}).get('resources'):
            return False, "未找到资源信息"
        first_resource = resource_data['list']['resources'][0]
        file_name = first_resource.get('name')
        file_size = str(first_resource.get('file_size'))
        total_file_count = str(first_resource.get('file_count'))
        # 4. 创建下载任务
        task_response = self.create_xunlei_task(target, magnet_url, downloads_id, file_name, file_size, total_file_count)
        if not task_response.ok:
            return False, f"创建下载任务失败: {task_response.text}"
        return True, f"下载任务创建成功: {file_name}"

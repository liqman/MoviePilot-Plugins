from app.plugins import _PluginBase
from typing import Any, List, Dict, Tuple, Optional
import requests
import urllib.parse
import re
from app.schemas.types import EventType
from app.core.event import eventmanager, Event
from app.log import logger

class XunleiDownloader(_PluginBase):
    """
    迅雷磁力下载插件
    """
    plugin_name = "迅雷磁力下载"
    plugin_desc = "通过迅雷添加磁力任务。"
    plugin_icon = "https://raw.githubusercontent.com/liqman/MoviePilot-Plugins/refs/heads/main/icons/xunlei.png"
    plugin_version = "1.5"
    plugin_author = "liqman"
    author_url = "https://github.com/liqman"
    plugin_config_prefix = "xunleidownloader_"
    plugin_order = 31
    auth_level = 1

    # 插件配置
    _enabled = False
    _BASE_URL = ''
    _PAN_AUTH = ''
    _Authorization = ''
    _file_id = ''
    _filter_size = ''
    _magnet_url = ''
    _device_id = ''

    def init_plugin(self, config: dict = None):
        """
        初始化插件
        """
        if config:
            self._enabled = config.get("enabled", False)
            self._BASE_URL = config.get("BASE_URL", "")
            self._Authorization = config.get("Authorization", "")
            self._file_id = config.get("file_id", "")
            self._filter_size = config.get("filter_size", "")
            self._magnet_url = config.get("magnet_url", "")
            
            # 自动获取 pan_auth
            if self._BASE_URL and self._Authorization:
                logger.info("开始自动获取迅雷 pan_auth ...")
                self._PAN_AUTH = self.get_pan_auth()
            else:
                self._PAN_AUTH = ''

            # 自动下载
            if self._magnet_url:
                logger.info(f"检测到磁力链接，开始自动下载...")
                for magnet_url in str(self._magnet_url).split("\n"):
                    if magnet_url.strip():
                        self.download(magnet_url.strip())
                self._magnet_url = ''  # 清空磁力链接

            # 更新配置
            self.update_config({
                "enabled": self._enabled,
                "BASE_URL": self._BASE_URL,
                "Authorization": self._Authorization,
                "file_id": self._file_id,
                "filter_size": self._filter_size,
                "magnet_url": self._magnet_url
            })
            logger.info("迅雷磁力下载插件初始化完成。")

    def get_state(self) -> bool:
        """
        获取插件状态
        """
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """
        定义插件命令
        """
        return [
            {
                "cmd": "/xl",
                "event": EventType.PluginAction,
                "desc": "迅雷磁力下载",
                "category": "",
                "data": {
                    "action": "xunlei_download"
                }
            }
        ]

    def get_api(self) -> List[Dict[str, Any]]:
        """
        定义插件API
        """
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        定义插件配置表单
        """
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
            # 用户名和密码同一行
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
                                    'model': 'file_id',
                                    'label': '迅雷Docker容器file_id',
                                    'placeholder': 'file_id'
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
                                    'model': 'filter_size',
                                    'label': '过滤指定体积(MB)以下文件',
                                    'placeholder': 'filter_size'
                                }
                            }
                        ]
                    },
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
                                    "text": "可使用 /xl 进行命令交互, 如 /xl 磁力链接"
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
            'Authorization': self._Authorization,
            'file_id': self._file_id,
            'filter_size': self._filter_size,
            'magnet_url': self._magnet_url
        }
        return form_content, form_data

    def get_page(self) -> List[dict]:
        """
        定义插件页面
        """
        pass
    
    def stop_service(self):
        """
        停止插件服务
        """
        pass

    def _get_headers(self) -> Dict[str, str]:
        """
        构造请求头
        """
        if not self._PAN_AUTH:
            logger.warning("pan_auth 未设置，将尝试重新获取。")
            self._PAN_AUTH = self.get_pan_auth()

        headers = {
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
        return headers

    def get_pan_auth(self) -> Optional[str]:
        """
        从迅雷页面获取 pan_auth
        """
        if not self._BASE_URL or not self._Authorization:
            logger.error("迅雷Docker地址或Authorization未配置，无法获取 pan_auth。")
            return None
        
        logger.info("正在获取迅雷 pan_auth ...")
        try:
            index_url = f"{self._BASE_URL}/webman/3rdparty/pan-xunlei-com/index.cgi/"
            headers = {"Authorization": self._Authorization}
            response = requests.get(index_url, headers=headers, timeout=10)
            response.raise_for_status()

            pattern = r'uiauth\(.*?\)\s*{\s*return\s*"([^"]+)"'
            match = re.search(pattern, response.text)
            if match:
                pan_auth = match.group(1)
                logger.info(f"成功获取到 pan_auth: {pan_auth}")
                return pan_auth
            else:
                logger.error("在页面中未找到 pan_auth。")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"获取迅雷 pan_auth 失败（网络请求错误）: {e}")
        except Exception as e:
            logger.error(f"获取迅雷 pan_auth 失败（未知错误）: {e}")
        return None

    def get_device_id(self) -> Optional[str]:
        """
        获取设备ID
        """
        if not self._BASE_URL:
            logger.error("迅雷Docker地址未配置，无法获取设备ID。")
            return None
        
        logger.info("正在获取迅雷设备ID...")
        try:
            headers = self._get_headers()
            if not headers.get('pan-auth'):
                logger.error("获取设备ID失败：pan_auth 为空。")
                return None

            url = f'{self._BASE_URL}/webman/3rdparty/pan-xunlei-com/index.cgi/drive/v1/tasks?type=user%23runner&device_space='
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data.get('error'):
                error_msg = data['error']
                logger.error(f"获取迅雷设备ID失败: {error_msg}")
                return None
            
            tasks = data.get('tasks')
            if tasks and len(tasks) > 0:
                device_id = tasks[0].get('params', {}).get('target')
                if device_id:
                    logger.info(f"成功获取到设备ID: {device_id}")
                    return device_id
            
            logger.error("未能从返回数据中解析出设备ID。")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"获取迅雷设备ID失败（网络请求错误）: {e}")
        except Exception as e:
            logger.error(f"获取迅雷设备ID失败（未知错误）: {e}")
        return None

    def download(self, magnet: str) -> bool:
        """
        通过迅雷下载磁力链接
        """
        logger.info(f"开始处理下载任务: {magnet}")
        if not self._device_id:
            self._device_id = self.get_device_id()

        if not all([self._BASE_URL, self._file_id, self._device_id]):
            logger.error("下载失败：缺少必要的配置信息（迅雷地址、file_id 或 device_id）。")
            return False

        try:
            # 1. 解析磁力链接获取文件列表
            logger.info("步骤 1/3: 解析磁力链接...")
            list_url = f"{self._BASE_URL}/webman/3rdparty/pan-xunlei-com/index.cgi/drive/v1/resource/list"
            data = {"page_size": 1000, "urls": magnet}
            headers = self._get_headers()
            if not headers.get('pan-auth'):
                logger.error("下载失败：pan_auth 为空。")
                return False

            response = requests.post(list_url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            files = response.json()

            if not files.get('list') or not files['list'].get('resources'):
                logger.error("解析磁力链接失败：返回结果为空。")
                return False

            # 2. 提取和筛选文件信息
            logger.info("步骤 2/3: 提取并筛选文件...")
            
            def _get_all_files_recursive(items: List[Dict]) -> List[Dict]:
                """递归获取所有文件"""
                file_list = []
                for item in items:
                    if item.get('is_dir') and 'dir' in item:
                        file_list.extend(_get_all_files_recursive(item.get('dir', {}).get('resources', [])))
                    elif not item.get('is_dir'):
                        file_list.append(item)
                return file_list

            resource_info = files['list']['resources'][0]
            file_name = resource_info.get('name', '未知任务')
            
            # 磁力链接可能包含多个文件/目录，或只是一个文件。递归获取所有文件。
            all_files_in_torrent = _get_all_files_recursive(files['list']['resources'])

            logger.info(f"种子名称: {file_name}")
            logger.info(f"共发现 {len(all_files_in_torrent)} 个文件。")
            logger.info("文件列表:")

            indices = []
            filtered_resources = []
            total_size = 0
            # logger.info(all_files_in_torrent)

            filter_size_bytes = 0
            filter_size_mb_str = "0"
            if self._filter_size and self._filter_size.isdigit():
                filter_size_mb = int(self._filter_size)
                filter_size_bytes = filter_size_mb * 1024 * 1024
                filter_size_mb_str = self._filter_size
                logger.info(f"将过滤小于 {filter_size_mb_str} MB 的文件。")
            else:
                logger.info("未设置或无效的过滤大小，将不过滤文件。")
            
            for index, resource in enumerate(all_files_in_torrent):
                file_size = resource.get('file_size', 0)
                file_size_mb = file_size / 1024 / 1024
                
                # 优先使用返回的 file_index，如果缺失则使用 enumerate 的索引作为备用
                file_index = resource.get('file_index')
                if file_index is None:
                    logger.warning(f"文件 '{resource.get('name', 'N/A')}' 缺少 'file_index'，将使用其在文件列表中的位置 '{index}' 作为索引。")
                    file_index = index

                logger.info(f"  - 文件名: {resource.get('name', 'N/A')}, 大小: {file_size_mb:.2f} MB, Index: {file_index}")
                
                if file_size > filter_size_bytes:
                    indices.append(str(file_index))
                    filtered_resources.append(resource)
                    total_size += file_size
                else:
                    logger.info(f"    - 文件 '{resource.get('name', 'N/A')}' 已被过滤，大小 {file_size_mb:.2f} MB 小于或等于阈值 {filter_size_mb_str} MB。")

            logger.info(f"过滤后 (大于 {filter_size_mb_str} MB) 的文件列表:")
            if not filtered_resources:
                logger.warning(f"没有大于 {filter_size_mb_str} MB 的文件，任务未添加。")
                return False
            for resource in filtered_resources:
                 logger.info(f"  - 文件名: {resource.get('name', 'N/A')}, 大小: {resource.get('file_size', 0) / 1024 / 1024:.2f} MB")

            # 3. 添加下载任务
            logger.info("步骤 3/3: 添加下载任务到迅雷...")
            task_url = f"{self._BASE_URL}/webman/3rdparty/pan-xunlei-com/index.cgi/drive/v1/task"
            task_data = {
                "params": {
                    "parent_folder_id": self._file_id,
                    "url": magnet,
                    "target": self._device_id,
                    "total_file_count": str(len(all_files_in_torrent)),
                    "sub_file_index": ','.join(indices)
                },
                "file_name": file_name,
                "file_size": str(total_size),
                "name": file_name,
                "type": "user#download-url",
                "space": self._device_id,
            }
            
            response = requests.post(task_url, json=task_data, headers=headers, timeout=30)
            response.raise_for_status()
            
            logger.info("成功添加迅雷下载任务！")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"添加迅雷下载失败（网络请求错误）: {e}")
        except Exception as e:
            logger.error(f"添加迅雷下载失败（未知错误）: {e}")
        
        return False

    @eventmanager.register(EventType.PluginAction)
    def remote_sync_one(self, event: Event = None):
        """
        处理插件动作事件，如下载命令
        """
        if not event or not event.event_data:
            return
        
        if event.event_data.get("action") != "xunlei_download":
            return

        logger.info(f"接收到迅雷下载命令: {event.event_data}")
        
        args = event.event_data.get("args") or event.event_data.get("arg_str")
        if not args:
            logger.error("缺少磁力链接参数。")
            self.post_message(
                channel=event.event_data.get("channel"),
                title="迅雷下载失败",
                message="命令缺少磁力链接参数。",
                userid=event.event_data.get("user")
            )
            return

        success = self.download(args)
        
        channel = event.event_data.get("channel")
        userid = event.event_data.get("user")
        
        if success:
            logger.info(f"磁力链接 {args} 已成功添加到迅雷。")
            self.post_message(
                channel=channel,
                title="迅雷任务添加成功！",
                message=f"磁力链接已成功添加到下载队列。",
                userid=userid
            )
        else:
            logger.error(f"磁力链接 {args} 添加到迅雷失败。")
            self.post_message(
                channel=channel,
                title="迅雷任务添加失败！",
                message="请检查插件配置和日志获取详细信息。",
                userid=userid
            )

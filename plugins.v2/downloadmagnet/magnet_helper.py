import re
from app.log import logger

class MagnetHelper:
    """
    磁力链接辅助类
    """
    @staticmethod
    def is_magnet_link(text: str) -> bool:
        """
        判断是否为磁力链接
        :param text: 待检测文本
        :return: True/False
        """
        if not text:
            return False
        # 匹配磁力链接的正则表达式
        pattern = r'^magnet:\?xt=urn:btih:[a-zA-Z0-9]{32,40}(&.*)?$'
        return bool(re.match(pattern, text.strip()))

    @staticmethod
    def extract_hash_from_magnet(magnet_link: str) -> str:
        """
        从磁力链接中提取哈希值
        :param magnet_link: 磁力链接
        :return: 哈希值
        """
        if not magnet_link:
            return ""
        
        match = re.search(r'urn:btih:([a-zA-Z0-9]{32,40})', magnet_link)
        if match:
            return match.group(1).lower()
        return ""

    @staticmethod
    def get_magnet_info(magnet_link: str) -> dict:
        """
        获取磁力链接信息
        :param magnet_link: 磁力链接
        :return: 磁力链接信息字典
        """
        if not magnet_link:
            return {}
        
        result = {
            "hash": "",
            "name": "",
            "trackers": []
        }
        
        # 提取哈希值
        result["hash"] = MagnetHelper.extract_hash_from_magnet(magnet_link)
        
        # 提取名称
        name_match = re.search(r'&dn=([^&]+)', magnet_link)
        if name_match:
            result["name"] = name_match.group(1)
        
        # 提取Tracker
        trackers = re.findall(r'&tr=([^&]+)', magnet_link)
        if trackers:
            result["trackers"] = trackers
        
        return result 

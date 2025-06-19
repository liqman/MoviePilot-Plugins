import requests
import json
from typing import List, Union

# 从 app.log 导入 logger
from app.log import logger

class Ollama:
    _api_url: str = "http://localhost:11434"
    _model: str = "llama3"

    def __init__(self, api_url: str = None, model: str = None):
        self._api_url = api_url.rstrip('/') if api_url else "http://localhost:11434"
        self._model = model if model else "llama3"
        logger.info(f"Ollama翻译器初始化：API URL={self._api_url}, 模型={self._model}")

    def __get_model(self, messages: List[dict], user: str = "MoviePilot", **kwargs):
        """
        与 Ollama 的 /api/generate 接口进行交互。
        Ollama 的 generate 接口通常接受一个 prompt 字符串，而不是 messages 列表。
        这里将 messages 转换为一个单一的 prompt 字符串。
        """
        url = f"{self._api_url}/api/generate"

        # 构建 prompt：将 messages 列表转换为 Ollama generate 接口所需的单一字符串
        # 简单地将所有角色内容拼接起来，以保留对话结构
        full_prompt = []
        for msg in messages:
            if msg["role"] == "system":
                full_prompt.append(f"System: {msg['content']}")
            elif msg["role"] == "user":
                full_prompt.append(f"User: {msg['content']}")
            elif msg["role"] == "assistant":
                full_prompt.append(f"Assistant: {msg['content']}")
        
        # 实际传递给 Ollama 的 prompt，只取最后一个用户消息
        # 考虑到 translate_to_zh 的实现，prompt 会被构建为一个包含 system 和 user 角色的字符串
        # 因此这里直接使用 messages 列表的最后一个元素的 content 作为核心 prompt，并确保包含系统指令
        final_prompt_content = messages[-1]["content"] # 最后一个消息是用户请求翻译的文本
        
        # 将 system 消息作为前缀添加到 final_prompt_content，模拟 system 角色
        system_content = ""
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"] + "\n\n"
                break # 假设只有一个 system 消息

        # Ollama 的 /api/generate 接口通常期望一个连续的对话文本，而不是结构化的消息列表。
        # 因此，我们需要将 system_prompt 和 user_prompt 合并为一个字符串。
        # 在 `translate_to_zh` 中已经构建了 `system_prompt` 和 `user_prompt`，
        # 并作为 `messages` 的 `content` 传入，这里需要将它们提取并组合成一个整体的 prompt。
        combined_prompt = f"{system_content}{final_prompt_content}"


        payload = {
            "model": self._model,
            "prompt": combined_prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7), # 默认值，可以从 kwargs 获取
                "top_p": kwargs.get("top_p", 0.9) # 默认值，可以从 kwargs 获取
            }
        }
        headers = {"Content-Type": "application/json"}

        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        response.raise_for_status()  # 检查HTTP错误

        return response.json()

    def translate_to_zh(self, text: str, context: str = None) -> (bool, str):
        """
        翻译为中文
        :param text: 输入文本
        :param context: 翻译上下文
        :return: (是否成功, 翻译结果或错误信息)
        """
        system_prompt = """您是一位专业字幕翻译专家，请严格遵循以下规则：
1. 将原文精准翻译为简体中文，保持原文本意
2. 使用自然的口语化表达，符合中文观影习惯
3. 结合上下文语境，人物称谓、专业术语、情感语气在上下文保持连贯
4. 按行翻译待译内容。翻译结果不要包括上下文。
5. 输出内容必须仅包括译文。不要输出任何开场白，解释说明或总结"""
        
        user_prompt = f"翻译上下文：\n{context}\n\n需要翻译的内容：\n{text}" if context else f"请翻译：\n{text}"
        
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
        
        result = ""
        try:
            # 调用内部的 __get_model 方法，适配 Ollama API
            completion_data = self.__get_model(
                messages=messages,
                temperature=0.2, # 保持与 OpenAi 示例相同的参数
                top_p=0.9      # 保持与 OpenAi 示例相同的参数
            )
            
            # 检查 Ollama 返回的数据结构
            if "response" in completion_data:
                result = completion_data["response"].strip()
                return True, result
            else:
                logger.error(f"Ollama API返回无效响应: {completion_data}")
                return False, f"Ollama API返回无效响应: {completion_data}"

        except requests.exceptions.RequestException as e:
            logger.error(f"调用Ollama API时发生网络或请求错误: {e}")
            return False, f"网络或请求错误: {e}"
        except json.JSONDecodeError as e:
            logger.error(f"解析Ollama API响应失败: {e}")
            return False, f"API响应格式错误: {e}"
        except Exception as e:
            logger.error(f"Ollama翻译过程中发生未知错误: {e}，翻译结果：{result}")
            return False, f"未知错误: {e}，部分结果：{result}"

"""
测试请用命令
```bash
python3 -m "src.OCRAgent.openai_ocr"
```
或者
```bash
python -m "src.OCRAgent.openai_ocr"
```
这取决于你的python解释器名
"""

import os
import requests
import base64
from src.utils.errors import file_not_exist_error
from src.utils.get_env import get_env


def ocr(path: str) -> str:
    """遵循OpenAI调用方式的OCR模型调用

    Args:
        path (str): 需要上传的图片的路径
    Raises:
        file_not_exist_error:如果检查图片路径不存在,则返回报错

    Returns:
        str: 返回值为str类
    """
    if not os.path.exists(path):
        raise file_not_exist_error(path)  # 若路径不存在 返回错误信息

    # 将图片转化为base64格式文件准备上传至大模型
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    image_data_url = f"data:image/png;base64,{b64}"
    url = get_env("Google_OCR_Node")  # API请求端点
    model = get_env("Google_OCR_Model_Name")  # 调用的API模型名称
    api_key = get_env("Google_OCR_Secret_Key")  # API的密钥

    # Post {BaseURL}/chat/completions 或  /responses

    # 请求体的头:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a engine designed to extract the text from the image. "
                    "Extract the text from user's picture faithfully and return ONLY the words in user's picture. "
                    "If there are the words you didn't know, replace them with a question mark. "
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all text from this image."},
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ],
            },
        ],
        "temperature": 0,
        "max_tokens": 2000,
    }

    # 发送request请求并且获得结果
    r = requests.post(url, json=body, headers=headers)

    print("status:", r.status_code)  # 响应请求结果
    print("content-type:", r.headers.get("Content-Type"))  # 返回文本的数据类型(json)
    print("text_head:", r.text)  # 返回的具体数据内容

    data = r.json()
    return data["choices"][0]["message"]["content"].strip()


if __name__ == "__main__":
    print(ocr("images/test.png"))

import os
from dotenv import load_dotenv
import requests

load_dotenv()


# 翻译文本为中文
def translate(query: str, to_lang="zh"):
    """将目标语言全部翻译为中文

    Args:
        query (str): 想要翻译的文本
        to_lang (str, optional): 想要翻译成什么样的语言(默认zh,中文)

    Returns:
        r.json: 返回Json文本格式的text_head.
    """
    url = os.getenv("Google_Translate_Node")
    api_key = os.getenv("Google_Translate_Secret_Key")
    model = os.getenv("Google_Translate_Model_Name")

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
                    "You are a translation engine. "
                    "Translate the user's text faithfully and return ONLY the translated text."
                ),
            },
            {
                "role": "user",
                "content": f"Translate the text to {to_lang}:\n{query}",
            },
        ],
        "temperature": 0,
    }

    # 发送request请求并获取结果
    r = requests.post(url, json=body, headers=headers)

    print("status:", r.status_code)  # 响应请求结果
    print("content-type:", r.headers.get("Content-Type"))  # 返回文本的数据类型(json)
    print("text_head:", r.text)  # 返回的具体数据内容

    data = r.json()
    return data["choices"][0]["message"]["content"].strip()


if __name__ == "__main__":
    print(translate("Hello world"))

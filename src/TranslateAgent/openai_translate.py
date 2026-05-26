import requests
from typing import Any

from src.utils.get_env import get_env
from src.utils.openai_compatible import chat_message_content, post_chat_completion


_SESSION = requests.Session()


# 翻译文本为中文
def translate(query: str, to_lang="zh"):
    """将目标语言全部翻译为中文

    Args:
        query (str): 想要翻译的文本
        to_lang (str, optional): 想要翻译成什么样的语言(默认zh,中文)

    Returns:
        r.json: 返回Json文本格式的text_head.
    """

    url = get_env("OpenAI_Translate_Node")
    api_key = get_env("OpenAI_Translate_Secret_Key")
    model = get_env("OpenAI_Translate_Model_Name")

    body = _translation_body(model, query, to_lang)

    data = post_chat_completion(_SESSION, url, api_key, body)
    return chat_message_content(data)


def _translation_body(model: str, query: str, to_lang: str) -> dict[str, Any]:
    if _is_qwen_mt_model(model):
        target_lang = _target_lang_name(to_lang)
        return {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": _qwen_mt_prompt(query, target_lang),
                },
            ],
            "extra_body": {
                "translation_options": {
                    "source_lang": "auto",
                    "target_lang": target_lang,
                },
            },
        }

    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a translation engine. "
                    "Translate the user's text faithfully and return ONLY the translated text."
                    "Filter the mistaken words and grammar errors in the original text and correct them in the translation. "
                ),
            },
            {
                "role": "user",
                "content": f"Translate the text to {to_lang}:\n{query}",
            },
        ],
        "temperature": 0,
    }


def _is_qwen_mt_model(model: str) -> bool:
    return model.strip().lower().startswith("qwen-mt")


def _qwen_mt_prompt(query: str, target_lang: str) -> str:
    return (
        f"Translate the text between <text> and </text> into {target_lang}.\n"
        "Return ONLY the translation. Do not explain, summarize, add notes, "
        "or include the tags. Preserve line breaks and speaker names if present.\n"
        "<text>\n"
        f"{query}\n"
        "</text>"
    )


def _target_lang_name(to_lang: str) -> str:
    normalized = to_lang.strip().lower()
    language_names = {
        "zh": "Chinese",
        "zh-cn": "Chinese",
        "chinese": "Chinese",
        "cn": "Chinese",
        "en": "English",
        "english": "English",
        "ja": "Japanese",
        "jp": "Japanese",
        "japanese": "Japanese",
        "ko": "Korean",
        "kr": "Korean",
        "korean": "Korean",
    }
    return language_names.get(normalized, to_lang)


if __name__ == "__main__":
    print(translate("Hello world"))

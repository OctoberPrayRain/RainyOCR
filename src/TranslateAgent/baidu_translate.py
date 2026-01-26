from hashlib import md5
import json
import random
from dotenv import load_dotenv
import requests
from src.OCRAgent import baidu_ocr
from src.utils.get_env import get_env
from src.utils.errors import network_error, baidu_api_error, TaskType
from src.utils.baidu_ocr_result_processor import process

load_dotenv()


def make_md5(s: str, encoding="utf-8"):
    """使用md5函数计算字符串的MD5哈希值

    Args:
        s (str): 需要被计算的字符串
        encoding (str, optional): 编码格式. Defaults to 'utf-8'.

    Returns:
        str: 计算得到的哈希值,以16进至大小写字母的形式返回.
    """
    return md5(s.encode(encoding)).hexdigest()


def translate(query: str, from_lang: str = "en", to_lang="zh"):
    """将输入字符串翻译成为目标语言

    Args:
        query (str): 需要翻译的字符串
        from_lang (str, optional): 输入的字符串的语言, 默认是英语. Defaults to "en".
        to_lang (str, optional): 目标语言, 默认是中文. Defaults to "zh".

    Raises:
        TaggedError: HTTP请求未能成功, 勤检查网络
        TaggedError: 百度翻译API使用过程中的错误, 具体需要查询百度翻译相关文档: https://fanyi-api.baidu.com/doc/23

    Returns:
        result(json): 返回一个json格式的结果
    """
    appid = get_env("APPID")
    appkey = get_env("APPKEY")

    endpoint = "http://api.fanyi.baidu.com"
    path = "/api/trans/vip/translate"
    url = endpoint + path
    # 生成盐
    salt = random.randint(32768, 65536)
    sign = make_md5(appid + query + str(salt) + appkey)

    # 构造request
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "appid": appid,
        "q": query,
        "from": from_lang,
        "to": to_lang,
        "salt": salt,
        "sign": sign,
    }

    # 发送request请求并获取结果
    response = requests.post(url, params=payload, headers=headers)

    if response.status_code != 200:
        raise network_error(response.status_code)

    result = response.json()

    if error_code := result.get("error_code"):
        raise baidu_api_error(
            result.get("error_msg", "Unknown error"), error_code, TaskType.TRANSLATE
        )

    return result


if __name__ == "__main__":
    result = translate(process(baidu_ocr.ocr("images/test.png")))
    print(json.dumps(result, ensure_ascii=False))

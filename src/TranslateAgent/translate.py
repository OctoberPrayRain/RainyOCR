from hashlib import md5
import json
import os
import random
from dotenv import load_dotenv
import requests
load_dotenv()
def make_md5(s: str, encoding='utf-8'):
    """使用md5

    Args:
        s (str): _description_
        encoding (str, optional): _description_. Defaults to 'utf-8'.

    Returns:
        _type_: _description_
    """
    return md5(s.encode(encoding)).hexdigest()


def translate(query: str):
    appid = os.getenv("APPID")
    appkey = os.getenv("APPKEY")
    if not appid:
        raise Exception("APPID not exist!")
    if not appkey:
        raise Exception("APPKEY not exist!")
    
    from_lang = "en"
    to_lang = "zh"

    endpoint = 'http://api.fanyi.baidu.com'
    path = '/api/trans/vip/translate'
    url = endpoint + path
    # 生成盐
    salt = random.randint(32768, 65536)
    sign = make_md5(appid + query + str(salt) + appkey)

    # 构造request
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    payload = {'appid': appid, 'q': query, 'from': from_lang, 'to': to_lang, 'salt': salt, 'sign': sign}


    # 发送request请求并获取结果
    r = requests.post(url, params=payload, headers=headers)
    
    if r.status_code != 200:
        raise Exception(f"Baidu Translate HTTP Error: {r.status_code}")
    
    result = r.json()
    
    if error_code := result.get("error_code"):
        raise Exception(f"API Error: {error_code}. {result.get("error_msg", "Unkown error")}")

    return result


if __name__ == "__main__":
    result = translate("How are you?")
    print(json.dumps(result, ensure_ascii=False))
"""
测试请用命令
```bash
python3 -m "src.BaiduOCR.ocr"
```
或者
```bash
python -m "src.BaiduOCR.ocr"
```
这取决于你的python解释器名
"""


import requests
import base64
import os
from dotenv import load_dotenv
from src.utils.get_baidu_access_token import get

load_dotenv()

"""
通用文字识别
"""

class BaiduOCRError(Exception):
    """百度OCR异常

    Attributes:
        status_code: HTTP 状态码
        error_code: API 错误码
    """
    def __init__(self, message: str, status_code: int | None = None, error_code: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code

def ocr(path: str) -> dict:
    """调用百度智能云的通用OCR进行图片识别

    Args:
        path (str): 图片路径

    Returns:
        dict: OCR识别结果

    Raises:
        BaiduOCRError: Token缺失、文件不存在、API调用失败等情况
    """
    if not os.path.exists(path):
        raise BaiduOCRError(f"Image file not found: {path}")

    request_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"
    access_token = os.getenv("ACCESS_TOKEN")

    # 假如ACCESS_TOKEN不存在,调用get函数,重新获取ACCESS_TOKEN,然后重新加载项目环境变量
    if not access_token:
        # raise BaiduOCRError("ACCESS_TOKEN not found in environment variables")
        get()
        load_dotenv()
        access_token = os.getenv("ACCESS_TOKEN")
        

    request_url = f"{request_url}?access_token={access_token}"
    headers = {"content-type": "application/x-www-form-urlencoded"}

    with open(path, 'rb') as f:
        img = base64.b64encode(f.read())
        params = {"image": img}
        response = requests.post(request_url, data=params, headers=headers)

        # HTTP 状态码检查
        if response.status_code != 200:
            raise BaiduOCRError(
                f"HTTP error: {response.status_code}",
                status_code=response.status_code
            )

        result = response.json()

        # API 错误响应检查
        if error_code := result.get("error_code"):
            raise BaiduOCRError(
                f"API error: {result.get('error_msg', 'Unknown error')}",
                error_code=error_code
            )

        return result
            
if __name__ == "__main__":
    print(ocr("images/test.png"))
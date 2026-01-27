import os
from dotenv import load_dotenv
from src.utils.get_baidu_access_token import get


def get_env(name: str, can_retry: bool = True) -> str:
    """获取局部环境变量(存放于.env)

    Args:
        name (str): 变量名
        can_retry (bool, optional): 重试标志. Defaults to True.

    Raises:
        ValueError: 变量名不存在, 变量名必须被设置

    Returns:
        str: 变量的内容
    """
    load_dotenv()
    val = os.getenv(name)

    if not val:
        # 只有在允许重试且是 ACCESS_TOKEN 的情况下才尝试获取
        if name == "ACCESS_TOKEN" and can_retry:
            get()
            # 第二次调用时禁用重试，确保不会无限循环
            return get_env(name, can_retry=False)

        raise ValueError(f"{name} environment variable must be set")
    return val

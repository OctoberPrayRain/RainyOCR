import os
from dotenv import load_dotenv

load_dotenv()


def get_env(name: str) -> str:
    """获取局部环境变量(存放于.env)

    Args:
        name (str): 变量名

    Raises:
        ValueError: 变量名不存在, 变量名必须被设置

    Returns:
        str: 变量的内容
    """
    val = os.getenv(name)
    if not val:
        raise ValueError(f"{name} environment variable must be set")
    return val

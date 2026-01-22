import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()


def get():
    api_key = os.getenv("API_KEY")
    secret_key = os.getenv("SECRET_KEY")
    
    if not api_key:
        raise Exception("API_KEY not exist!")
    if not secret_key:
        raise Exception("SECRET_KEY not exist!")

    url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"

    payload = ""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    response = requests.request("POST", url, headers=headers, data=payload)

    response_json = json.loads(response.text)

    # print(json.dumps(response_json, indent=4, ensure_ascii=False))
    
    content = f'\nACCESS_TOKEN = "{response_json["access_token"]}"'
    
    with open(".env", "a", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    get()

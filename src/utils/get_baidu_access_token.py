import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()


def main():
    api_key = os.getenv("API_KEY")
    secret_key = os.getenv("SECRET_KEY")

    url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"

    payload = ""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    response = requests.request("POST", url, headers=headers, data=payload)

    response_json = json.loads(response.text)

    # print(json.dumps(response_json, indent=4, ensure_ascii=False))
    print(response_json["access_token"])

if __name__ == "__main__":
    main()

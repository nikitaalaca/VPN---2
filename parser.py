import requests
from bs4 import BeautifulSoup
import json

def fetch_links():
    urls = [
        "https://v2rayssr.com",
        "https://freevpn.us/v2ray",
        "https://getvmess.net",
    ]
    links = []

    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            for code in soup.find_all("code"):
                text = code.get_text(strip=True)
                if text.startswith("vmess://") or text.startswith("vless://"):
                    links.append(text)
        except Exception as e:
            print(f"Ошибка при парсинге {url}: {e}")
    return links

def save_links():
    links = fetch_links()
    with open("storage.json", "w") as f:
        json.dump(links, f, indent=2)

def get_random_key():
    try:
        with open("storage.json", "r") as f:
            links = json.load(f)
            return links[0] if links else None
    except:
        return None
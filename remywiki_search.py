import requests
import webbrowser
from bs4 import BeautifulSoup
from urllib.parse import quote

BASE_URL = "https://remywiki.com"

def _link(text, url):
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"

def remywiki_search_loop():
    query = input("RemyWiki search (Enter to skip): ").strip()
    if not query:
        return

    url = f"{BASE_URL}/index.php?search={quote(query)}&profile=advanced&fulltext=1"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "html.parser")

    items = soup.select("ul.mw-search-results > li.mw-search-result")
    results = []

    for item in items[:3]:
        a = item.select_one(".mw-search-result-heading a")
        title = a.get_text(" ", strip=True)
        href = BASE_URL + a["href"]
        results.append((title, href))

    if not results:
        return

    for i, (title, href) in enumerate(results, 1):
        print(f"{i}. {_link(title, href)}")

    choice = input("Open (1-3 / Enter = continue): ").strip()
    if choice in {"1", "2", "3"}:
        webbrowser.open(results[int(choice) - 1][1])

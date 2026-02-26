from urllib.parse import quote


BASE_URL = "https://remywiki.com"


def build_remywiki_url(title: str) -> str:
    clean = (title or "").strip()
    if not clean:
        return BASE_URL
    encoded = quote(clean.replace(" ", "_"), safe=":_-()[]")
    return f"{BASE_URL}/{encoded}"

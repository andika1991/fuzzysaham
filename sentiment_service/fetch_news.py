import requests

URL = "https://berita-indo-api-next.vercel.app/API/cnbc-news/market"

def fetch_news():
    r = requests.get(URL, timeout=15)
    if r.status_code != 200:
        return []

    data = r.json().get("data", [])
    news = []

    for a in data:
        news.append({
            "judul": a.get("title", ""),
            "tanggal": a.get("isoDate", ""),
            "konten": a.get("contentSnippet", ""),
            "link": a.get("link", "")
        })

    return news

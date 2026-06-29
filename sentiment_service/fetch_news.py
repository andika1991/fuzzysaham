import requests

URL = "https://thorn-iodize-crushing.ngrok-free.dev/cnbc/market"

def fetch_news():
    r = requests.get(URL, timeout=15)

    if r.status_code != 200:
        return []

    response = r.json()

    # Ambil array posts dari dalam data
    data = response.get("data", {}).get("posts", [])

    news = []

    for a in data:
        news.append({
            "judul": a.get("title", ""),
            "tanggal": a.get("pubDate", ""),
            "konten": a.get("description", ""),
            "link": a.get("link", "")
        })

    return news